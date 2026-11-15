# -*- coding: utf-8 -*-
"""M2 基础数据管理：导入与维护（详设第 4 章）。"""
from flask import Blueprint, jsonify, request

from blueprints.helpers import body_json, fail, need_auth, ok, term_id
from services import base_data as m2

bp = Blueprint("base", __name__, url_prefix="/api/base")


@bp.post("/import-plan")
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
        return jsonify({"code": "IMPORT_REJECTED",
                        "message": "导入被拒绝（整文件回滚）",
                        "data": {"errors": errors[:20], "total": total}}), 400
    return ok(result)


@bp.get("/teachers")
def api_teachers():
    _, err = need_auth("base", "list")
    if err:
        return err
    from models import Teacher
    return ok([{"id": t.id, "tno": t.tno, "name": t.name, "title": t.title}
               for t in Teacher.query.all()])


@bp.get("/rooms")
def api_rooms():
    _, err = need_auth("base", "list")
    if err:
        return err
    from models import Classroom
    return ok([{"id": r.id, "rno": r.rno, "capacity": r.capacity, "rtype": r.rtype}
               for r in Classroom.query.all()])


@bp.get("/courses")
def api_courses():
    _, err = need_auth("base", "list")
    if err:
        return err
    from models import Course
    return ok([{"id": c.id, "cno": c.cno, "name": c.name, "hours": c.hours, "ctype": c.ctype}
               for c in Course.query.all()])


@bp.get("/classes")
def api_classes():
    _, err = need_auth("base", "list")
    if err:
        return err
    from models import ClassInfo
    return ok([{"id": c.id, "name": c.name, "grade": c.grade, "size": c.size}
               for c in ClassInfo.query.all()])


@bp.get("/tasks")
def api_tasks():
    _, err = need_auth("base", "list")
    if err:
        return err
    from models import TeachingTask
    tasks = TeachingTask.query.filter_by(term_id=term_id()).all()
    return ok([{"id": t.id, "course": t.course.name if t.course else "",
                "teacher": t.teacher.name if t.teacher else "",
                "class": t.klass.name if t.klass else "", "weeks": t.weeks}
               for t in tasks])
