# -*- coding: utf-8 -*-
"""注册全部业务域 Blueprint（对应概要设计 M1~M8）。"""
from blueprints.agent import bp as agent_bp
from blueprints.adjust import bp as adjust_bp
from blueprints.audit import bp as audit_bp
from blueprints.auth import bp as auth_bp
from blueprints.base import bp as base_bp
from blueprints.constraint import bp as constraint_bp
from blueprints.engine_bp import bp as engine_bp
from blueprints.query_bp import bp as query_bp


def register_all(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(base_bp)
    app.register_blueprint(constraint_bp)
    app.register_blueprint(engine_bp)
    app.register_blueprint(adjust_bp)
    app.register_blueprint(query_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(audit_bp)
