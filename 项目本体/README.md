# 项目本体 · PiAgent 赋能的高校排课系统（原型）

技术栈（原型阶段拍板，见《概要设计说明书》2.7 节）：**Flask 3 + SQLAlchemy 2 + MySQL 8.0 + Vue 3（CDN 单页）**。
对应文档模块划分：M1 用户与权限 / M2 基础数据 / M3 约束配置 / M4 排课引擎 / M5 调课闭环 / M6 查询通知 / M7 PiAgent / M8 数据访问与审计（backend/ 每模块一个文件）。

## 启动
1. 数据库：MySQL 8 已安装于 `D:\mysql-8\mysql-8.0.28-winx64`（本机）。建库脚本 `db\schema.sql`（已执行：库 course_scheduling、账号 course/course123）。未装 MySQL 的机器：`set PROTOTYPE_DB=sqlite:///prototype.db` 回退 SQLite。
2. 依赖：`pip install -r requirements.txt`（本机 pip.ini 配置了代理，需加 `--proxy ""`）。
3. 初始化与启动：
   - `cd backend && python -c "import app; from models import db; from app import app; app.app_context().__enter__(); db.create_all()"`（首次建表）
   - `python -c "import sys; sys.path.insert(0,'.'); from seed_data import run; run()"`（生成模拟数据）
   - `python app.py` → 浏览器打开 http://127.0.0.1:5000/

4. 测试：`pytest tests/ -q`（13 用例：引擎小算例/不可行报告/防御分支/接口冒烟/RBAC 越权/PiAgent 闭环）。

## 演示路径（第 14 周演示脚本雏形）
1. admin 登录 → 概览统计 → 下载教学计划模板 CSV → 导入（或用 seed 已生成的 120 条任务）→ 运行排课引擎（实测 0.3~0.4 秒，硬冲突 0，指标 ≤5 分钟）→ 课表页按班级/教师/教室查询 → 导出 CSV/Excel。
2. t01 教师登录 → 我的课表 → 发起调课申请 → admin 在调课审核通过（局部重排同事务）→ 教师与班级学生收到站内通知、课表更新。
3. admin 在 PiAgent 对话输入「T001 希望尽量安排在周二上午」→ 生成偏好待确认项 → 约束与偏好页确认生效 → 启用后参与下次排课（软约束）。
4. 越权演示：教师账号调 PiAgent 接口被 403 拒绝并留痕（审计日志页可见）。

## 账号
| 角色 | 账号 | 口令 |
| --- | --- | --- |
| 管理员 | admin | admin123 |
| 教师 | t01 ~ t30 | tXX123（如 t01123） |
| 学生 | 班级前 3 名学号尾四位（如 s0001） | s123456 |

## PiAgent 真实大模型接入（可选）
设置环境变量 `LLM_API_KEY`（国产大模型 OpenAI 兼容 key）、`LLM_BASE_URL`（默认智谱 v4）、`LLM_MODEL`（默认 glm-4-flash）后重启，PiAgent 自动从桩切到真实函数调用；未配置时为桩模式（编排与校验逻辑完全一致）。

## 目录
- `backend/`：M1–M8 每模块一个文件（app.py 为入口与路由）＋ models.py（13 表）＋ seed_data.py。
- `frontend/`：index.html（Vue 3 单页）＋ static/vue.global.prod.js（本地化，离线可用）。
- `tests/`：pytest 13 用例。`db/schema.sql`：建库脚本。
