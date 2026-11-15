# -*- coding: utf-8 -*-
"""M5 调课申请与审核：状态机闭环（详设第 7 章，表 7-1）。"""
from flask import Blueprint

from blueprints.helpers import body_json, fail, need_auth, ok
from services import adjust as m5

bp = Blueprint("adjust", __name__, url_prefix="/api/adjust")


@bp.get("/list")
def api_adjust_list():
    _, err = need_auth("adjust", "list")
    if err:
        return err
    from models import AdjustRequest
    rows = AdjustRequest.query.order_by(AdjustRequest.id.desc()).all()
    return ok([{"id": r.id, "status": r.status, "original": r.original,
                "expectation": r.expectation, "reason": r.reason,
                "review_comment": r.review_comment} for r in rows])


@bp.post("/apply")
def api_adjust_apply():
    sess, err = need_auth("adjust", "apply")
    if err:
        return err
    data = body_json()
    req, err2 = m5.apply(sess["ref_id"], int(data.get("record_id", 0)),
                         data.get("expectation", ""), data.get("reason", ""),
                         operator=sess["login_name"])
    if err2:
        return fail("ADJUST_REJECT", err2)
    return ok({"id": req.id, "status": req.status})


@bp.post("/review")
def api_adjust_review():
    sess, err = need_auth("adjust", "review")
    if err:
        return err
    data = body_json()
    req, err2 = m5.review(int(data.get("id", 0)), data.get("verdict", ""),
                          data.get("comment", ""), operator=sess["login_name"])
    if err2 and req is None:
        return fail("ADJUST_FAILED", err2)
    note = err2 or ("已生效" if req.status == "通过" else "已退回")
    return ok({"id": req.id, "status": req.status, "note": note})
