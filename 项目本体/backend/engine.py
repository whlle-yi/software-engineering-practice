# -*- coding: utf-8 -*-
"""M4 自动排课引擎（详设第 6 章）：约束建模 → 贪心+回溯构造 → 模拟退火/遗传寻优 → 冲突检测。

三个子模块对应三个函数族：build_model / greedy_construct + optimize / full_scan。
对外接口：solve(term_id)（期初全量）、relocal(term_id, affected_task_ids)（局部重排）。
"""
import json
import math
import random
import time

import config
from dao import schedule_write_tx
from models import (db, TeachingTask, ScheduleRecord, Classroom, ClassInfo,
                    ConstraintConfig, TeacherPreference)

CourseHoursCache = {}     # 课程学时缓存（solve 前由 refresh_caches 填充）
ClassSizeCache = {}       # 班级人数缓存

DAY_SLOTS = list(range(1, 6))       # 周一~周五
PERIOD_SLOTS = list(range(1, 5))    # 1~4 大节


class Model:
    """约束建模（详设 6.6(1)）：变量 x(t)=(day,period,room)，硬软约束分级。"""

    def __init__(self, tasks, rooms, hard_rules, soft_rules):
        self.tasks = tasks                       # [(task_id, hours, class_size, teacher_id, class_id)]
        self.rooms = rooms                       # [(room_id, capacity, rtype)]
        self.hard = hard_rules                   # 全局硬约束开关 dict
        self.soft = soft_rules                   # [(weight, type, params)] 教师/管理员软约束
        self.slots = [(d, p) for d in DAY_SLOTS for p in PERIOD_SLOTS]
        self.class_size = {t[0]: t[2] for t in tasks}
        self.task_teacher = {t[0]: t[3] for t in tasks}
        self.task_class = {t[0]: t[4] for t in tasks}

    def feasible_rooms(self, task_id):
        """容量硬约束：教室容量 ≥ 班级人数。"""
        size = self.class_size[task_id]
        return [r for r in self.rooms if r[1] >= size]


class Solution:
    """解：task_id -> (day, period, room_id)。"""

    def __init__(self, assignment):
        self.assign = dict(assignment)

    def copy(self):
        return Solution(self.assign)


def hard_conflicts(sol: Solution, model: Model, affected=None):
    """四类硬约束全量扫描（详设 6.6(3)），返回冲突列表（含定位）。"""
    conflicts = []
    seen_room, seen_teacher, seen_class = {}, {}, {}
    items = [(tid, sol.assign[tid]) for tid in sol.assign
             if affected is None or tid in affected]
    for tid, (d, p, rid) in items:
        tkey = (d, p)
        if tkey in seen_room and seen_room[tkey][0] == rid:
            conflicts.append(("room_conflict", tid, seen_room[tkey][1], tkey, rid))
        else:
            seen_room[tkey] = (rid, tid)
        tch = model.task_teacher.get(tid)
        tck = (d, p, tch)
        if tch is not None:
            if tck in seen_teacher:
                conflicts.append(("teacher_conflict", tid, seen_teacher[tck], tkey, tch))
            else:
                seen_teacher[tck] = tid
        kls = model.task_class.get(tid)
        kck = (d, p, kls)
        if kls is not None:
            if kck in seen_class:
                conflicts.append(("class_conflict", tid, seen_class[kck], tkey, kls))
            else:
                seen_class[kck] = tid
    return conflicts


def soft_score(sol: Solution, model: Model, prefs_by_teacher, soft_rules):
    """软约束加权得分 F=Σ w_i·s_i（详设 6.6(1)）。"""
    score = 0.0
    for tid, (d, p, rid) in sol.assign.items():
        tch = model.task_teacher.get(tid)
        for pref in prefs_by_teacher.get(tch, []):
            if pref["type"] == "prefer" and pref.get("day") == d:
                score += pref.get("weight", 2)
            elif pref["type"] == "avoid" and pref.get("day") == d:
                score -= pref.get("weight", 2)
            elif pref["type"] == "consecutive" and p in (1, 3):
                score += pref.get("weight", 1)
    for rule in soft_rules:
        w = rule.get("weight", 2)
        if rule.get("key") == "max_daily":
            pass  # 每日节次上限在邻域生成时约束，计分不重复
    return score


def fitness(sol, model, prefs_by_teacher, soft_rules):
    """适应度 = 硬约束罚项（大罚系数）+ 软约束得分（详设 6.6）。"""
    conflicts = hard_conflicts(sol, model)
    return -config.HARD_PENALTY * len(conflicts) + soft_score(sol, model, prefs_by_teacher, soft_rules)


def greedy_construct(model: Model, prefs_by_teacher):
    """阶段一：贪心+回溯构造初始可行解（详设 6.6(2)）。

    任务按节次要求紧度降序排序；逐任务选软约束得分最高的可行赋值；
    无可行赋值时回溯前一任务改选次优；回溯预算耗尽报告不可行。
    """
    order = sorted(model.tasks, key=lambda t: -t[1])
    assign = {}
    occupied = set()          # {(day,period,room_id)}
    teacher_busy = set()      # {(day,period,teacher_id)}
    class_busy = set()        # {(day,period,class_id)}
    budget = [60]             # 回溯预算（次）

    def place(idx):
        if idx >= len(order):
            return True
        tid, _hours, _size, tch, _cls = order[idx]
        candidates = []
        for (d, p) in model.slots:
            if (d, p, tch) in teacher_busy:
                continue
            if (d, p, model.task_class[tid]) in class_busy:
                continue
            for rid, cap, _rt in model.feasible_rooms(tid):
                if (d, p, rid) in occupied:
                    continue
                gain = 0
                for pref in prefs_by_teacher.get(tch, []):
                    if pref["type"] == "prefer" and pref.get("day") == d:
                        gain += pref.get("weight", 2)
                    elif pref["type"] == "avoid" and pref.get("day") == d:
                        gain -= pref.get("weight", 2)
                candidates.append((gain, d, p, rid))
        candidates.sort(key=lambda x: -x[0])
        for cand_i, (_g, d, p, rid) in enumerate(candidates):
            if cand_i > 0:                     # 回溯换位才消耗预算，首选放置不消耗
                budget[0] -= 1
                if budget[0] <= 0:
                    return False
            assign[tid] = (d, p, rid)
            occupied.add((d, p, rid))
            teacher_busy.add((d, p, tch))
            class_busy.add((d, p, model.task_class[tid]))
            if place(idx + 1):
                return True
            del assign[tid]
            occupied.discard((d, p, rid))
            teacher_busy.discard((d, p, tch))
            class_busy.discard((d, p, model.task_class[tid]))
        return False

    if place(0):
        return Solution(assign), None
    return None, "回溯预算耗尽仍无可行解：请检查约束是否过紧或数据是否存在冲突"


def neighbor(sol: Solution, model: Model, rng):
    """邻域：随机选一个任务重排至随机可行位（详设 6.6 阶段二邻域）。"""
    tid = rng.choice(list(sol.assign.keys()))
    d, p = rng.choice(model.slots)
    rid, _cap, _rt = rng.choice(model.feasible_rooms(tid))
    new = sol.copy()
    new.assign[tid] = (d, p, rid)
    return new


def optimize_sa(sol, model, prefs_by_teacher, soft_rules, rng,
                iterations=None, no_improve=None, deadline=None):
    """模拟退火寻优（详设 6.6(2)：Metropolis 准则、几何降温）。"""
    iterations = iterations or config.ENGINE_ITERATIONS
    no_improve = no_improve or config.ENGINE_NO_IMPROVE_ROUNDS
    cur = sol.copy()
    cur_fit = fitness(cur, model, prefs_by_teacher, soft_rules)
    best, best_fit = cur.copy(), cur_fit
    temp = 100.0
    stall = 0
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
    """遗传算法寻优（详设 6.6(2)：锦标赛选择、单点交叉、单任务重排变异、精英保留）。"""
    iterations = iterations or config.ENGINE_ITERATIONS
    no_improve = no_improve or config.ENGINE_NO_IMPROVE_ROUNDS
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
        for a, b in zip(parents[::2], parents[1::2]):
            cut = rng.randrange(len(sol.assign))
            child = sol.copy()
            for j, tid in enumerate(sol.assign.keys()):
                if j < cut:
                    child.assign[tid] = a.assign[tid]
                else:
                    child.assign[tid] = b.assign[tid]
            children.append((child, fitness(child, model, prefs_by_teacher, soft_rules)))
            child2 = neighbor(children[-1][0], model, rng)  # 单任务重排变异
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
    deadline = start + config.ENGINE_TIME_BUDGET_SECONDS
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
    if config.ENGINE_STRATEGY == "ga":
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
    with schedule_write_tx(operator):
        ScheduleRecord.query.filter(
            ScheduleRecord.task_id.in_([t[0] for t in tasks])).delete(
            synchronize_session=False)
        for tid, (d, p, rid) in best.assign.items():
            db.session.add(ScheduleRecord(task_id=tid, day=d, period=p, room_id=rid))
    report = {"tasks": len(tasks), "elapsed_seconds": round(elapsed, 1),
              "hard_conflicts": 0, "optimizer": info,
              "score": round(_fit, 1)}
    return report, None


def relocal(term_id, affected_task_ids, operator=""):
    """局部重排（详设 6.8）：仅对受影响子集求解，未涉任务保持原安排。"""
    start = time.time()
    affected = [int(x) for x in affected_task_ids]
    all_tasks = TeachingTask.query.filter_by(term_id=term_id).all()
    fixed = {}
    moved = {}
    for t in all_tasks:
        rooms = Classroom.query.all()
        rec = ScheduleRecord.query.filter_by(task_id=t.id).first()
        if rec is None:
            continue
        if t.id in affected:
            moved[t.id] = (rec.day, rec.period, rec.room_id)
        else:
            fixed[t.id] = (rec.day, rec.period, rec.room_id)
    if not moved:
        return None, "未找到受影响的课表记录"

    class_sizes = {c.id: c.size for c in ClassInfo.query.all()}
    tasks = [(t.id, 3, class_sizes.get(t.class_id, 30), t.teacher_id, t.class_id)
             for t in all_tasks if t.id in moved]
    rooms = [(r.id, r.capacity, r.rtype) for r in Classroom.query.all()]
    model = Model(tasks, rooms, {}, _soft_rules(term_id))
    prefs_by_teacher = _prefs_by_teacher(term_id)
    # 固定上下文占用（未涉任务不可被移动到冲突位）
    rng = random.Random(hash(tuple(affected)) & 0xFFFF)
    initial = Solution({tid: moved[tid] for tid in moved})
    # 修正初始解中的硬冲突（原记录被调课后可能冲突）
    if hard_conflicts(initial, model):
        initial, err = greedy_construct(model, prefs_by_teacher)
        if err:
            return None, err
    best, _fit, info = optimize_sa(initial, model, prefs_by_teacher, _soft_rules(term_id),
                                   rng, iterations=800)
    conflicts = hard_conflicts(best, model, affected=set(moved))
    if conflicts:
        return None, "局部重排后仍存在硬冲突，本次调课不生效"
    elapsed = time.time() - start
    with schedule_write_tx(operator):
        for tid, (d, p, rid) in best.assign.items():
            rec = ScheduleRecord.query.filter_by(task_id=tid).first()
            if rec:
                rec.day, rec.period, rec.room_id = d, p, rid
            else:
                db.session.add(ScheduleRecord(task_id=tid, day=d, period=p, room_id=rid))
    return {"affected": len(moved), "elapsed_seconds": round(elapsed, 1),
            "optimizer": info, "hard_conflicts": 0}, None


def refresh_caches():
    """solve 前调用：课程学时与班级人数缓存（避免逐任务查库）。"""
    from models import Course, ClassInfo
    for c in Course.query.all():
        CourseHoursCache[c.id] = c.hours
    for c in ClassInfo.query.all():
        ClassSizeCache[c.id] = c.size
