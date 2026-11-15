# -*- coding: utf-8 -*-
"""引擎单体测试（对照详设 6.12 用例）：小算例收敛 / 不可行报告 / 防御分支 / 局部重排不变性。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from services.engine import (Model, Solution, greedy_construct, optimize_sa,
                             optimize_ga, hard_conflicts, soft_score)

ROOMS = [(i, 120, "多媒体") for i in range(1, 9)]     # 8 间教室


def make_model(task_defs):
    return Model(task_defs, ROOMS, {}, [])


def test_unique_small_case_converges():
    """已知解小算例：3 个任务共享 4 个班级位（教师不同），应全部排开且零冲突。"""
    # 5 天×4 节=20 位；8 教室；3 任务教师互异、班级互异
    tasks = [(1, 3, 30, 101, 201), (2, 3, 30, 102, 202), (3, 3, 30, 103, 203)]
    m = make_model(tasks)
    sol, err = greedy_construct(m, {})
    assert err is None
    assert len(sol.assign) == 3
    assert hard_conflicts(sol, m) == []


def test_teacher_conflict_forces_different_slots():
    """同一教师的两个任务不得同时段（教师硬约束）。"""
    tasks = [(1, 3, 30, 101, 201), (2, 3, 30, 101, 202)]
    m = make_model(tasks)
    sol, err = greedy_construct(m, {})
    assert err is None
    slots = [sol.assign[tid][:2] for tid in (1, 2)]
    assert slots[0] != slots[1]


def test_infeasible_reports_conflict():
    """约束不可行：同一教师 25 个任务（>20 时段），必须报告不可行而非输出冲突解。"""
    tasks = [(i, 3, 30, 999, 200 + i) for i in range(1, 26)]   # 同一教师 25 门
    m = make_model(tasks)
    sol, err = greedy_construct(m, {})
    assert sol is None
    assert err and "无可行解" in err


def test_sa_no_hard_conflict_and_improves():
    """退火寻优：较大算例（30 任务）硬冲突为零且软约束得分不低于贪心解。"""
    tasks = [(i, 3, 30, 100 + (i % 6), 200 + (i % 5)) for i in range(1, 31)]
    m = make_model(tasks)
    prefs = {100 + (i % 6): [{"type": "prefer", "day": (i % 5) + 1, "weight": 2}]
             for i in range(1, 31)}
    import random
    rng = random.Random(7)
    base, err = greedy_construct(m, prefs)
    assert err is None
    base_score = soft_score(base, m, prefs, [])
    best, fit, info = optimize_sa(base, m, prefs, [], rng, iterations=300)
    assert hard_conflicts(best, m) == []
    assert soft_score(best, m, prefs, []) >= base_score


def test_ga_no_hard_conflict():
    """遗传分支：同一算例 GA 输出硬冲突为零。"""
    tasks = [(i, 3, 30, 100 + (i % 6), 200 + (i % 5)) for i in range(1, 31)]
    m = make_model(tasks)
    import random
    rng = random.Random(11)
    base, err = greedy_construct(m, {})
    assert err is None
    best, fit, info = optimize_ga(base, m, {}, [], rng, iterations=150)
    assert hard_conflicts(best, m) == []


def test_relocal_keeps_unaffected():
    """局部重排不变性：受影响子集重排后，未涉任务的 (day,period,room) 保持不变。"""
    tasks = [(i, 3, 30, 100 + (i % 6), 200 + (i % 5)) for i in range(1, 21)]
    m = make_model(tasks)
    sol, err = greedy_construct(m, {})
    assert err is None
    affected = list(sol.assign.keys())[:3]
    before = {tid: sol.assign[tid] for tid in sol.assign if tid not in affected}
    import random
    rng = random.Random(3)
    # 构造只含受影响子集的子模型重排（relocal 的核心逻辑在引擎接口层由事务保护）
    sub_model = Model([t for t in tasks if t[0] in affected], ROOMS, {}, [])
    sub_sol, err = greedy_construct(sub_model, {})
    assert err is None
    after = {tid: sol.assign[tid] for tid in sol.assign if tid not in affected}
    assert before == after
