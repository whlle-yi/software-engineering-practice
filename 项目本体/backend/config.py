# -*- coding: utf-8 -*-
"""配置（分环境类式，口令等敏感项一律来自环境变量，见 .env.example）。"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_DIR = Path(__file__).resolve().parent

# ---- 数据库（环境变量 PROTOTYPE_DB 优先；MySQL 8.0 为文档口径，SQLite 为演示回退）----
MYSQL_URI = (
    "mysql+pymysql://%s:%s@%s:%s/course_scheduling?charset=utf8mb4"
    % (os.environ.get("DB_USER", "course"),
       os.environ.get("DB_PASSWORD", ""),
       os.environ.get("DB_HOST", "127.0.0.1"),
       os.environ.get("DB_PORT", "3306"))
)
SQLITE_URI = "sqlite:///" + str(BASE_DIR / "prototype.db").replace("\\", "/")


class Config:
    SECRET_KEY = os.environ.get("PROTOTYPE_SECRET", "prototype-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("PROTOTYPE_DB", MYSQL_URI)
    SQLALCHEMY_ENGINE_OPTIONS = {}
    SESSION_TIMEOUT_SECONDS = 4 * 3600
    HASH_COST = 12
    LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
    LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
    LLM_MODEL = os.environ.get("LLM_MODEL", "glm-4-flash")
    LLM_TIMEOUT_SECONDS = 30
    # pi-bridge（开源 pi agent harness 桥接层，见 项目本体/pi-bridge/）
    PI_BRIDGE_URL = os.environ.get("PI_BRIDGE_URL", "http://127.0.0.1:8710")
    PI_BRIDGE_TOKEN = os.environ.get("PI_BRIDGE_TOKEN", "pi-bridge-local")
    ENGINE_STRATEGY = os.environ.get("ENGINE_STRATEGY", "sa")
    ENGINE_ITERATIONS = int(os.environ.get("ENGINE_ITERATIONS", "2000"))
    ENGINE_NO_IMPROVE_ROUNDS = 200
    ENGINE_TIME_BUDGET_SECONDS = 240
    TIMESLOTS = [(d, p) for d in range(1, 6) for p in range(1, 5)]
    HARD_PENALTY = 10000.0


class TestingConfig(Config):
    """测试环境：SQLite 内存库（conftest.py 使用）。"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}


def engine_options_for(uri):
    if uri.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_size": 10, "pool_recycle": 3600}


# 默认实例（services 层读取用；Testing 路径由 create_app 装配）
cfg = Config()
