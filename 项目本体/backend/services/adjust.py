# -*- coding: utf-8 -*-
"""M5 调课申请与审核（详设第 7 章）：状态机 + 与局部重排同事务（表 7-1）。"""
from datetime import datetime

from services.dao import tx, audit
from models import db, AdjustRequest, ScheduleRecord, Notification, SysUser, TeachingTask

STATES = ("待审核", "通过", "退回")


def apply(teacher_id, record_id, expectation, reason, operator=""):
    """教师提交调课申请：建记录、审计留痕、通知管理员（表 7-1 行 1）。"""
    rec = ScheduleRecord.query.get(record_id)
    if rec is None:
        return None, "课表记录不存在"
    if rec.task and rec.task.teacher_id != teacher_id:
        return None, "只能对本人的课表发起调课"
    original = "周%d 第%d节 %s" % (rec.day, rec.period, rec.room.rno if rec.room else rec.room_id)
    with tx() as s:
        req = AdjustRequest(teacher_id=teacher_id, record_id=record_id,
                            original=original, expectation=expectation, reason=reason,
                            status="待审核", created_at=datetime.now())
        s.add(req)
        s.flush()
        audit(operator or ("t%d" % teacher_id), "adjust_apply", "adjust_request#%d" % req.id,
              "%s → %s" % (original, expectation))
        for u in SysUser.query.filter_by(role="admin").all():
            s.add(Notification(user_id=u.id, content="收到新调课申请 #%d（教师 %s：%s → %s）"
                               % (req.id, teacher_id, original, expectation),
                               created_at=datetime.now()))
        return req, None


def review(req_id, verdict, comment, operator=""):
    """管理员审核（表 7-1 行 2~4）。verdict ∈ {通过, 退回}。

    通过 → 同一事务内调度 M4 局部重排并复检；不可行则整体回滚、状态保持待审核。
    """
    req = AdjustRequest.query.get(req_id)
    if req is None:
        return None, "申请不存在"
    if req.status != "待审核":
        return None, "该申请已流转至终态（%s）" % req.status
    from services.engine import relocal
    if verdict == "退回":
        with tx() as s:
            req.status = "退回"
            req.review_comment = comment or ""
            audit(operator, "adjust_review", "adjust_request#%d" % req_id, "退回：" + (comment or ""))
            s.add(Notification(user_id=_teacher_user_id(req.teacher_id),
                               content="调课申请 #%d 已退回：%s" % (req_id, comment or ""),
                               created_at=datetime.now()))
        return req, None
    if verdict != "通过":
        return None, "非法审核结论：%s" % verdict
    # 通过：同事务局部重排——relocal 内部使用 schedule_write_tx（独立事务），
    # 原型实现：先重排成功再更新申请状态，失败则申请保持待审核（表 7-1 行 4）。
    result, err = relocal(req.record.task.term_id, [req.record_id], operator=operator)
    if err:
        with tx() as s:
            audit(operator, "adjust_review", "adjust_request#%d" % req_id,
                  "重排不可行：%s" % err)
            s.add(Notification(user_id=_teacher_user_id(req.teacher_id),
                               content="调课申请 #%d 重排不可行：%s（申请保持待审核）" % (req_id, err),
                               created_at=datetime.now()))
        return req, "重排不可行：%s（申请保持待审核，可调整期望安排后重新审核）" % err
    with tx() as s:
        req.status = "通过"
        req.review_comment = comment or ""
        audit(operator, "adjust_review", "adjust_request#%d" % req_id, "通过并已重排")
        s.add(Notification(user_id=_teacher_user_id(req.teacher_id),
                           content="调课申请 #%d 已通过并生效" % req_id,
                           created_at=datetime.now()))
        # 变更事件 → M6 通知受影响班级学生
        task = TeachingTask.query.get(req.record.task_id)
        if task:
            _notify_class(s, task.class_id, "课程「%s」的课表已调整，请查看最新课表" % (
                task.course.name if task.course else ""))
    return req, None


def _teacher_user_id(teacher_id):
    u = SysUser.query.filter_by(role="teacher").all()
    from models import Teacher
    t = Teacher.query.get(teacher_id)
    if t:
        u = SysUser.query.filter_by(role="teacher").join(
            Teacher, SysUser.ref_id == t.id).all()
        if u:
            return u[0].id
    # 回退：按 t 编号约定（t%02d 与教师序号一致）
    guess = SysUser.query.filter_by(login_name="t%02d" % (teacher_id % 100)).first()
    return guess.id if guess else None


def _notify_class(s, class_id, content):
    """变更通知：原型简化——通知全部学生账号（M6 通知算法按班级过滤，详设 8.6）。"""
    from models import Student, SysUser
    user_ids = set()
    for st in Student.query.filter_by(class_id=class_id).all():
        u = SysUser.query.filter(SysUser.role == "student",
                                 SysUser.login_name == "s" + st.sno[-4:]).first()
        if u:
            user_ids.add(u.id)
    for uid in user_ids:
        s.add(Notification(user_id=uid, content=content, created_at=datetime.now()))
