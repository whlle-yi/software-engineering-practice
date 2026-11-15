# -*- coding: utf-8 -*-
"""M1 用户与权限管理（详设第 3 章）。

登录认证（加盐慢散列）、会话令牌、RBAC 授权表判定。
授权表（详设 3.6）：管理员全部资源；教师本人课表读+调课申请写；学生本人/班级课表读。
"""
import hashlib
import os
import secrets
import time

from flask import request, g

import config
from config import cfg
from services.dao import tx, audit
from models import SysUser

# 会话缓存：token -> {user_id, role, ref_id, login_name, expires}
_SESSIONS = {}

# RBAC 授权表：(资源前缀, 操作) -> 允许角色集合；未匹配一律默认拒绝
AUTH_TABLE = {
    ("auth", "*"): {"admin", "teacher", "student"},
    ("base", "*"): {"admin"},
    ("constraint", "*"): {"admin"},
    ("engine", "*"): {"admin"},
    ("adjust", "apply"): {"teacher"},
    ("adjust", "review"): {"admin"},
    ("adjust", "list"): {"admin", "teacher"},
    ("query", "schedule"): {"admin", "teacher", "student"},
    ("query", "export"): {"admin", "teacher", "student"},
    ("query", "notifications"): {"admin", "teacher", "student"},
    ("agent", "chat"): {"admin", "teacher", "student"},  # PiAgent 三角色可用，工具按角色差异化（服务层二次校验）
    ("agent", "pending"): {"admin"},
    ("agent", "confirm"): {"admin"},
    ("audit", "list"): {"admin"},
}


def hash_password(password: str, salt: str = None) -> str:
    """加盐慢散列（详设 3.6：bcrypt 类思路，用 sha256+salt 迭代模拟慢散列）。"""
    salt = salt or secrets.token_hex(16)
    digest = password
    for _ in range(cfg.HASH_COST):
        digest = hashlib.sha256((salt + digest).encode()).hexdigest()
    return salt + "$" + digest


def check_password(password: str, stored: str) -> bool:
    salt, _ = stored.split("$", 1)
    return hash_password(password, salt) == stored


def login(login_name: str, password: str):
    """认证成功返回 (token, user)，失败返回 (None, 原因码)。"""
    user = SysUser.query.filter_by(login_name=login_name).first()
    if user is None or not check_password(password, user.password_hash):
        return None, "AUTH_FAILED"          # 不区分账号与口令错误（防枚举）
    token = secrets.token_hex(24)
    _SESSIONS[token] = {
        "user_id": user.id, "role": user.role, "ref_id": user.ref_id,
        "login_name": user.login_name, "expires": time.time() + cfg.SESSION_TIMEOUT_SECONDS,
    }
    return token, user


def logout(token: str):
    _SESSIONS.pop(token, None)


def _session_from_request():
    token = request.headers.get("X-Auth-Token", "")
    sess = _SESSIONS.get(token)
    if sess is None or sess["expires"] < time.time():
        _SESSIONS.pop(token, None)
        return None, None
    return token, sess


def authorize(domain: str, action: str):
    """RBAC 判定：返回 (sess, None) 或 (None, 原因码)。原因码：NO_SESSION / EXPIRED / DENIED。"""
    token, sess = _session_from_request()
    if sess is None:
        token2, sess = None, None
        for t, s in list(_SESSIONS.items()):
            if s["expires"] < time.time():
                _SESSIONS.pop(t, None)
        return None, "NO_SESSION"
    for (res, act), roles in AUTH_TABLE.items():
        if res == domain and (act == "*" or act == action) and sess["role"] in roles:
            g.login_name = sess["login_name"]
            g.role = sess["role"]
            g.ref_id = sess["ref_id"]
            g.token = token
            return sess, None
    with tx() as s:
        audit(sess["login_name"], "deny", "%s/%s" % (domain, action), "越权拒绝并留痕")
    return None, "DENIED"
