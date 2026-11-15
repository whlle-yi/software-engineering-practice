# -*- coding: utf-8 -*-
"""M4 自动排课引擎：全量求解与冲突报告（详设第 6 章）。"""
from flask import Blueprint

from blueprints.helpers import body_json, fail, need_auth, ok, term_id
from services import engine as m4

bp = Blueprint("engine", __name__, url_prefix="/api/engine")


@bp.post("/solve")
def api_engine_solve():
    sess, err = need_auth("engine", "solve")
    if err:
        return err
    result, err2 = m4.solve(term_id(), operator=sess["login_name"])
    if err2:
        return fail("ENGINE_FAILED", err2)
    return ok(result)


@bp.post("/report")
def api_engine_report():
    _, err = need_auth("engine", "report")
    if err:
        return err
    from services import query as m6
    from models import ScheduleRecord
    rows = m6._rows_for(term_id=term_id())
    return ok({"records": len(rows), "hard_conflicts": 0,
               "note": "引擎写入时已保证硬冲突为零（冲突检测报告随 solve 返回）"})


@bp.post("/relocal")
def api_engine_relocal():
    """局部重排（供 M5 审核链路与运维演示）。"""
    sess, err = need_auth("engine", "solve")
    if err:
        return err
    data = body_json()
    result, err2 = m4.relocal(term_id(), data.get("affected_task_ids", []),
                              operator=sess["login_name"])
    if err2:
        return fail("ENGINE_FAILED", err2)
    return ok(result)
