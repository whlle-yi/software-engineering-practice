# -*- coding: utf-8 -*-
"""应用工厂（企业级惯例）：按环境装配配置、扩展与各业务域 Blueprint。

路由按业务域拆分在 blueprints/（对应概要设计 M1~M8），业务逻辑在 services/。
"""
import os

from flask import Flask

import config as config_module
from extensions import db


def create_app(config_name=None):
    """config_name: None（默认，取环境变量）/ "testing"。"""
    app = Flask(__name__, static_folder=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "static"),
        static_url_path="/static")
    if config_name == "testing":
        from config import TestingConfig
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(config_module.Config)
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = config_module.engine_options_for(
        app.config["SQLALCHEMY_DATABASE_URI"])
    db.init_app(app)

    from blueprints import register_all
    register_all(app)

    @app.get("/")
    def index():
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "frontend", "index.html"), encoding="utf-8") as f:
            return f.read()

    return app


def _current_term_id():
    from models import Term
    t = Term.query.filter_by(status="active").first()
    return t.id if t else 1


app = create_app()


def _body_json():
    from flask import request
    try:
        return request.get_json(force=True, silent=True) or {}
    except Exception:
        return {}


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="127.0.0.1", port=5000, debug=False)
