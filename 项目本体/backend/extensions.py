# -*- coding: utf-8 -*-
"""Flask 扩展集中初始化（企业级惯例：避免 models/dao 各自实例化造成循环导入）。"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
