# -*- coding: utf-8 -*-
"""M3 排课约束配置：约束 CRUD、启停、偏好状态（详设第 5 章）。"""
import json

from flask import Blueprint

from blueprints.helpers import body_json, fail, need_auth, ok, term_id
from services import constraints as m3

bp = Blueprint("constraint", __name__, url_prefix="/api/constraint")


@bp.get("/list")
def api_constraint_list():
    _, err = need_auth("constraint", "list")
    if err:
        return err
    from models import ConstraintConfig, TeacherPreference
    rows = ConstraintConfig.query.filter_by(term_id=term_id()).all()
    prefs = TeacherPreference.query.filter_by(term_id=term_id()).all()
    return ok({"constraints": [{"id": c.id, "key": c.key, "ctype": c.ctype, "params": c.params,
                                "priority": c.priority, "enabled": c.enabled} for c in rows],
               "preferences": [{"id": p.id, "teacher_id": p.teacher_id, "ptype": p.ptype,
                                "content": p.content, "priority": p.priority, "status": p.status}
                               for p in prefs]})


@bp.post("/add")
def api_constraint_add():
    sess, err = need_auth("constraint", "add")
    if err:
        return err
    data = body_json()
    c, err2 = m3.add_constraint(term_id(), data.get("key", ""),
                                json.dumps(data.get("params", {}), ensure_ascii=False),
                                int(data.get("priority", 5)), sess["login_name"])
    if err2:
        return fail("CONSTRAINT_CONFLICT", err2)
    return ok({"id": c.id})


@bp.post("/status")
def api_constraint_status():
    sess, err = need_auth("constraint", "status")
    if err:
        return err
    data = body_json()
    err2 = m3.update_status(int(data.get("id")), bool(data.get("enabled")), sess["login_name"])
    if err2:
        return fail("NOT_FOUND", err2, 404)
    return ok()


@bp.post("/preference-status")
def api_pref_status():
    sess, err = need_auth("constraint", "status")
    if err:
        return err
    data = body_json()
    err2 = m3.set_preference_status(int(data.get("id")), data.get("status"), sess["login_name"])
    if err2:
        return fail("INVALID", err2)
    return ok()
