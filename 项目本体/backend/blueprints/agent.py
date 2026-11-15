# -*- coding: utf-8 -*-
"""M7 PiAgent 智能体：对话、待确认项、确认闭环（详设第 9 章）。仅教务管理员（SRS 2.3(7)）。"""
import json

from flask import Blueprint, request

import config
from flask import current_app
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
    answer, pendings = m7.handle(data.get("instruction", ""), operator=sess["login_name"])
    return ok({"answer": answer,
               "mode": "llm" if current_app.config["LLM_API_KEY"] else "stub",
               "pendings": [{"id": p.id, "kind": p.kind, "payload": json.loads(p.payload)}
                            for p in pendings]})


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
