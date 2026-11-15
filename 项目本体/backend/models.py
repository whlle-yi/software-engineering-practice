# -*- coding: utf-8 -*-
"""数据模型：13 张表，字段与《概要设计说明书》表 5-1~5-3 一致。

基础数据域：sys_user / teacher / student / class_info / course / classroom
排课业务域：term / teaching_task / schedule_record / adjust_request
约束与偏好域：constraint_config / teacher_preference；审计：audit_log
"""
from extensions import db


class SysUser(db.Model):
    __tablename__ = "sys_user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    login_name = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)   # salt$hash
    role = db.Column(db.String(10), nullable=False)             # admin/teacher/student
    ref_id = db.Column(db.Integer)                              # 关联教师/学生编号（管理员为空）


class Teacher(db.Model):
    __tablename__ = "teacher"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tno = db.Column(db.String(20), unique=True, nullable=False)     # 教师编号
    name = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(30))
    phone = db.Column(db.String(30))


class Student(db.Model):
    __tablename__ = "student"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sno = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("class_info.id"), nullable=False)


class ClassInfo(db.Model):
    __tablename__ = "class_info"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)    # 班级名称
    grade = db.Column(db.String(20))
    size = db.Column(db.Integer, default=0)


class Course(db.Model):
    __tablename__ = "course"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cno = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    hours = db.Column(db.Integer, nullable=False)                   # 周学时
    ctype = db.Column(db.String(20), default="必修")                 # 必修/选修


class Classroom(db.Model):
    __tablename__ = "classroom"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rno = db.Column(db.String(20), unique=True, nullable=False)     # 教室编号
    capacity = db.Column(db.Integer, nullable=False)
    rtype = db.Column(db.String(20), default="普通")                 # 多媒体/普通


class Term(db.Model):
    __tablename__ = "term"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30), unique=True, nullable=False)    # 如 2026-2027-1
    status = db.Column(db.String(10), default="active")


class TeachingTask(db.Model):
    __tablename__ = "teaching_task"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    term_id = db.Column(db.Integer, db.ForeignKey("term.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teacher.id"), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("class_info.id"), nullable=False)
    weeks = db.Column(db.String(30), default="1-16")                # 周次
    note = db.Column(db.String(100))                                # 节次要求等

    course = db.relationship("Course")
    teacher = db.relationship("Teacher")
    klass = db.relationship("ClassInfo")


class ScheduleRecord(db.Model):
    __tablename__ = "schedule_record"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey("teaching_task.id"), nullable=False)
    day = db.Column(db.Integer, nullable=False)                     # 1~5
    period = db.Column(db.Integer, nullable=False)                  # 1~4 大节
    room_id = db.Column(db.Integer, db.ForeignKey("classroom.id"), nullable=False)
    weeks = db.Column(db.String(30), default="1-16")

    task = db.relationship("TeachingTask")
    room = db.relationship("Classroom")


class AdjustRequest(db.Model):
    __tablename__ = "adjust_request"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teacher.id"), nullable=False)
    record_id = db.Column(db.Integer, db.ForeignKey("schedule_record.id"), nullable=False)
    original = db.Column(db.String(120))                            # 原安排快照
    expectation = db.Column(db.String(200), nullable=False)         # 期望安排
    reason = db.Column(db.String(200))
    status = db.Column(db.String(10), default="待审核")              # 待审核/通过/退回
    review_comment = db.Column(db.String(200))
    created_at = db.Column(db.DateTime)

    record = db.relationship("ScheduleRecord")


class ConstraintConfig(db.Model):
    __tablename__ = "constraint_config"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    term_id = db.Column(db.Integer, db.ForeignKey("term.id"), nullable=False)
    ctype = db.Column(db.String(20), nullable=False)                # global_hard/admin_soft
    key = db.Column(db.String(40), nullable=False)                  # 约束类型标识（与 M4 对应）
    params = db.Column(db.String(300), nullable=False)              # 结构化参数（JSON 字符串）
    priority = db.Column(db.Integer, default=5)
    enabled = db.Column(db.Boolean, default=True)


class TeacherPreference(db.Model):
    __tablename__ = "teacher_preference"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teacher.id"), nullable=False)
    term_id = db.Column(db.Integer, db.ForeignKey("term.id"), nullable=False)
    ptype = db.Column(db.String(20), nullable=False)                # prefer/avoid/consecutive
    content = db.Column(db.String(200), nullable=False)             # 如 "周二上午"
    priority = db.Column(db.Integer, default=5)
    status = db.Column(db.String(10), default="草稿")                # 草稿/已启用/已停用
    created_by = db.Column(db.Integer)                              # 确认的管理员用户编号
    updated_at = db.Column(db.DateTime)


class AuditLog(db.Model):
    __tablename__ = "audit_log"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    operator = db.Column(db.String(50))                             # 登录名
    action = db.Column(db.String(40), nullable=False)
    target = db.Column(db.String(120))
    detail = db.Column(db.String(300))
    created_at = db.Column(db.DateTime)


class Notification(db.Model):
    __tablename__ = "notification"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("sys_user.id"), nullable=False)
    content = db.Column(db.String(300), nullable=False)
    read_flag = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime)


class PendingItem(db.Model):
    """PiAgent 待确认项：写操作经管理员确认后生效（详设 9.6）。"""
    __tablename__ = "pending_item"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kind = db.Column(db.String(20), nullable=False)                 # preference/constraint
    payload = db.Column(db.String(500), nullable=False)             # 结构化 JSON
    status = db.Column(db.String(10), default="待确认")              # 待确认/已确认/已驳回
