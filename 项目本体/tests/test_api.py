# -*- coding: utf-8 -*-
"""接口冒烟测试（对照测试计划 T1/T2/T4 核心用例）：登录/鉴权/导入/约束/调课闭环/PiAgent 桩。

使用 Flask test client + SQLite 内存库（不污染 MySQL）。
"""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import config

# 必须在 import app 前切到内存库
config.SQLALCHEMY_DATABASE_URI = "sqlite://"
config.SQLALCHEMY_ENGINE_OPTIONS = {}

from app import app  # noqa: E402
from models import db  # noqa: E402
from seed_data import run as seed  # noqa: E402


def make_client():
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        seed(app)
    return app.test_client()


def login(client, name, password):
    r = client.post("/api/auth/login", json={"login_name": name, "password": password})
    assert r.status_code == 200
    return r.get_json()["data"]["token"]


def test_login_and_wrong_password():
    c = make_client()
    token = login(c, "admin", "admin123")
    assert token
    r = c.post("/api/auth/login", json={"login_name": "admin", "password": "wrong"})
    assert r.status_code == 401
    d = r.get_json()
    assert d["message"] == "登录名或口令错误"      # 防枚举：不区分账号/口令


def test_rbac_denies_teacher_on_agent():
    """教师调用 PiAgent 必须 403（PiAgent 仅面向教务管理员）。"""
    c = make_client()
    token = login(c, "t01", "t01123")
    r = c.post("/api/agent/chat", headers={"X-Auth-Token": token},
               json={"instruction": "现在有多少门课程？"})
    assert r.status_code == 403
    assert r.get_json()["code"] == "DENIED"


def test_no_session_401():
    c = make_client()
    r = c.get("/api/base/teachers")
    assert r.status_code == 401


def test_import_plan_and_report():
    """教学计划导入：合法文件成功；缺班级文件整文件回滚并逐行定位（详设 4.6）。"""
    c = make_client()
    token = login(c, "admin", "admin123")
    csv = ("课程名称,课程编号,学时,周次,星期,节次,授课班级,授课教师\n"
           "数据结构,C01,4,1-16,周一,1,计科2401,T001\n"
           "操作系统,C02,4,1-16,周二,2,计科2401,T002\n").encode("utf-8")
    r = c.post("/api/base/import-plan", headers={"X-Auth-Token": token},
               data={"file": (io.BytesIO(csv), "plan.csv"), "term": "2026-2027-1"},
               content_type="multipart/form-data")
    d = r.get_json()
    assert d["code"] == 0 and d["data"]["success"] == 2
    # 不存在的班级 → 整文件拒绝并给出行号
    bad = ("课程名称,课程编号,学时,周次,星期,节次,授课班级,授课教师\n"
           "数据挖掘,C19,2,1-16,周五,3,不存在的班级,T003\n").encode("utf-8")
    r = c.post("/api/base/import-plan", headers={"X-Auth-Token": token},
               data={"file": (io.BytesIO(bad), "bad.csv"), "term": "2026-2027-1"},
               content_type="multipart/form-data")
    d = r.get_json()
    assert d["code"] == "IMPORT_REJECTED"
    assert any("第 2 行" in e for e in d["data"]["errors"])


def test_constraint_conflict_detected():
    """矛盾约束拦截：同一时段既期望又回避（详设 5.6）。"""
    c = make_client()
    token = login(c, "admin", "admin123")
    r = c.post("/api/constraint/add", headers={"X-Auth-Token": token},
               json={"key": "prefer_day", "params": {"day": "周一"}, "priority": 3})
    assert r.get_json()["code"] == 0
    r = c.post("/api/constraint/add", headers={"X-Auth-Token": token},
               json={"key": "avoid_day", "params": {"day": "周一"}, "priority": 3})
    d = r.get_json()
    assert d["code"] == "CONSTRAINT_CONFLICT"
    assert "既期望又回避" in d["message"]


def test_adjust_flow_and_engine():
    """调课闭环：先求解 → 教师申请 → 管理员通过 → 课表更新、状态终态。"""
    c = make_client()
    admin = login(c, "admin", "admin123")
    r = c.post("/api/engine/solve", headers={"X-Auth-Token": admin})
    assert r.get_json()["code"] == 0
    # 找一条有课表记录的教师
    from models import ScheduleRecord, TeachingTask, SysUser
    with app.app_context():
        rec = ScheduleRecord.query.first()
        task = TeachingTask.query.get(rec.task_id)
        tno = task.teacher.tno
        teacher_login = "t" + tno[1:] if tno.startswith("T") else tno
        rec_id = rec.id
    ttoken = None
    for name in ("t%02d" % int(tno[1:]), teacher_login):
        rr = c.post("/api/auth/login", json={"login_name": name, "password": name + "123" if False else "t01123"})
        # 通用口令：tXX123（seed 约定 t%02d123）
        rr = c.post("/api/auth/login", json={"login_name": name, "password": name + "123"})
        if rr.status_code == 200:
            ttoken = rr.get_json()["data"]["token"]
            break
    assert ttoken, "教师账号登录失败"
    r = c.post("/api/adjust/apply", headers={"X-Auth-Token": ttoken},
               json={"record_id": rec_id, "expectation": "周五 第2节", "reason": "外出开会"})
    assert r.status_code == 200
    req_id = r.get_json()["data"]["id"]
    r = c.post("/api/adjust/review", headers={"X-Auth-Token": admin},
               json={"id": req_id, "verdict": "通过", "comment": "同意"})
    assert r.status_code == 200
    d = r.get_json()["data"]
    assert d["status"] == "通过"


def test_agent_stub_answer_and_pending():
    """PiAgent 桩：read 工具直答；write 工具生成待确认项，确认后落库。"""
    c = make_client()
    token = login(c, "admin", "admin123")
    r = c.post("/api/agent/chat", headers={"X-Auth-Token": token},
               json={"instruction": "T001 希望尽量安排在周二上午"})
    d = r.get_json()["data"]
    assert "待确认项" in d["answer"]
    pend_id = d["pendings"][0]["id"]
    r = c.post("/api/agent/confirm", headers={"X-Auth-Token": token}, json={"id": pend_id})
    assert r.get_json()["code"] == 0
    r = c.post("/api/agent/chat", headers={"X-Auth-Token": token},
               json={"instruction": "现在有多少门课程？"})
    assert "20" in r.get_json()["data"]["answer"]
