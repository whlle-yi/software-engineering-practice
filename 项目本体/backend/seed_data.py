# -*- coding: utf-8 -*-
"""模拟数据生成（seed_data.py）：对齐概设假定的单院系规模。

约 20 门课程、30 名教师、20 间教室、10 个班级、约 500 条开课任务；
账号：admin（管理员）、教师账号 t01..t30、学生账号 s001..（每班 20 人）。
全部为模拟数据，不使用真实师生个人信息。
"""
import random
from datetime import datetime

from flask import Flask

import config
from services.dao import tx
from models import (db, SysUser, Teacher, Student, ClassInfo, Course, Classroom,
                    Term, TeachingTask)

random.seed(2026)  # 固定种子保证可复现


def hash_password(password: str) -> str:
    from services.auth_service import hash_password
    return hash_password(password)


def run(app: Flask = None):
    if app is None:
        app = Flask(__name__)
        app.config.from_object(config)
        db.init_app(app)
    with app.app_context():
        with tx() as s:
            _seed(s)
    print("模拟数据已生成")


def _seed(s):
    if Term.query.filter_by(name="2026-2027-1").first():
        print("数据已存在，跳过")
        return
    term = Term(name="2026-2027-1", status="active")
    s.add(term)
    s.flush()

    # ---- 管理员 ----
    s.add(SysUser(login_name="admin", password_hash=hash_password("admin123"),
                  role="admin", ref_id=None))

    # ---- 教师 30 名 ----
    surnames = "王李张刘陈杨赵黄周吴徐孙马朱胡郭何高林郑"
    given = "伟芳娜敏静丽强磊军洋勇艳杰娟涛明超秀霞平刚桂华建文"
    teachers = []
    for i in range(1, 31):
        t = Teacher(tno="T%03d" % i, name=surnames[i % 10] + given[i % 20],
                    title=random.choice(["教授", "副教授", "讲师", "助教"]),
                    phone="138%08d" % random.randint(0, 99999999))
        s.add(t)
        s.flush()
        teachers.append(t)
        s.add(SysUser(login_name="t%02d" % i, password_hash=hash_password("t%02d123" % i),
                      role="teacher", ref_id=t.id))

    # ---- 教室 20 间 ----
    rooms = []
    for i in range(1, 21):
        r = Classroom(rno="J%02d%02d" % (random.randint(1, 3), i),
                      capacity=random.choice([40, 60, 80, 120, 150]),
                      rtype=random.choice(["多媒体", "多媒体", "普通"]))
        s.add(r)
        rooms.append(r)
    s.flush()

    # ---- 班级 10 个（每班 30 人，共 300 学生）----
    majors = ["计算机科学", "软件工程", "数据科学", "人工智能", "信息安全"]
    classes = []
    for i in range(1, 11):
        c = ClassInfo(name="计科%02d%02d" % (24, i), grade="2024级", size=30)
        s.add(c)
        classes.append(c)
    s.flush()
    for idx, c in enumerate(classes):
        for j in range(1, 31):
            sno = "2024%02d%03d" % (idx + 1, j)
            st = Student(sno=sno, name=random.choice(surnames) + given[random.randint(0, 19)],
                         class_id=c.id)
            s.add(st)
            s.flush()        # 取 st.id 供学生账号 ref_id 引用
            if j <= 3:  # 每班 3 个学生账号用于演示
                s.add(SysUser(login_name="s" + sno[-4:], password_hash=hash_password("s123456"),
                              role="student", ref_id=st.id))
    s.flush()

    # ---- 课程 20 门 ----
    course_names = [
        "数据结构", "操作系统", "计算机网络", "数据库原理", "软件工程",
        "编译原理", "计算机组成", "离散数学", "算法设计", "机器学习",
        "深度学习", "Web开发技术", "软件测试", "软件项目管理", "需求工程",
        "面向对象设计", "Python程序设计", "数据挖掘", "云计算导论", "信息安全导论",
    ]
    courses = []
    for i, name in enumerate(course_names, 1):
        c = Course(cno="C%02d" % i, name=name,
                   hours=random.choice([2, 3, 4]), ctype=random.choice(["必修", "必修", "选修"]))
        s.add(c)
        courses.append(c)
    s.flush()

    # ---- 开课任务：每班任务数必须 ≤ 每周时段数（5 天×4 节=20，概设硬约束模型）----
    # 必修 13 门每班全开（130）+ 选修 7 门每班随机 3 门（约 21）→ 合计约 151 条。
    task_count = 0
    required = [c for c in courses if c.ctype == "必修"]
    elective = [c for c in courses if c.ctype == "选修"]
    for c in required:
        for klass in classes:
            s.add(TeachingTask(term_id=term.id, course_id=c.id,
                               teacher_id=random.choice([t.id for t in teachers]),
                               class_id=klass.id, weeks="1-16", note=""))
            task_count += 1
    for klass in classes:
        for c in random.sample(elective, 3):
            s.add(TeachingTask(term_id=term.id, course_id=c.id,
                               teacher_id=random.choice([t.id for t in teachers]),
                               class_id=klass.id, weeks="1-16", note=""))
            task_count += 1
    print("开课任务 %d 条" % task_count)
