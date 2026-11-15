# -*- coding: utf-8 -*-
"""M4 自动排课引擎（详设第 6 章）：约束建模 → 贪心+回溯构造 → 模拟退火/遗传寻优 → 冲突检测。

三个子模块对应三个函数族：build_model / greedy_construct + optimize / full_scan。
对外接口：solve(term_id)（期初全量）、relocal(term_id, affected_task_ids)（局部重排）。

连排块建模：课程学时 → 连排块（2 学时=1 块 2 节；3 学时=1 块 3 节；4 学时=2 块 2 节），
排课与冲突检测以块为原子变量，块内每节逐一登记占用（详设 6.6 建模）。
"""
import json
import math
import random
import time

import config
from config import cfg
from services.dao import schedule_write_tx
from models import (db, TeachingTask, ScheduleRecord, Classroom, ClassInfo,
                    ConstraintConfig, TeacherPreference)

CourseHoursCache = {}     # 课程学时缓存（solve 前由 refresh_caches 填充）
ClassSizeCache = {}       # 班级人数缓存

DAY_SLOTS = list(range(1, 6))       # 周一~周五

# 每日 12 节分三时段（无第 9 节）：上午 1-4、下午 5-8、晚上 10-12
SEGMENTS = [("上午", [1, 2, 3, 4]), ("下午", [5, 6, 7, 8]), ("晚上", [10, 11, 12])]
PERIOD_SLOTS = [p for _n, ps in SEGMENTS for p in ps]   # [1..8, 10, 11, 12] 共 11 节


def block_starts(length):
    """连排块合法起始节（一次上课只能是 2 或 3 节，组合固定）：
    2 节块：上午 1-2 / 3-4，下午 5-6 / 7-8，晚上 10-11 → 起始 [1,3,5,7,10]；
    3 节块：上午 1-3，下午 5-7，晚上 10-12 → 起始 [1,5,10]。"""
    starts = []
    for _name, ps in SEGMENTS:
        if length == 2:
            starts += [ps[0], ps[2]] if len(ps) >= 4 else [ps[0]]
        elif length == 3:
            starts.append(ps[0])           # 各时段前三节
    return starts


def hours_to_blocks(hours):
    """学时 → 连排块长度列表，块长只允许 2 或 3 节（排课口径：1 节与 4 节及以上单块均不出现）。

    2→[2]，3→[3]，4→[2,2]，5→[3,2]，6→[2,2,2]，其余贪心切分；1 节零头按 2 节连排。
    """
    out = []
    rem = int(hours or 0)
    while rem > 0:
        if rem in (2, 3):
            out.append(rem)
            rem = 0
        elif rem == 4:
            out.extend([2, 2])
            rem = 0
        elif rem == 1:
            out.append(2)          # 不足 2 节的零头按 2 节连排
            rem = 0
        else:
            take = 3 if rem % 2 == 1 else 2
            out.append(take)
            rem -= take
    return out or [2]


class Model:
    """约束建模：任务按学时展开为连排块，变量 x(b)=(day, start_period, room)。"""

    def __init__(self, tasks, rooms, hard_rules, soft_rules, fixed_busy=None):
        self.tasks = tasks                       # [(task_id, hours, class_size, teacher_id, class_id)]
        self.blocks = []                         # [{key:(task_id,part), task, len, teacher, klass, size}]
        for (tid, hours, size, tch, kls) in tasks:
            for part, L in enumerate(hours_to_blocks(hours)):
                self.blocks.append({"key": (tid, part), "task": tid, "len": L,
                                    "teacher": tch, "klass": kls, "size": size})
        self.block_by_key = {b["key"]: b for b in self.blocks}
        self.rooms = rooms                       # [(room_id, capacity, rtype)]
        self.hard = hard_rules
        self.soft = soft_rules                   # [(weight, type, params)] 教师/管理员软约束
        self.class_size = {t[0]: t[2] for t in tasks}
        self.task_teacher = {t[0]: t[3] for t in tasks}
        self.task_class = {t[0]: t[4] for t in tasks}
        # 固定上下文占用（局部重排时未涉任务的槽位，键与下方冲突检测一致）
        self.fixed_busy = fixed_busy or {"room": set(), "teacher": set(), "class": set()}

    def feasible_rooms(self, task_id):
        """容量硬约束：教室容量 ≥ 班级人数。"""
        size = self.class_size[task_id]
        return [r for r in self.rooms if r[1] >= size]


class Solution:
    """解：block_key -> (day, start_period, room_id)，块内 [start, start+len) 连续占用。"""

    def __init__(self, assignment):
        self.assign = dict(assignment)

    def copy(self):
        return Solution(self.assign)


def hard_conflicts(sol: Solution, model: Model, affected=None):
    """四类硬约束全量扫描（详设 6.6(3)），块内逐槽登记，返回冲突列表（含定位）。

    另含"同任务同天"约束：同一任务拆出的多块必须分布在不同天（4 学时=不同天各 2 节），
    保证一次连排只能是 2 或 3 节。
    """
    conflicts = []
    seen_room, seen_teacher, seen_class = {}, {}, {}
    task_days = {}                              # task_id -> {day: block_key}
    items = [(bkey, sol.assign[bkey]) for bkey in sol.assign
             if affected is None or bkey[0] in affected]
    for bkey, (d, p0, rid) in items:
        if bkey[0] in task_days and d in task_days[bkey[0]]:
            conflicts.append(("same_task_day_conflict", bkey, task_days[bkey[0]][d], (d,)))
        task_days.setdefault(bkey[0], {})[d] = bkey
        b = model.block_by_key[bkey]
        tch, kls = b["teacher"], b["klass"]
        for p in range(p0, p0 + b["len"]):
            tkey = (d, p)
            if tkey in seen_room and seen_room[tkey][0] == rid:
                conflicts.append(("room_conflict", bkey, seen_room[tkey][1], tkey, rid))
            else:
                seen_room[tkey] = (rid, bkey)
            if (d, p, rid) in model.fixed_busy["room"]:
                conflicts.append(("room_conflict_fixed", bkey, "fixed", tkey, rid))
            if tch is not None:
                tck = (d, p, tch)
                if tck in seen_teacher:
                    conflicts.append(("teacher_conflict", bkey, seen_teacher[tck], tkey, tch))
                else:
                    seen_teacher[tck] = bkey
                if (d, p, tch) in model.fixed_busy["teacher"]:
                    conflicts.append(("teacher_conflict_fixed", bkey, "fixed", tkey, tch))
            if kls is not None:
                kck = (d, p, kls)
                if kck in seen_class:
                    conflicts.append(("class_conflict", bkey, seen_class[kck], tkey, kls))
                else:
                    seen_class[kck] = bkey
                if (d, p, kls) in model.fixed_busy["class"]:
                    conflicts.append(("class_conflict_fixed", bkey, "fixed", tkey, kls))
    return conflicts


def soft_score(sol: Solution, model: Model, prefs_by_teacher, soft_rules):
    """软约束加权得分 F=Σ w_i·s_i（详设 6.6(1)），按块起始节计分。"""
    score = 0.0
    for bkey, (d, p0, rid) in sol.assign.items():
        b = model.block_by_key[bkey]
        tch = b["teacher"]
        for pref in prefs_by_teacher.get(tch, []):
            if pref["type"] == "prefer" and pref.get("day") == d:
                score += pref.get("weight", 2)
            elif pref["type"] == "avoid" and pref.get("day") == d:
                score -= pref.get("weight", 2)
            elif pref["type"] == "consecutive" and p0 in (1, 3, 5, 10):
                score += pref.get("weight", 1)
    for rule in soft_rules:
        w = rule.get("weight", 2)
        if rule.get("key") == "max_daily":
            pass  # 每日节次上限在邻域生成时约束，计分不重复
    return score


def fitness(sol, model, prefs_by_teacher, soft_rules):
    """适应度 = 硬约束罚项（大罚系数）+ 软约束得分（详设 6.6）。"""
    conflicts = hard_conflicts(sol, model)
    return -cfg.HARD_PENALTY * len(conflicts) + soft_score(sol, model, prefs_by_teacher, soft_rules)


def greedy_construct(model: Model, prefs_by_teacher):
    """阶段一：贪心+回溯构造初始可行解（详设 6.6(2)）。

    块按长度降序排序（长块更难放置）；逐块选软约束得分最高的可行赋值；
    无可行赋值时回溯前一块改选次优；回溯预算耗尽报告不可行。
    """
    order = sorted(model.blocks, key=lambda b: -b["len"])
    assign = {}
    occupied = set(model.fixed_busy["room"])       # {(day,period,room_id)}
    teacher_busy = set(model.fixed_busy["teacher"])
    class_busy = set(model.fixed_busy["class"])
    task_days = {}                                 # task_id -> set(已用天)：同任务块不排同天
    budget = [200]                                 # 回溯预算（次）

    def place(idx):
        if idx >= len(order):
            return True
        b = order[idx]
        tid, L, tch, kls = b["task"], b["len"], b["teacher"], b["klass"]
        used_days = task_days.get(tid, set())
        candidates = []
        for d in DAY_SLOTS:
            if d in used_days:                     # 同任务块必须不同天
                continue
            for p0 in block_starts(L):             # 段内合法连排组合
                ps = range(p0, p0 + L)
                if any((d, p, tch) in teacher_busy for p in ps):
                    continue
                if any((d, p, kls) in class_busy for p in ps):
                    continue
                for rid, cap, _rt in model.feasible_rooms(tid):
                    if any((d, p, rid) in occupied for p in ps):
                        continue
                    gain = 0
                    for pref in prefs_by_teacher.get(tch, []):
                        if pref["type"] == "prefer" and pref.get("day") == d:
                            gain += pref.get("weight", 2)
                        elif pref["type"] == "avoid" and pref.get("day") == d:
                            gain -= pref.get("weight", 2)
                    candidates.append((gain, d, p0, rid))
        candidates.sort(key=lambda x: -x[0])
        for cand_i, (_g, d, p0, rid) in enumerate(candidates):
            if cand_i > 0:                     # 回溯换位才消耗预算，首选放置不消耗
                budget[0] -= 1
                if budget[0] <= 0:
                    return False
            ps = range(p0, p0 + L)
            assign[b["key"]] = (d, p0, rid)
            task_days.setdefault(tid, set()).add(d)
            for p in ps:
                occupied.add((d, p, rid))
                teacher_busy.add((d, p, tch))
                class_busy.add((d, p, kls))
            if place(idx + 1):
                return True
            del assign[b["key"]]
            task_days[tid].discard(d)
            for p in ps:
                occupied.discard((d, p, rid))
                teacher_busy.discard((d, p, tch))
                class_busy.discard((d, p, kls))
        return False

    if place(0):
        return Solution(assign), None
    return None, "回溯预算耗尽仍无可行解：请检查约束是否过紧或数据是否存在冲突"


def neighbor(sol: Solution, model: Model, rng):
    """邻域：随机选一块重排至随机合法位（详设 6.6 阶段二邻域）。"""
    bkey = rng.choice(list(sol.assign.keys()))
    b = model.block_by_key[bkey]
    d = rng.choice(DAY_SLOTS)
    p0 = rng.choice(block_starts(b["len"]))
    rid, _cap, _rt = rng.choice(model.feasible_rooms(b["task"]))
    new = sol.copy()
    new.assign[bkey] = (d, p0, rid)
    return new


def optimize_sa(sol, model, prefs_by_teacher, soft_rules, rng,
                iterations=None, no_improve=None, deadline=None):
    """模拟退火寻优（详设 6.6(2)：Metropolis 准则、几何降温）。"""
    iterations = iterations or cfg.ENGINE_ITERATIONS
    no_improve = no_improve or cfg.ENGINE_NO_IMPROVE_ROUNDS
    cur = sol.copy()
    cur_fit = fitness(cur, model, prefs_by_teacher, soft_rules)
    best, best_fit = cur.copy(), cur_fit
    temp = 100.0
    stall = 0
    i = 0
    for i in range(iterations):
        if deadline and time.time() > deadline:
            break
        cand = neighbor(cur, model, rng)
        cand_fit = fitness(cand, model, prefs_by_teacher, soft_rules)
        if cand_fit >= cur_fit or rng.random() < math.exp((cand_fit - cur_fit) / max(temp, 1e-6)):
            cur, cur_fit = cand, cand_fit
            if cur_fit > best_fit:
                best, best_fit = cur.copy(), cur_fit
                stall = 0
        temp *= 0.995
        stall += 1
        if stall >= no_improve:
            break
    return best, best_fit, {"iterations": i + 1, "reason": "无改进终止" if stall >= no_improve else "迭代上限"}


def optimize_ga(sol, model, prefs_by_teacher, soft_rules, rng,
                iterations=None, no_improve=None, deadline=None, pop_size=12):
    """遗传算法寻优（详设 6.6(2)：锦标赛选择、单点交叉、单块重排变异、精英保留）。"""
    iterations = iterations or cfg.ENGINE_ITERATIONS
    no_improve = no_improve or cfg.ENGINE_NO_IMPROVE_ROUNDS
    pop = [(sol.copy(), fitness(sol, model, prefs_by_teacher, soft_rules))]
    for _ in range(pop_size - 1):
        ind = neighbor(sol, model, rng)
        pop.append((ind, fitness(ind, model, prefs_by_teacher, soft_rules)))
    best, best_fit = max(pop, key=lambda x: x[1])
    best_fit0, stall = best_fit, 0
    used = 0
    for i in range(iterations):
        if deadline and time.time() > deadline:
            break
        used += 1
        pop.sort(key=lambda x: -x[1])
        elites = pop[:2]                                   # 精英保留
        parents = [pop[rng.randrange(min(4, len(pop)))][0] for _ in range(pop_size)]
        children = list(elites)
        keys = list(sol.assign.keys())
        for a, b in zip(parents[::2], parents[1::2]):
            cut = rng.randrange(len(keys))
            child = sol.copy()
            for j, bkey in enumerate(keys):
                child.assign[bkey] = a.assign[bkey] if j < cut else b.assign[bkey]
            children.append((child, fitness(child, model, prefs_by_teacher, soft_rules)))
            child2 = neighbor(children[-1][0], model, rng)  # 单块重排变异
            children.append((child2, fitness(child2, model, prefs_by_teacher, soft_rules)))
        pop = sorted(children, key=lambda x: -x[1])[:pop_size]
        cur_best, cur_fit = max(pop, key=lambda x: x[1])
        if cur_fit > best_fit:
            best, best_fit = cur_best.copy(), cur_fit
        stall = 0 if cur_fit > best_fit0 else stall + 1
        best_fit0 = max(best_fit0, cur_fit)
        if stall >= no_improve:
            break
    return best, best_fit, {"iterations": used, "reason": "无改进终止" if stall >= no_improve else "迭代上限"}


def _prefs_by_teacher(term_id):
    """已启用教师偏好 → {teacher_id: [{type, day, weight}]}（仅"已启用"状态，详设 5.11）。"""
    prefs = TeacherPreference.query.filter_by(term_id=term_id, status="已启用").all()
    out = {}
    for p in prefs:
        day = None
        for token in ("周一", "周二", "周三", "周四", "周五"):
            if token in (p.content or ""):
                day = "周一周二周三周四周五".index(token) // 2 + 1
                break
        out.setdefault(p.teacher_id, []).append(
            {"type": p.ptype, "day": day, "weight": max(1, 7 - p.priority)})
    return out


def _soft_rules(term_id):
    rows = ConstraintConfig.query.filter_by(term_id=term_id, enabled=True).all()
    out = []
    for r in rows:
        if r.ctype == "admin_soft":
            try:
                out.append({"key": r.key, "params": json.loads(r.params), "weight": max(1, 7 - r.priority)})
            except json.JSONDecodeError:
                continue
    return out


def solve(term_id, operator=""):
    """期初全量排课（详设 6.2）：读约束→建模→构造→寻优→检测→写库。返回 (结果 dict, 错误)。"""
    start = time.time()
    deadline = start + cfg.ENGINE_TIME_BUDGET_SECONDS
    refresh_caches()
    tasks = [(t.id, CourseHoursCache.get(t.course_id, 3), ClassSizeCache.get(t.class_id, 30),
              t.teacher_id, t.class_id) for t in TeachingTask.query.filter_by(term_id=term_id).all()]
    rooms = [(r.id, r.capacity, r.rtype) for r in Classroom.query.all()]
    if not tasks or not rooms:
        return None, "基础数据或开课任务为空，请先导入数据"

    model = Model(tasks, rooms, {}, _soft_rules(term_id))
    prefs_by_teacher = _prefs_by_teacher(term_id)
    rng = random.Random(2026)

    initial, err = greedy_construct(model, prefs_by_teacher)
    if err:
        return None, err
    if cfg.ENGINE_STRATEGY == "ga":
        best, _fit, info = optimize_ga(initial, model, prefs_by_teacher, _soft_rules(term_id),
                                       rng, deadline=deadline)
    else:
        best, _fit, info = optimize_sa(initial, model, prefs_by_teacher, _soft_rules(term_id),
                                       rng, deadline=deadline)
    conflicts = hard_conflicts(best, model)
    if conflicts:                                  # 防御分支：记录并回退重试（详设 6.6(3)）
        for _ in range(3):
            best, _fit, info = optimize_sa(best, model, prefs_by_teacher, _soft_rules(term_id),
                                           rng, iterations=500, deadline=deadline)
            conflicts = hard_conflicts(best, model)
            if not conflicts:
                break
    if conflicts:
        return None, "防御分支触发：寻优后仍存在硬冲突 %d 处，已回退未写库" % len(conflicts)

    elapsed = time.time() - start
    task_ids = [t[0] for t in tasks]
    with schedule_write_tx(operator):
        ScheduleRecord.query.filter(
            ScheduleRecord.task_id.in_(task_ids)).delete(
            synchronize_session=False)
        for bkey, (d, p0, rid) in best.assign.items():     # 块展开：每节一行（连排合并由查询层完成）
            for p in range(p0, p0 + model.block_by_key[bkey]["len"]):
                db.session.add(ScheduleRecord(task_id=bkey[0], day=d, period=p, room_id=rid))
    report = {"tasks": len(tasks), "blocks": len(best.assign),
              "elapsed_seconds": round(elapsed, 1),
              "hard_conflicts": 0, "optimizer": info,
              "score": round(_fit, 1)}
    return report, None


def relocal(term_id, affected_task_ids, operator=""):
    """局部重排（详设 6.8）：仅对受影响子集按块求解，未涉任务占用作为固定上下文。"""
    start = time.time()
    refresh_caches()
    affected = {int(x) for x in affected_task_ids}
    all_tasks = TeachingTask.query.filter_by(term_id=term_id).all()
    moved_tasks = []
    fixed_busy = {"room": set(), "teacher": set(), "class": set()}
    for t in all_tasks:
        recs = ScheduleRecord.query.filter_by(task_id=t.id).all()
        if not recs:
            continue
        if t.id in affected:
            moved_tasks.append(t)
        else:
            for rec in recs:               # 未涉任务的每节占用作为固定上下文
                fixed_busy["room"].add((rec.day, rec.period, rec.room_id))
                fixed_busy["teacher"].add((rec.day, rec.period, t.teacher_id))
                fixed_busy["class"].add((rec.day, rec.period, t.class_id))
    if not moved_tasks:
        return None, "未找到受影响的课表记录"

    tasks = [(t.id, CourseHoursCache.get(t.course_id, 3), ClassSizeCache.get(t.class_id, 30),
              t.teacher_id, t.class_id) for t in moved_tasks]
    rooms = [(r.id, r.capacity, r.rtype) for r in Classroom.query.all()]
    model = Model(tasks, rooms, {}, _soft_rules(term_id), fixed_busy=fixed_busy)
    prefs_by_teacher = _prefs_by_teacher(term_id)
    rng = random.Random(hash(tuple(sorted(affected))) & 0xFFFF)
    initial, err = greedy_construct(model, prefs_by_teacher)
    if err:
        return None, err
    best, _fit, info = optimize_sa(initial, model, prefs_by_teacher, _soft_rules(term_id),
                                   rng, iterations=800)
    conflicts = hard_conflicts(best, model, affected={t.id for t in moved_tasks})
    if conflicts:
        return None, "局部重排后仍存在硬冲突，本次调课不生效"
    elapsed = time.time() - start
    with schedule_write_tx(operator):
        for t in moved_tasks:              # 块化后每任务的记录整体重写
            ScheduleRecord.query.filter_by(task_id=t.id).delete(synchronize_session=False)
        for bkey, (d, p0, rid) in best.assign.items():
            for p in range(p0, p0 + model.block_by_key[bkey]["len"]):
                db.session.add(ScheduleRecord(task_id=bkey[0], day=d, period=p, room_id=rid))
    return {"affected": len(moved_tasks), "elapsed_seconds": round(elapsed, 1),
            "optimizer": info, "hard_conflicts": 0}, None


def refresh_caches():
    """solve 前调用：课程学时与班级人数缓存（避免逐任务查库）。"""
    from models import Course, ClassInfo
    for c in Course.query.all():
        CourseHoursCache[c.id] = c.hours
    for c in ClassInfo.query.all():
        ClassSizeCache[c.id] = c.size
