# -*- coding: utf-8 -*-
"""M6 课表查询与通知（详设第 8 章）：四视图过滤投影、导出、通知查询。

四视图 = 同一 schedule_record 集在不同维度的过滤投影（详设 8.6）；
导出 = 模板化生成 CSV/Excel（受控样式，详设 8.6）；
通知 = 变更事件产生的站内消息查询（由 adjust.py 写入）。
"""
import csv
import io
from datetime import datetime

from models import (db, ScheduleRecord, TeachingTask, Course, Teacher, Classroom,
                    ClassInfo, Student, Term, Notification, SysUser)


def _rows_for(teacher_id=None, class_id=None, room_id=None, student_sno=None, term_id=None):
    """四视图统一过滤投影（详设 8.6 算法）。"""
    q = ScheduleRecord.query.join(TeachingTask, ScheduleRecord.task_id == TeachingTask.id)
    if term_id:
        q = q.filter(TeachingTask.term_id == term_id)
    if teacher_id:
        q = q.filter(TeachingTask.teacher_id == teacher_id)
    if class_id:
        q = q.filter(TeachingTask.class_id == class_id)
    if room_id:
        q = q.filter(ScheduleRecord.room_id == room_id)
    records = q.order_by(ScheduleRecord.day, ScheduleRecord.period).all()
    if student_sno:
        st = Student.query.filter_by(sno=student_sno).first()
        if st:
            records = [r for r in records if r.task.class_id == st.class_id]
    out = []
    for r in records:
        out.append({
            "record_id": r.id,
            "task_id": r.task_id,
            "course": r.task.course.name if r.task.course else "",
            "teacher": r.task.teacher.name if r.task.teacher else "",
            "class": r.task.klass.name if r.task.klass else "",
            "day": r.day, "period": r.period,
            "room": r.room.rno if r.room else str(r.room_id),
            "weeks": r.weeks,
        })
    return out


def view(view_type, ref, term_id, student_sno=None):
    """view_type ∈ teacher/class/room/student。返回 (行列表, 错误)。"""
    if view_type == "teacher":
        return _rows_for(teacher_id=ref, term_id=term_id), None
    if view_type == "class":
        return _rows_for(class_id=ref, term_id=term_id), None
    if view_type == "room":
        return _rows_for(room_id=ref, term_id=term_id), None
    if view_type == "student":
        st = Student.query.filter_by(sno=str(student_sno)).first()
        if st is None:
            return None, "学号不存在"
        return _rows_for(class_id=st.class_id, student_sno=student_sno, term_id=term_id), None
    return None, "未知视图类型：%s" % view_type


def export_csv(rows):
    """导出 CSV（详设 8.6：受控模板，Excel 打开无乱码——UTF-8 BOM）。"""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["课程", "教师", "班级", "星期", "节次", "教室", "周次"])
    for r in rows:
        writer.writerow([r["course"], r["teacher"], r["class"],
                         "周%d" % r["day"], "第%d节" % r["period"], r["room"], r["weeks"]])
    return buf.getvalue().encode("utf-8-sig")


def export_xlsx(rows):
    """导出 Excel（openpyxl，详设 8.6 受控模板）。"""
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "课表"
    ws.append(["课程", "教师", "班级", "星期", "节次", "教室", "周次"])
    for r in rows:
        ws.append([r["course"], r["teacher"], r["class"],
                   "周%d" % r["day"], "第%d节" % r["period"], r["room"], r["weeks"]])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def notifications_for(user_id):
    msgs = Notification.query.filter_by(user_id=user_id).order_by(
        Notification.created_at.desc()).all()
    return [{"id": n.id, "content": n.content, "read": n.read_flag,
             "created_at": n.created_at.strftime("%m-%d %H:%M")} for n in msgs]


def mark_read(user_id, nid=None):
    from dao import tx
    with tx() as s:
        q = Notification.query.filter_by(user_id=user_id, read_flag=False)
        if nid:
            q = Notification.query.filter_by(user_id=user_id, id=nid)
        for n in q.all():
            n.read_flag = True
    return None
