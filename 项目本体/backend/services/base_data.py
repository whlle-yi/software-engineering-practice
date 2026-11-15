# -*- coding: utf-8 -*-
"""M2 基础数据管理（详设第 4 章）：Excel/CSV 导入（整文件单事务+行号定位报告）与维护。"""
import csv
import io
from datetime import datetime

from services.dao import tx, audit
from models import (db, Teacher, Student, ClassInfo, Course, Classroom,
                    Term, TeachingTask)


def _check(value, rules):
    """规则表驱动校验：rules=[(规则名, 参数, 错误信息), ...]，返回错误信息或 None。"""
    if value is None or str(value).strip() == "":
        return "必填项缺失" if any(r[0] == "required" for r in rules) else None
    v = str(value).strip()
    for rule, arg, msg in rules:
        if rule == "int":
            try:
                iv = int(v)
                if arg and not (int(arg[0]) <= iv <= int(arg[1])):
                    return msg % v
            except ValueError:
                return msg % v
        elif rule == "enum" and v not in arg:
            return msg % v
        elif rule == "maxlen" and len(v) > arg:
            return msg % v
    return None


def import_teaching_plan(term_name, filename, content: bytes, operator=""):
    """教学计划导入（Excel/CSV）：逐行校验+查重，整文件单事务（详设 4.6）。"""
    from openpyxl import load_workbook
    rows, errors = [], []
    if filename.lower().endswith((".xlsx", ".xls")):
        wb = load_workbook(io.BytesIO(content), read_only=True)
        ws = wb.active
        it = ws.iter_rows(values_only=True)
        header = [str(c or "").strip() for c in next(it)]
        rows = [list(r) for r in it]
    else:
        text = content.decode("utf-8-sig", errors="replace")
        reader = list(csv.reader(io.StringIO(text)))
        header = [c.strip() for c in (reader[0] if reader else [])]
        rows = reader[1:]

    need = ["课程名称", "课程编号", "学时", "周次", "星期", "节次", "授课班级", "授课教师"]
    for col in need:
        if col not in header:
            return None, ["表头缺少列：%s（请使用受控导入模板）" % col], 0, 0

    idx = {name: header.index(name) for name in need}
    with tx() as s:
        term = Term.query.filter_by(name=term_name).first()
        if term is None:
            term = Term(name=term_name, status="active")
            s.add(term)
            s.flush()
        ok = 0
        for lineno, r in enumerate(rows, start=2):
            vals = [(r[idx[n]] if idx[n] < len(r) else None) for n in need]
            err = _check(vals[0], [("required", None, ""), ("maxlen", 80, "")])
            err = err or _check(vals[1], [("required", None, ""), ("maxlen", 20, "")])
            err = err or _check(vals[2], [("int", (1, 8), "学时超出范围：%s")])
            if err:
                errors.append("第 %d 行：%s" % (lineno, err))
                continue
            cname, cno, hours, weeks, day, period, klass_name, tname = [str(v).strip() for v in vals]
            course = Course.query.filter_by(cno=cno).first()
            if course is None:
                course = Course(cno=cno, name=cname, hours=int(hours))
                s.add(course)
                s.flush()
            klass = ClassInfo.query.filter_by(name=klass_name).first()
            if klass is None:
                errors.append("第 %d 行：班级不存在（%s），请先维护班级" % (lineno, klass_name))
                continue
            teacher = (Teacher.query.filter_by(name=tname).first()
                       or Teacher.query.filter_by(tno=tname).first())
            if teacher is None:
                errors.append("第 %d 行：教师不存在（%s），请先维护教师" % (lineno, tname))
                continue
            dup = TeachingTask.query.filter_by(term_id=term.id, course_id=course.id,
                                               class_id=klass.id, teacher_id=teacher.id).first()
            if dup:
                errors.append("第 %d 行：与既有开课任务重复（课程 %s × 班级 %s）" % (lineno, cno, klass_name))
                continue
            s.add(TeachingTask(term_id=term.id, course_id=course.id, teacher_id=teacher.id,
                               class_id=klass.id, weeks=weeks,
                               note="%s-%s" % (day, period)))
            ok += 1
        audit(operator, "import_plan", filename,
              "成功 %d 行，失败 %d 行" % (ok, len(errors)))
        # 整文件单事务：任一失败整体回滚由调用方判断（errors 非空则不提交）
        if errors:
            from models import db as _db
            _db.session.rollback()
            return None, errors, 0, len(rows)
        return {"success": ok, "failed": 0, "total": len(rows)}, [], ok, len(rows)


def import_teachers(content_rows, operator=""):
    """教师批量导入（表 2-1 维护功能），返回 (结果, 错误列表)。"""
    with tx() as s:
        ok = 0
        errors = []
        for lineno, (tno, name, title, phone) in enumerate(content_rows, start=2):
            if Teacher.query.filter_by(tno=str(tno).strip()).first():
                errors.append("第 %d 行：教师编号已存在（%s）" % (lineno, tno))
                continue
            s.add(Teacher(tno=str(tno).strip(), name=str(name).strip(),
                          title=str(title or "").strip(), phone=str(phone or "").strip()))
            ok += 1
        audit(operator, "import_teachers", "teacher", "成功 %d" % ok)
        if errors:
            db.session.rollback()
            return None, errors
        return {"success": ok}, []


def import_classrooms(content_rows, operator=""):
    with tx() as s:
        ok = 0
        errors = []
        for lineno, (rno, capacity, rtype) in enumerate(content_rows, start=2):
            if Classroom.query.filter_by(rno=str(rno).strip()).first():
                errors.append("第 %d 行：教室编号已存在（%s）" % (lineno, rno))
                continue
            s.add(Classroom(rno=str(rno).strip(), capacity=int(capacity or 40),
                            rtype=str(rtype or "普通").strip()))
            ok += 1
        audit(operator, "import_classrooms", "classroom", "成功 %d" % ok)
        if errors:
            db.session.rollback()
            return None, errors
        return {"success": ok}, []
