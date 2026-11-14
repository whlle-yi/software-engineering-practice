# -*- coding: utf-8 -*-
"""PiAgent 排课系统 · 原型配置。

LLM 接入可切换：config 或环境变量提供 LLM_API_KEY 时走真实大模型 API
（OpenAI 兼容格式，base_url 可指向智谱/DeepSeek/通义等），否则自动切桩模式。
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ---- 数据库 ----
# 文档口径为 MySQL 8.0；本机未安装 MySQL 时可用回退串（SQLite）跑通演示。
MYSQL_URI = ("mysql+pymysql://course:course123@127.0.0.1:3306/"
             "course_scheduling?charset=utf8mb4")
SQLITE_URI = "sqlite:///" + str(BASE_DIR / "prototype.db").replace("\\", "/")
SQLALCHEMY_DATABASE_URI = os.environ.get("PROTOTYPE_DB", MYSQL_URI)
if SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
    # SQLite 需要多线程访问时关闭同进程连接检查
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}
else:
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_size": 10, "pool_recycle": 3600}

# ---- 会话与安全 ----
SECRET_KEY = os.environ.get("PROTOTYPE_SECRET", "prototype-secret-key")
SESSION_TIMEOUT_SECONDS = 4 * 3600
HASH_COST = 12                      # 口令慢散列代价因子（详设 3.6）

# ---- PiAgent（M7）----
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
LLM_MODEL = os.environ.get("LLM_MODEL", "glm-4-flash")
LLM_TIMEOUT_SECONDS = 30            # SRS 3.2.2：单次请求 30 秒超时
LLM_FIRST_TOKEN_BUDGET = 5          # SRS 3.2.2：首字响应 5 秒（预算提示值）

# ---- 排课引擎（M4）----
ENGINE_STRATEGY = os.environ.get("ENGINE_STRATEGY", "sa")   # sa=模拟退火 ga=遗传
ENGINE_ITERATIONS = int(os.environ.get("ENGINE_ITERATIONS", "2000"))
ENGINE_NO_IMPROVE_ROUNDS = 200              # 连续无改进终止轮数
ENGINE_TIME_BUDGET_SECONDS = 240            # 求解时间预算（SRS：含检测 ≤5 分钟）

# ---- 业务参数 ----
TIMESLOTS = [(day, period) for day in range(1, 6) for period in range(1, 5)]  # 周一~周五×1~4大节
HARD_PENALTY = 10000.0                      # 硬约束罚系数（详设 6.6）
