# -*- coding: utf-8 -*-
"""Blueprint 公共助手：响应体、鉴权门、请求体解析。"""
from flask import jsonify, request

import config
from services.auth_service import login as _login, authorize as _authorize


def ok(payload=None):
    return jsonify({"code": 0, "data": payload or {}})


def fail(code, message, status=400):
    return jsonify({"code": code, "message": message}), status


def need_auth(domain, action):
    sess, err = _authorize(domain, action)
    if err == "NO_SESSION":
        return None, fail("AUTH", "未登录或会话不存在", 401)
    if err == "EXPIRED":
        return None, fail("EXPIRED", "会话已过期，请重新登录", 401)
    if err == "DENIED":
        return None, fail("DENIED", "权限不足，操作已拒绝并留痕", 403)
    return sess, None


def body_json():
    try:
        return request.get_json(force=True, silent=True) or {}
    except Exception:
        return {}


def term_id():
    from models import Term
    t = Term.query.filter_by(status="active").first()
    return t.id if t else 1


def operator_name(sess):
    return sess["login_name"]
