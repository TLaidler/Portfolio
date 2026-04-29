from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from app.config import Config, get_config

load_dotenv()


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(
        __name__,
        instance_relative_config=False,
        template_folder="templates",
        static_folder="static",
    )

    config_class = get_config(config_name)
    app.config.from_object(config_class)

    Path(Config.INSTANCE_DIR).mkdir(parents=True, exist_ok=True)

    from app.utils.formatters import register_filters
    register_filters(app)

    from app.routes import register_blueprints
    register_blueprints(app)

    return app
