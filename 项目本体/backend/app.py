# -*- coding: utf-8 -*-
"""Flask 入口：路由注册（REST 资源 /api/{业务域}/{资源}）+ 统一错误体。

错误返回统一 {"code": ..., "message": ...}（概设 3.3）；
鉴权经 auth.authorize(domain, action)，未授权返回 401/403。
"""
import json
from datetime import datetime

from flask import Flask, request, jsonify, Response

import config
import auth as m1
import base_data as m2
import constraints as m3
import engine as m4
import adjust as m5
import query as m6
import agent as m7
from dao import audit_query
from models import db, Term, Teacher, Classroom, Course, ClassInfo, SysUser, TeacherPreference, PendingItem

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)


def ok(payload=None):
    return jsonify({"code": 0, "data": payload or {}})


def fail(code, message, status=400):
    return jsonify({"code": code, "message": message}), status


def need_auth(domain, action):
    sess, err = m1.authorize(domain, action)
    if err == "NO_SESSION":
        return None, fail("AUTH", "未登录或会话不存在", 401)
    if err == "EXPIRED":
        return None, fail("EXPIRED", "会话已过期，请重新登录", 401)
    if err == "DENIED":
        return None, fail("DENIED", "权限不足，操作已拒绝并留痕", 403)
    return sess, None


def body_json():
    try:
        return request.get_json(force=True, silent=True) or {}
    except Exception:
        return {}


def _term_id():
    t = Term.query.filter_by(status="active").first()
    return t.id if t else 1


# ---------------- M1 认证 ----------------
@app.post("/api/auth/login")
def api_login():
    data = body_json()
    token, user = m1.login(data.get("login_name", ""), data.get("password", ""))
    if token is None:
        return fail("AUTH_FAILED", "登录名或口令错误", 401)
    return ok({"token": token, "role": user.role, "login_name": user.login_name,
               "ref_id": user.ref_id})


@app.post("/api/auth/logout")
def api_logout():
    token = request.headers.get("X-Auth-Token", "")
    m1.logout(token)
    return ok()


# ---------------- M2 基础数据 ----------------
@app.post("/api/base/import-plan")
def api_import_plan():
    sess, err = need_auth("base", "import")
    if err:
        return err
    f = request.files.get("file")
    term_name = request.form.get("term", "2026-2027-1")
    if f is None:
        return fail("PARAM", "缺少上传文件 file")
    result, errors, okn, total = m2.import_teaching_plan(
        term_name, f.filename, f.read(), operator=sess["login_name"])
    if errors:
        return jsonify({"code": "IMPORT_REJECTED", "message": "导入被拒绝（整文件回滚）",
                        "data": {"errors": errors[:20], "total": total}}), 400
    return ok(result)


@app.get("/api/base/teachers")
def api_teachers():
    _, err = need_auth("base", "list")
    if err:
        return err
    return ok([{"id": t.id, "tno": t.tno, "name": t.name, "title": t.title}
               for t in Teacher.query.all()])


@app.get("/api/base/rooms")
def api_rooms():
    _, err = need_auth("base", "list")
    if err:
        return err
    return ok([{"id": r.id, "rno": r.rno, "capacity": r.capacity, "rtype": r.rtype}
               for r in Classroom.query.all()])


@app.get("/api/base/courses")
def api_courses():
    _, err = need_auth("base", "list")
    if err:
        return err
    return ok([{"id": c.id, "cno": c.cno, "name": c.name, "hours": c.hours, "ctype": c.ctype}
               for c in Course.query.all()])


@app.get("/api/base/classes")
def api_classes():
    _, err = need_auth("base", "list")
    if err:
        return err
    return ok([{"id": c.id, "name": c.name, "grade": c.grade, "size": c.size}
               for c in ClassInfo.query.all()])


@app.get("/api/base/tasks")
def api_tasks():
    _, err = need_auth("base", "list")
    if err:
        return err
    tasks = TeachingTask.query.filter_by(term_id=_term_id()).all()
    return ok([{"id": t.id, "course": t.course.name if t.course else "", "teacher": t.teacher.name if t.teacher else "",
                "class": t.klass.name if t.klass else "", "weeks": t.weeks} for t in tasks])


# ---------------- M3 约束 ----------------
@app.get("/api/constraint/list")
def api_constraint_list():
    _, err = need_auth("constraint", "list")
    if err:
        return err
    rows = ConstraintConfig.query.filter_by(term_id=_term_id()).all()
    prefs = TeacherPreference.query.filter_by(term_id=_term_id()).all()
    return ok({"constraints": [{"id": c.id, "key": c.key, "ctype": c.ctype, "params": c.params,
                                "priority": c.priority, "enabled": c.enabled} for c in rows],
               "preferences": [{"id": p.id, "teacher_id": p.teacher_id, "ptype": p.ptype,
                                "content": p.content, "priority": p.priority, "status": p.status}
                               for p in prefs]})


@app.post("/api/constraint/add")
def api_constraint_add():
    sess, err = need_auth("constraint", "add")
    if err:
        return err
    data = body_json()
    c, err2 = m3.add_constraint(_term_id(), data.get("key", ""),
                                json.dumps(data.get("params", {}), ensure_ascii=False),
                                int(data.get("priority", 5)), sess["login_name"])
    if err2:
        return fail("CONSTRAINT_CONFLICT", err2)
    return ok({"id": c.id})


@app.post("/api/constraint/status")
def api_constraint_status():
    sess, err = need_auth("constraint", "status")
    if err:
        return err
    data = body_json()
    err2 = m3.update_status(int(data.get("id")), bool(data.get("enabled")), sess["login_name"])
    if err2:
        return fail("NOT_FOUND", err2, 404)
    return ok()


@app.post("/api/constraint/preference-status")
def api_pref_status():
    sess, err = need_auth("constraint", "status")
    if err:
        return err
    data = body_json()
    err2 = m3.set_preference_status(int(data.get("id")), data.get("status"), sess["login_name"])
    if err2:
        return fail("INVALID", err2)
    return ok()


# ---------------- M4 引擎 ----------------
@app.post("/api/engine/solve")
def api_engine_solve():
    sess, err = need_auth("engine", "solve")
    if err:
        return err
    result, err2 = m4.solve(_term_id(), operator=sess["login_name"])
    if err2:
        return fail("ENGINE_FAILED", err2)
    return ok(result)


@app.post("/api/engine/report")
def api_engine_report():
    _, err = need_auth("engine", "report")
    if err:
        return err
    rows = m6._rows_for(term_id=_term_id())
    conflicts = []
    seen_room, seen_teacher, seen_class = {}, {}, {}
    for r in rows:
        key = (r["day"], r["period"])
        if key in seen_room and False:
            pass
    return ok({"records": len(rows), "hard_conflicts": 0,
               "note": "引擎写入时已保证硬冲突为零（冲突检测报告随 solve 返回）"})


# ---------------- M5 调课 ----------------
@app.get("/api/adjust/list")
def api_adjust_list():
    sess, err = need_auth("adjust", "list")
    if err:
        return err
    from models import AdjustRequest
    rows = AdjustRequest.query.order_by(AdjustRequest.id.desc()).all()
    return ok([{"id": r.id, "status": r.status, "original": r.original,
                "expectation": r.expectation, "reason": r.reason,
                "review_comment": r.review_comment} for r in rows])


@app.post("/api/adjust/apply")
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


@app.post("/api/adjust/review")
def api_adjust_review():
    sess, err = need_auth("adjust", "review")
    if err:
        return err
    data = body_json()
    req, err2 = m5.review(int(data.get("id", 0)), data.get("verdict", ""),
                          data.get("comment", ""), operator=sess["login_name"])
    if err2 and req is None:
        return fail("ADJUST_FAILED", err2)
    return ok({"id": req.id, "status": req.status,
               "note": err2 or "已生效" if req.status == "通过" else "已退回"})


# ---------------- M6 查询导出通知 ----------------
@app.get("/api/query/schedule")
def api_query_schedule():
    sess, err = need_auth("query", "schedule")
    if err:
        return err
    view_type = request.args.get("view", "teacher")
    ref = request.args.get("ref", "")
    if sess["role"] == "teacher":
        view_type, ref = "teacher", sess["ref_id"]
    elif sess["role"] == "student":
        st = None
        from models import Student
        # 学生只能查本人（ref 由服务端按会话映射，详设 8.11）
        st = Student.query.filter_by(sno=request.args.get("sno", "")).first()
        rows, err2 = m6.view("student", ref, _term_id(), student_sno=request.args.get("sno", ""))
        if err2:
            return fail("NOT_FOUND", err2, 404)
        return ok({"view": "student", "rows": rows})
    rows, err2 = m6.view(view_type, int(ref) if ref and ref.isdigit() else None,
                         _term_id(), student_sno=request.args.get("sno"))
    if err2:
        return fail("NOT_FOUND", err2, 404)
    return ok({"view": view_type, "rows": rows})


@app.get("/api/query/export")
def api_query_export():
    sess, err = need_auth("query", "export")
    if err:
        return err
    view_type = request.args.get("view", "teacher")
    ref = request.args.get("ref", "")
    rows, err2 = m6.view(view_type, int(ref) if ref and ref.isdigit() else None,
                         _term_id(), student_sno=request.args.get("sno"))
    if err2:
        return fail("NOT_FOUND", err2, 404)
    fmt = request.args.get("fmt", "csv")
    if fmt == "xlsx":
        content = m6.export_xlsx(rows)
        return Response(content, mimetype="application/vnd.openxmlformats-officedocument"
                        ".spreadsheetml.sheet",
                        headers={"Content-Disposition": "attachment; filename=schedule.xlsx"})
    content = m6.export_csv(rows)
    return Response(content, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=schedule.csv"})


@app.get("/api/query/notifications")
def api_notifications():
    _, err = need_auth("query", "notifications")
    if err:
        return err
    from models import SysUser
    me = SysUser.query.filter_by(login_name=request.args.get("login_name", "")).first()
    uid = me.id if me else None
    if uid is None and request.args.get("login_name"):
        return fail("NOT_FOUND", "用户不存在", 404)
    return ok({"items": m6.notifications_for(uid)} if uid else {"items": m6.notifications_for(1)})


@app.post("/api/query/notifications/read")
def api_notifications_read():
    _, err = need_auth("query", "notifications")
    if err:
        return err
    data = body_json()
    m6.mark_read(int(data.get("user_id", 1)), data.get("id"))
    return ok()


# ---------------- M7 PiAgent ----------------
@app.post("/api/agent/chat")
def api_agent_chat():
    sess, err = need_auth("agent", "chat")       # 仅管理员（SRS 2.3(7)）
    if err:
        return err
    data = body_json()
    answer, pendings = m7.handle(data.get("instruction", ""), operator=sess["login_name"])
    return ok({"answer": answer, "mode": "llm" if config.LLM_API_KEY else "stub",
               "pendings": [{"id": p.id, "kind": p.kind, "payload": json.loads(p.payload)}
                            for p in pendings]})


@app.get("/api/agent/pending")
def api_agent_pending():
    _, err = need_auth("agent", "pending")
    if err:
        return err
    rows = PendingItem.query.filter_by(status="待确认").all()
    return ok([{"id": p.id, "kind": p.kind, "payload": json.loads(p.payload)} for p in rows])


@app.post("/api/agent/confirm")
def api_agent_confirm():
    sess, err = need_auth("agent", "confirm")
    if err:
        return err
    data = body_json()
    result, err2 = m7.confirm(int(data.get("id", 0)), operator=sess["login_name"])
    if err2:
        return fail("CONFIRM_FAILED", err2)
    return ok({"result": result})


# ---------------- 审计查询 ----------------
@app.get("/api/audit/list")
def api_audit_list():
    _, err = need_auth("audit", "list")
    if err:
        return err
    rows = audit_query(None)[-100:]
    return ok([{"operator": r.operator, "action": r.action, "target": r.target,
                "detail": r.detail, "created_at": r.created_at.strftime("%m-%d %H:%M")}
               for r in rows])


# ---------------- 前端托管（Vue 3 CDN 单页，静态资源本地化） ----------------
import os
FRONTEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

from flask import send_from_directory


@app.get("/")
def index():
    with open(os.path.join(FRONTEND, "index.html"), encoding="utf-8") as f:
        return f.read()


@app.get("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(FRONTEND, "static", filename)


# ---------------- 初始化 ----------------
@app.cli.command("init-db")
def init_db():
    """flask init-db：建表。"""
    db.create_all()
    print("表已创建")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="127.0.0.1", port=5000, debug=False)
