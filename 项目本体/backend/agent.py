# -*- coding: utf-8 -*-
"""M7 PiAgent 智能体（详设第 9 章）：白名单工具编排 + LLM 调用（可切换桩）+ 结构化校验。

白名单两类（详设 9.6）：
  read  —— 直调 M2/M3/M6/M4 查询服务并组织回答
  write —— 一律生成待确认项（PendingItem），经管理员确认后才由 M3/M8 落库
结构化校验（详设 9.6）：工具名必须在白名单内；参数字段完整、时段合法、教师编号存在。
30 秒超时降级提示；桩与真实 API 走同一编排与校验。
"""
import json
import time
from datetime import datetime

import requests
from flask import request

import config
from dao import tx, audit
from models import (db, PendingItem, Teacher, TeacherPreference, Course,
                    TeachingTask, ScheduleRecord, ConstraintConfig, SysUser)

# ---- 白名单工具清单（详设 9.10：函数签名与用途注释）----
WHITELIST = {
    "query_course_count": {"type": "read", "desc": "统计课程数量", "args": []},
    "query_teacher_count": {"type": "read", "desc": "统计教师数量", "args": []},
    "query_schedule_stats": {"type": "read", "desc": "按视图统计课表记录数（args: view, ref）",
                             "args": ["view", "ref"]},
    "query_teacher_schedule": {"type": "read", "desc": "查询某教师的课表（args: teacher_no）",
                               "args": ["teacher_no"]},
    "save_teacher_preference": {
        "type": "write", "desc": "保存教师排课偏好待确认项（args: teacher_no, ptype, content, priority）",
        "args": ["teacher_no", "ptype", "content", "priority"]},
    "save_constraint": {
        "type": "write", "desc": "保存排课约束待确认项（args: key, params, priority）",
        "args": ["key", "params", "priority"]},
}

TOOL_SPEC = [{"type": "function", "function": {"name": name, "description": meta["desc"],
             "parameters": {"type": "object", "properties": {a: {"type": "string"} for a in meta["args"]},
                            "required": meta["args"]}}}
             for name, meta in WHITELIST.items()]


class AgentError(Exception):
    pass


def _teacher_by_no(tno):
    return Teacher.query.filter_by(tno=str(tno).strip()).first()


def execute_tool(name, args: dict, operator=""):
    """白名单工具执行：read 直调；write 生成待确认项（详设 9.6）。返回 (可读结果, 待确认项或None)。"""
    if name not in WHITELIST:
        raise AgentError("工具不在白名单内：%s" % name)
    meta = WHITELIST[name]
    if meta["type"] == "read":
        if name == "query_course_count":
            return "当前课程数量：%d 门" % Course.query.count(), None
        if name == "query_teacher_count":
            return "当前教师数量：%d 名" % Teacher.query.count(), None
        if name == "query_schedule_stats":
            view, ref = args.get("view", "class"), args.get("ref")
            q = ScheduleRecord.query
            if view == "teacher" and ref:
                t = Teacher.query.filter_by(tno=str(ref)).first()
                q = q.join(TeachingTask).filter(TeachingTask.teacher_id == t.id) if t else q
            rows = q.count()
            return "%s视图课表记录共 %d 条" % (view, rows), None
        if name == "query_teacher_schedule":
            t = _teacher_by_no(args.get("teacher_no", ""))
            if t is None:
                raise AgentError("教师编号不存在：%s" % args.get("teacher_no"))
            rows = (ScheduleRecord.query.join(TeachingTask)
                    .filter(TeachingTask.teacher_id == t.id)
                    .order_by(ScheduleRecord.day, ScheduleRecord.period).all())
            lines = ["%s（%s）的课表：" % (t.name, t.tno)]
            for r in rows:
                lines.append("周%d 第%d节 %s @%s" % (
                    r.day, r.period,
                    r.task.course.name if r.task.course else "", r.room.rno if r.room else ""))
            return "\n".join(lines) or "该教师暂无课表", None
    if meta["type"] == "write":
        if name == "save_teacher_preference":
            t = _teacher_by_no(args.get("teacher_no", ""))
            if t is None:
                raise AgentError("教师编号不存在：%s" % args.get("teacher_no"))
            ptype = args.get("ptype", "prefer")
            if ptype not in ("prefer", "avoid", "consecutive"):
                raise AgentError("偏好类型非法：%s" % ptype)
            content = str(args.get("content", "")).strip()
            if not content:
                raise AgentError("偏好内容缺失")
            payload = {"teacher_id": t.id, "ptype": ptype, "content": content,
                       "priority": int(args.get("priority", 5)), "desc": "教师 %s（%s）：%s" % (t.name, t.tno, content)}
            item = _add_pending("preference", payload, operator)
            return "已生成偏好待确认项 #%d（教师 %s：%s）——请在确认页操作后生效" % (item.id, t.name, content), item
        if name == "save_constraint":
            key = args.get("key", "")
            if key not in ("prefer_day", "avoid_day", "max_daily"):
                raise AgentError("约束类型非法或不在白名单：%s" % key)
            params = args.get("params", "{}")
            try:
                json.loads(params)
            except json.JSONDecodeError:
                raise AgentError("约束参数不是合法 JSON")
            payload = {"key": key, "params": params, "priority": int(args.get("priority", 5)),
                       "desc": "约束 %s：%s" % (key, params)}
            item = _add_pending("constraint", payload, operator)
            return "已生成约束待确认项 #%d——请在确认页操作后生效" % item.id, item
    raise AgentError("工具执行失败：%s" % name)


def _add_pending(kind, payload, operator=""):
    with tx() as s:
        item = PendingItem(kind=kind, payload=json.dumps(payload, ensure_ascii=False), status="待确认")
        s.add(item)
        s.flush()
        audit(operator, "agent_pending", "pending_item#%d" % item.id,
              payload.get("desc", "")[:120])
        return item


def confirm(pending_id, operator=""):
    """管理员确认待确认项 → 真正落库（详设 9.2 写操作闭环）。"""
    item = PendingItem.query.get(pending_id)
    if item is None or item.status != "待确认":
        return None, "待确认项不存在或已处理"
    payload = json.loads(item.payload)
    import constraints as m3
    if item.kind == "preference":
        p, err = m3.save_preference(payload["teacher_id"], _current_term_id(),
                                    payload["ptype"], payload["content"],
                                    payload["priority"], operator_id=0, operator=operator)
        if err:
            return None, err
        result = "偏好已保存为草稿（#%d），启用后参与排课" % p.id
    else:
        c, err = m3.add_constraint(_current_term_id(), payload["key"], payload["params"],
                                   payload["priority"], operator)
        if err:
            return None, err
        result = "约束已保存并启用（#%d）" % c.id
    with tx() as s:
        item.status = "已确认"
        audit(operator, "agent_confirm", "pending_item#%d" % pending_id, result)
    return result, None


def _current_term_id():
    from models import Term
    t = Term.query.filter_by(status="active").first()
    return t.id if t else 1


def _structured_check(tool_name, args):
    """结构化校验（详设 9.6）：工具在白名单内 + 必填参数完整。"""
    if tool_name not in WHITELIST:
        return "工具名不在白名单：%s" % tool_name
    for arg in WHITELIST[tool_name]["args"]:
        if arg not in args or args[arg] in (None, ""):
            return "参数缺失：%s" % arg
    return None


def _llm_call(instruction):
    """调用外部大模型 API（OpenAI 兼容 + tools），30 秒超时（详设 9.3）。"""
    resp = requests.post(
        config.LLM_BASE_URL.rstrip("/") + "/chat/completions",
        headers={"Authorization": "Bearer " + config.LLM_API_KEY},
        json={"model": config.LLM_MODEL, "messages": [
            {"role": "system", "content": "你是高校排课系统的智能助手 PiAgent，只能通过提供的工具操作排课业务；"
                                          "涉及写操作时必须调用对应工具生成待确认项。"},
            {"role": "user", "content": instruction}],
            "tools": TOOL_SPEC, "temperature": 0.2},
        timeout=config.LLM_TIMEOUT_SECONDS)
    resp.raise_for_status()
    data = resp.json()
    msg = data["choices"][0]["message"]
    if msg.get("tool_calls"):
        call = msg["tool_calls"][0]
        return call["function"]["name"], json.loads(call["function"]["arguments"] or "{}")
    return None, {"_answer": msg.get("content", "")}


def _stub_call(instruction):
    """桩模式（无 key 时）：按关键词路由到白名单工具，走同一编排与校验。"""
    low = instruction.lower()
    if "多少" in instruction and ("课程" in instruction):
        return "query_course_count", {}
    if "多少" in instruction and ("教师" in instruction or "老师" in instruction):
        return "query_teacher_count", {}
    if "课表" in instruction and ("T0" in instruction or "教师编号" in instruction):
        tno = [tok for tok in instruction.replace("：", " ").replace("，", " ").split()
               if tok.upper().startswith("T0")]
        return "query_teacher_schedule", {"teacher_no": tno[0] if tno else "T001"}
    if "希望" in instruction or "偏好" in instruction or "尽量" in instruction:
        tno = [tok for tok in instruction.replace("：", " ").replace("，", " ").split()
               if tok.upper().startswith("T0")]
        day = None
        for token in ("周一", "周二", "周三", "周四", "周五"):
            if token in instruction:
                day = token
        ptype = "avoid" if ("避开" in instruction or "避免" in instruction or "不要" in instruction) else "prefer"
        content = (day or "周二") + ("上午" if "上午" in instruction else "下午" if "下午" in instruction else "")
        return "save_teacher_preference", {"teacher_no": tno[0] if tno else "T001",
                                           "ptype": ptype, "content": content, "priority": 3}
    if "约束" in instruction and ("避开" in instruction or "避免" in instruction):
        day = [token for token in ("周一", "周二", "周三", "周四", "周五") if token in instruction]
        return "save_constraint", {"key": "avoid_day", "params": json.dumps({"day": day[0] if day else "周五"}),
                                   "priority": 4}
    if "统计" in instruction:
        return "query_schedule_stats", {"view": "class", "ref": ""}
    return None, {"_answer": "（桩模式）已收到指令，本演示桩支持：课程/教师数量查询、教师课表查询（含教师编号 T0xx）、"
                             "教师偏好描述、软约束描述、排课统计。配置 LLM_API_KEY 后可接入真实大模型。"}


def handle(instruction, operator=""):
    """M7 主入口（详设 9.7 流程）：鉴权在路由层；返回 (回答文本, 待确认项列表)。"""
    t0 = time.time()
    try:
        if config.LLM_API_KEY:
            tool_name, args = _llm_call(instruction)
        else:
            tool_name, args = _stub_call(instruction)
    except (requests.Timeout, requests.RequestException) as e:
        audit(operator, "agent_timeout", "llm_api", str(e)[:100])
        return "外部模型服务暂时不可用（%d 秒超时），PiAgent 已降级停用——排课、调课、课表查询等核心功能不受影响。" \
               "请稍后重试。" % config.LLM_TIMEOUT_SECONDS, []
    except json.JSONDecodeError:
        return "模型输出格式错误，结构化校验未通过，请重述或修正后重试。", []

    if tool_name is None:                       # 模型直接回答（无工具调用）
        return args.get("_answer", ""), []
    err = _structured_check(tool_name, args)    # 结构化校验（详设 9.6）
    if err:
        return "结构化校验未通过：%s——请重述或修正后重试。" % err, []
    try:
        answer, pending = execute_tool(tool_name, args, operator)
    except AgentError as e:
        return "结构化校验未通过：%s——请重述或修正后重试。" % e, []
    audit(operator, "agent_tool", tool_name, instruction[:80])
    return answer, [pending] if pending else []
