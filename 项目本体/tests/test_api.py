# -*- coding: utf-8 -*-
"""接口冒烟测试（对照《测试计划》T1/T2/T4 核心用例）：登录/鉴权/导入/约束/调课闭环/PiAgent 桩。"""
import io


def test_login_and_wrong_password(client):
    token = None
    r = client.post("/api/auth/login", json={"login_name": "admin", "password": "admin123"})
    assert r.status_code == 200
    token = r.get_json()["data"]["token"]
    assert token
    r = client.post("/api/auth/login", json={"login_name": "admin", "password": "wrong"})
    assert r.status_code == 401
    assert r.get_json()["message"] == "登录名或口令错误"     # 防枚举：不区分账号/口令


def test_agent_role_differentiation(teacher_token, student_token, client):
    """角色差异化（原型阶段口径）：三角色可对话、工具按角色裁剪——
    教师提交偏好强制绑定本人、待确认项确认权仅管理员、学生只读。"""
    # 教师：提交本人偏好 → 待确认项的 teacher_id 必须是本人（T01），非参数可伪造
    r = client.post("/api/agent/chat", headers={"X-Auth-Token": teacher_token},
                    json={"instruction": "我周二上午有会，尽量别排我的课"})
    d = r.get_json()
    assert r.status_code == 200 and "待确认项" in d["data"]["answer"]
    with client.application.app_context():
        from models import Teacher, SysUser, PendingItem
        t = Teacher.query.filter_by(tno="T001").first()
        u = SysUser.query.filter_by(login_name="t01").first()
        assert u.ref_id == t.id
        item = PendingItem.query.order_by(PendingItem.id.desc()).first()
        assert item.kind == "preference"
        import json as _json
        assert _json.loads(item.payload)["teacher_id"] == t.id
    # 教师：无法使用约束工具（角色白名单拦截）
    r = client.post("/api/agent/chat", headers={"X-Auth-Token": teacher_token},
                    json={"instruction": "查我的课表"})          # 合法：查本人课表
    assert "课表" in r.get_json()["data"]["answer"]
    from services.agent import execute_tool, AgentError
    import pytest
    with client.application.app_context():
        with pytest.raises(AgentError):
            execute_tool("save_constraint", {"key": "avoid_day", "params": "{}", "priority": 4},
                         operator="t01", role="teacher")
    # 待确认项列表与确认权仅管理员
    r = client.get("/api/agent/pending", headers={"X-Auth-Token": teacher_token})
    assert r.status_code == 403
    r = client.post("/api/agent/confirm", headers={"X-Auth-Token": teacher_token}, json={"id": 1})
    assert r.status_code == 403
    # 学生：只读课表问答；统计类管理工具不可用
    r = client.post("/api/agent/chat", headers={"X-Auth-Token": student_token},
                    json={"instruction": "查课表"})
    d = r.get_json()["data"]
    assert "课表" in d["answer"] and d["pendings"] == []
    with client.application.app_context():
        with pytest.raises(AgentError):
            execute_tool("query_course_count", {}, operator="s0001", role="student")


def test_no_session_401(client):
    r = client.get("/api/base/teachers")
    assert r.status_code == 401


def test_import_plan_and_report(client, admin_token):
    """教学计划导入：合法文件成功；缺班级文件整文件回滚并逐行定位（详设 4.6）。"""
    csv = ("课程名称,课程编号,学时,周次,星期,节次,授课班级,授课教师\n"
           "数据结构,C01,4,1-16,周一,1,计科2401,T001\n"
           "操作系统,C02,4,1-16,周二,2,计科2401,T002\n").encode("utf-8")
    r = client.post("/api/base/import-plan", headers={"X-Auth-Token": admin_token},
                    data={"file": (io.BytesIO(csv), "plan.csv"), "term": "2026-2027-1"},
                    content_type="multipart/form-data")
    d = r.get_json()
    assert d["code"] == 0 and d["data"]["success"] == 2
    bad = ("课程名称,课程编号,学时,周次,星期,节次,授课班级,授课教师\n"
           "数据挖掘,C19,2,1-16,周五,3,不存在的班级,T003\n").encode("utf-8")
    r = client.post("/api/base/import-plan", headers={"X-Auth-Token": admin_token},
                    data={"file": (io.BytesIO(bad), "bad.csv"), "term": "2026-2027-1"},
                    content_type="multipart/form-data")
    d = r.get_json()
    assert d["code"] == "IMPORT_REJECTED"
    assert any("第 2 行" in e for e in d["data"]["errors"])


def test_constraint_conflict_detected(client, admin_token):
    """矛盾约束拦截：同一时段既期望又回避（详设 5.6）。"""
    r = client.post("/api/constraint/add", headers={"X-Auth-Token": admin_token},
                    json={"key": "prefer_day", "params": {"day": "周一"}, "priority": 3})
    assert r.get_json()["code"] == 0
    r = client.post("/api/constraint/add", headers={"X-Auth-Token": admin_token},
                    json={"key": "avoid_day", "params": {"day": "周一"}, "priority": 3})
    d = r.get_json()
    assert d["code"] == "CONSTRAINT_CONFLICT"
    assert "既期望又回避" in d["message"]


def test_adjust_flow_and_engine(client, admin_token):
    """调课闭环：求解 → 教师申请 → 管理员通过 → 状态终态（表 7-1 行 1~3）。"""
    r = client.post("/api/engine/solve", headers={"X-Auth-Token": admin_token})
    assert r.get_json()["code"] == 0
    from models import ScheduleRecord, TeachingTask, Teacher
    with client.application.app_context():
        rec = ScheduleRecord.query.first()
        task = TeachingTask.query.get(rec.task_id)
        tno = task.teacher.tno
        rec_id = rec.id
        tname_login = "t" + tno[1:]
    # seed 教师账号口令 tXX123：t 序号与 tno 序号一致
    seq = int(tno[1:])
    r = client.post("/api/auth/login",
                    json={"login_name": "t%02d" % seq, "password": "t%02d123" % seq})
    assert r.status_code == 200
    ttoken = r.get_json()["data"]["token"]
    r = client.post("/api/adjust/apply", headers={"X-Auth-Token": ttoken},
                    json={"record_id": rec_id, "expectation": "周五 第2节", "reason": "外出开会"})
    assert r.status_code == 200
    req_id = r.get_json()["data"]["id"]
    r = client.post("/api/adjust/review", headers={"X-Auth-Token": admin_token},
                    json={"id": req_id, "verdict": "通过", "comment": "同意"})
    assert r.status_code == 200
    assert r.get_json()["data"]["status"] == "通过"


def test_agent_stub_answer_and_pending(client, admin_token):
    """PiAgent 桩：read 工具直答；write 工具生成待确认项，确认后落库（详设 9.6）。"""
    r = client.post("/api/agent/chat", headers={"X-Auth-Token": admin_token},
                    json={"instruction": "T001 希望尽量安排在周二上午"})
    d = r.get_json()["data"]
    assert "待确认项" in d["answer"]
    pend_id = d["pendings"][0]["id"]
    r = client.post("/api/agent/confirm", headers={"X-Auth-Token": admin_token},
                    json={"id": pend_id})
    assert r.get_json()["code"] == 0
    r = client.post("/api/agent/chat", headers={"X-Auth-Token": admin_token},
                    json={"instruction": "现在有多少门课程？"})
    assert "20" in r.get_json()["data"]["answer"]
