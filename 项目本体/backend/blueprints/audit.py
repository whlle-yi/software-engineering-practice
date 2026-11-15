# -*- coding: utf-8 -*-
"""审计日志查询：仅管理员可达（详设 10.2 / M8）。"""
from flask import Blueprint

from blueprints.helpers import fail, need_auth, ok
from services.dao import audit_query

bp = Blueprint("audit", __name__, url_prefix="/api/audit")


@bp.get("/list")
def api_audit_list():
    _, err = need_auth("audit", "list")
    if err:
        return err
    rows = audit_query(None)[-100:]
    return ok([{"operator": r.operator, "action": r.action, "target": r.target,
                "detail": r.detail, "created_at": r.created_at.strftime("%m-%d %H:%M")}
               for r in rows])
