# -*- coding: utf-8 -*-
"""M8 数据访问与审计（公用程序，详设第 10 章）。

仓储语义由 SQLAlchemy 提供；本模块补齐三件事：
  1) 事务边界助手（业务层 with dao.tx() 包裹多表写操作，异常整体回滚）；
  2) 课表库写锁（schedule_record 写操作互斥串行化，详设 10.6）；
  3) 审计切面 audit(operator, action, target, detail)——写操作统一落 audit_log。
"""
import threading
from contextlib import contextmanager
from datetime import datetime

from flask import g

from models import db, AuditLog

# 课表库写锁：期初排课与调课局部重排互斥（详设 6.11 / 7.11）
schedule_write_lock = threading.Lock()


@contextmanager
def tx():
    """事务边界：正常提交，异常整体回滚后继续抛出。"""
    try:
        yield db.session
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


@contextmanager
def schedule_write_tx(operator=""):
    """课表库写操作：写锁 + 事务 + 审计三件套。"""
    with schedule_write_lock:
        try:
            yield db.session
            db.session.commit()
            audit(operator, "schedule_write", "schedule_record", "课表库写操作成功")
        except Exception:
            db.session.rollback()
            raise


def audit(operator, action, target="", detail=""):
    """审计切面：与业务写同事务调用（调用方在 tx() 内），失败随业务回滚。"""
    db.session.add(AuditLog(operator=operator or getattr(g, "login_name", ""),
                            action=action, target=target, detail=detail,
                            created_at=datetime.now()))


def audit_query(operator, time_range=None):
    """审计查询：仅经 M1 鉴权的管理员可达（路由层校验）。"""
    q = AuditLog.query.filter_by(operator=operator) if operator else AuditLog.query
    if time_range:
        start, end = time_range
        q = q.filter(AuditLog.created_at >= start, AuditLog.created_at <= end)
    return q.order_by(AuditLog.created_at.desc()).all()
