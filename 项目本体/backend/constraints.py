# -*- coding: utf-8 -*-
"""M3 排课约束配置（详设第 5 章）：三级约束的 CRUD、矛盾检测、启停、生效集合。

约束五元组（类型 key，作用对象，参数，优先级，状态），key 与 M4 建模对应：
  teacher_conflict / room_conflict / class_conflict / capacity   —— 全局硬约束
  prefer_day / avoid_day / max_daily                             —— 管理员软约束
"""
import json
from datetime import datetime

from dao import tx, audit
from models import db, ConstraintConfig, TeacherPreference

# 硬约束类型集合（M4 支持的全局硬约束）
HARD_KEYS = ["teacher_conflict", "room_conflict", "class_conflict", "capacity"]
# 软约束类型集合（M4 支持的软约束）
SOFT_KEYS = ["prefer_day", "avoid_day", "max_daily"]
# 教师偏好类型
PREF_TYPES = ["prefer", "avoid", "consecutive"]


def validate(key, params_json, existing_list):
    """合法性校验：key 必须在支持集合内；同类同对象参数矛盾检测（详设 5.6）。"""
    try:
        params = json.loads(params_json)
    except json.JSONDecodeError:
        return "参数不是合法 JSON"
    if key in HARD_KEYS:
        return None            # 全局硬约束每类至多一条，由路由层保证
    if key not in SOFT_KEYS and key not in PREF_TYPES:
        return "不支持的约束类型：%s" % key
    # 同类同对象矛盾检测：avoid 与 prefer 指向同一天
    if key in ("prefer_day", "avoid_day"):
        target_day = params.get("day")
        opposite = "avoid_day" if key == "prefer_day" else "prefer_day"
        for e in existing_list:
            if e.key == opposite and e.enabled:
                try:
                    ep = json.loads(e.params)
                except json.JSONDecodeError:
                    continue
                if ep.get("day") == target_day:
                    return "与既有约束冲突：同一时段既期望又回避（冲突条目 #%d）" % e.id
    return None


def add_constraint(term_id, key, params, priority, operator=""):
    existing = ConstraintConfig.query.filter_by(term_id=term_id).all()
    err = validate(key, params, existing)
    if err:
        return None, err
    with tx() as s:
        c = ConstraintConfig(term_id=term_id, ctype="global_hard" if key in HARD_KEYS else "admin_soft",
                             key=key, params=params, priority=priority, enabled=True)
        s.add(c)
        s.flush()
        audit(operator, "constraint_add", "constraint_config#%d" % c.id, params)
        return c, None


def update_status(cid, enabled, operator=""):
    c = ConstraintConfig.query.get(cid)
    if c is None:
        return "条目不存在"
    with tx() as s:
        c.enabled = bool(enabled)
        audit(operator, "constraint_status", "constraint_config#%d" % cid,
              "启用" if enabled else "停用")
    return None


def get_active_constraints(term_id):
    """生效集合：学期号 + 已启用（M4 求解前读取，详设 5.6）。"""
    rows = ConstraintConfig.query.filter_by(term_id=term_id, enabled=True).all()
    prefs = TeacherPreference.query.filter_by(term_id=term_id, status="已启用").all()
    return rows, prefs


def save_preference(teacher_id, term_id, ptype, content, priority, operator_id=0, operator=""):
    """教师偏好保存（M7 确认后调用；直接录入也走这里）。状态=草稿。"""
    if ptype not in PREF_TYPES:
        return None, "不支持的偏好类型：%s" % ptype
    with tx() as s:
        p = TeacherPreference(teacher_id=teacher_id, term_id=term_id, ptype=ptype,
                              content=content, priority=priority, status="草稿",
                              created_by=operator_id, updated_at=datetime.now())
        s.add(p)
        s.flush()
        audit(operator, "preference_save", "teacher_preference#%d" % p.id,
              "教师 %d %s %s" % (teacher_id, ptype, content))
        return p, None


def set_preference_status(pid, status, operator=""):
    """偏好状态机：草稿→已启用→已停用（详设 5.6）。"""
    if status not in ("草稿", "已启用", "已停用"):
        return "非法状态：%s" % status
    p = TeacherPreference.query.get(pid)
    if p is None:
        return "记录不存在"
    with tx() as s:
        p.status = status
        p.updated_at = datetime.now()
        audit(operator, "preference_status", "teacher_preference#%d" % pid, status)
    return None
