# -*- coding: utf-8 -*-
"""M1 用户与权限管理：登录/登出（详设第 3 章）。"""
from flask import Blueprint, jsonify

from blueprints.helpers import body_json, fail, ok
from services.auth_service import login as m1_login, logout as m1_logout

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
def api_login():
    data = body_json()
    token, user = m1_login(data.get("login_name", ""), data.get("password", ""))
    if token is None:
        return fail("AUTH_FAILED", "登录名或口令错误", 401)
    return ok({"token": token, "role": user.role, "login_name": user.login_name,
               "ref_id": user.ref_id})


@bp.post("/logout")
def api_logout():
    from flask import request
    m1_logout(request.headers.get("X-Auth-Token", ""))
    return ok()
