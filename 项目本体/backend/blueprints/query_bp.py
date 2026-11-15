# -*- coding: utf-8 -*-
"""M6 课表查询与通知：四视图、导出、站内通知（详设第 8 章）。"""
from flask import Blueprint, Response, request

from blueprints.helpers import body_json, fail, need_auth, ok, term_id
from services import query as m6

bp = Blueprint("query", __name__, url_prefix="/api/query")


@bp.get("/schedule")
def api_query_schedule():
    sess, err = need_auth("query", "schedule")
    if err:
        return err
    from models import Student
    view_type = request.args.get("view", "teacher")
    ref = request.args.get("ref", "")
    if sess["role"] == "teacher":
        view_type, ref = "teacher", sess["ref_id"]
    elif sess["role"] == "student":
        rows, err2 = m6.view("student", ref, term_id(),
                             student_sno=request.args.get("sno", ""))
        if err2:
            return fail("NOT_FOUND", err2, 404)
        return ok({"view": "student", "rows": rows})
    rows, err2 = m6.view(view_type, int(ref) if ref and ref.isdigit() else None,
                         term_id(), student_sno=request.args.get("sno"))
    if err2:
        return fail("NOT_FOUND", err2, 404)
    return ok({"view": view_type, "rows": rows})


@bp.get("/export")
def api_query_export():
    sess, err = need_auth("query", "export")
    if err:
        return err
    view_type = request.args.get("view", "teacher")
    ref = request.args.get("ref", "")
    rows, err2 = m6.view(view_type, int(ref) if ref and ref.isdigit() else None,
                         term_id(), student_sno=request.args.get("sno"))
    if err2:
        return fail("NOT_FOUND", err2, 404)
    fmt = request.args.get("fmt", "csv")
    if fmt == "xlsx":
        content = m6.export_xlsx(rows)
        return Response(content,
                        mimetype="application/vnd.openxmlformats-officedocument"
                                 ".spreadsheetml.sheet",
                        headers={"Content-Disposition": "attachment; filename=schedule.xlsx"})
    content = m6.export_csv(rows)
    return Response(content, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=schedule.csv"})


@bp.get("/notifications")
def api_notifications():
    sess, err = need_auth("query", "notifications")
    if err:
        return err
    from models import SysUser
    login_name = request.args.get("login_name", "")
    me = SysUser.query.filter_by(login_name=login_name).first() if login_name else None
    if login_name and me is None:
        return fail("NOT_FOUND", "用户不存在", 404)
    uid = me.id if me else 1
    return ok({"items": m6.notifications_for(uid)})


@bp.post("/notifications/read")
def api_notifications_read():
    _, err = need_auth("query", "notifications")
    if err:
        return err
    data = body_json()
    m6.mark_read(int(data.get("user_id", 1)), data.get("id"))
    return ok()
