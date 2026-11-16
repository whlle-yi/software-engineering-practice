# -*- coding: utf-8 -*-
"""M7 PiAgent 智能体：对话（三角色，工具按角色差异化）、待确认项、确认闭环（详设第 9 章）。"""
import json

import requests
from flask import Blueprint, current_app, request

import config
from blueprints.helpers import body_json, fail, need_auth, ok
from services import agent as m7
from models import PendingItem

bp = Blueprint("agent", __name__, url_prefix="/api/agent")


@bp.post("/chat")
def api_agent_chat():
    sess, err = need_auth("agent", "chat")
    if err:
        return err
    data = body_json()
    # 优先委托 pi-bridge（开源 pi agent harness；桥不可达/异常时回退内置桩路径）
    bridge_url = current_app.config.get("PI_BRIDGE_URL", "")
    if bridge_url:
        try:
            r = requests.post(bridge_url.rstrip("/") + "/chat",
                              json={"instruction": data.get("instruction", ""), "role": sess["role"]},
                              headers={"X-Bridge-Token": current_app.config.get("PI_BRIDGE_TOKEN", "")},
                              timeout=90)
            d = r.json()
            if d.get("code") == 0:
                pendings = []
                for p in (d["data"].get("pendings") or []):
                    meta = p.get("pending") if isinstance(p, dict) and "pending" in p else p
                    if not (isinstance(meta, dict) and "id" in meta):
                        continue
                    item = PendingItem.query.get(meta["id"])
                    if item:
                        pendings.append({"id": item.id, "kind": item.kind,
                                         "payload": json.loads(item.payload)})
                return ok({"answer": d["data"]["answer"], "mode": "pi", "pendings": pendings})
        except (requests.RequestException, ValueError):
            pass  # 桥不可达 → 回退桩路径（核心功能不受影响）
    answer, pendings = m7.handle(data.get("instruction", ""), operator=sess["login_name"],
                                 role=sess["role"], ref_id=sess.get("ref_id"))
    return ok({"answer": answer,
               "mode": "llm" if current_app.config["LLM_API_KEY"] else "stub",
               "pendings": [{"id": p.id, "kind": p.kind, "payload": json.loads(p.payload)}
                            for p in pendings]})


@bp.post("/bridge-tool")
def api_agent_bridge_tool():
    """pi-bridge 回调：以服务令牌执行白名单工具（复用角色白名单/待确认项/审计安全壳）。"""
    token = request.headers.get("X-Bridge-Token", "")
    expected = current_app.config.get("PI_BRIDGE_TOKEN", "")
    if not expected or token != expected:
        return fail("DENIED", "桥令牌无效", 403)
    data = body_json()
    try:
        answer, pending = m7.execute_tool(data.get("name", ""), data.get("args", {}) or {},
                                          operator="pi-bridge", role="admin")
    except m7.AgentError as e:
        return fail("TOOL_FAILED", str(e))
    return ok({"answer": answer,
               "pending": ({"id": pending.id, "kind": pending.kind} if pending else None)})


@bp.get("/pending")
def api_agent_pending():
    _, err = need_auth("agent", "pending")
    if err:
        return err
    rows = PendingItem.query.filter_by(status="待确认").all()
    return ok([{"id": p.id, "kind": p.kind, "payload": json.loads(p.payload)} for p in rows])


@bp.post("/confirm")
def api_agent_confirm():
    sess, err = need_auth("agent", "confirm")
    if err:
        return err
    data = body_json()
    result, err2 = m7.confirm(int(data.get("id", 0)), operator=sess["login_name"])
    if err2:
        return fail("CONFIRM_FAILED", err2)
    return ok({"result": result})
