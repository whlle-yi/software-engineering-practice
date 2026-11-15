# -*- coding: utf-8 -*-
"""pytest 共享 fixtures：分环境应用（SQLite 内存）、测试客户端、登录令牌。

对应《测试计划》2.3.2 条件：驱动程序 + M8 内存数据库桩。
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

import pytest  # noqa: E402

from config import TestingConfig  # noqa: E402


@pytest.fixture()
def app():
    from app import create_app
    from models import db
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        from seed_data import run as seed
        seed(app)
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin_token(client):
    r = client.post("/api/auth/login", json={"login_name": "admin", "password": "admin123"})
    assert r.status_code == 200
    return r.get_json()["data"]["token"]


@pytest.fixture()
def teacher_token(client):
    """教师 t01（seed 约定 t%02d123）。"""
    r = client.post("/api/auth/login", json={"login_name": "t01", "password": "t01123"})
    assert r.status_code == 200
    return r.get_json()["data"]["token"]
