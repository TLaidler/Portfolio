from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    BASE_DIR = Path(__file__).resolve().parent.parent
    INSTANCE_DIR = BASE_DIR / "instance"

    BACEN_CACHE_TTL_SECONDS = int(os.getenv("BACEN_CACHE_TTL_SECONDS", "86400"))
    BACEN_CACHE_PATH = INSTANCE_DIR / "bacen_cache.json"

    RENTALS_CACHE_TTL_HOURS = int(os.getenv("RENTALS_CACHE_TTL_HOURS", "6"))
    RENTALS_DB_PATH = INSTANCE_DIR / "rentals_cache.db"

    DEFAULT_SELIC_ANNUAL = Decimal(os.getenv("DEFAULT_SELIC_ANNUAL", "0.1075"))
    DEFAULT_IPCA_ANNUAL = Decimal(os.getenv("DEFAULT_IPCA_ANNUAL", "0.045"))
    DEFAULT_CDI_ANNUAL = Decimal(os.getenv("DEFAULT_CDI_ANNUAL", "0.1065"))

    JSON_AS_ASCII = False
    TESTING = False
    DEBUG = False


class DevConfig(Config):
    DEBUG = True


class TestConfig(Config):
    TESTING = True
    BACEN_CACHE_PATH = Config.INSTANCE_DIR / "bacen_cache.test.json"
    RENTALS_DB_PATH = ":memory:"


class ProdConfig(Config):
    DEBUG = False


CONFIG_MAP = {
    "development": DevConfig,
    "testing": TestConfig,
    "production": ProdConfig,
    "default": DevConfig,
}


def get_config(name: str | None = None) -> type[Config]:
    name = name or os.getenv("FLASK_ENV", "default")
    return CONFIG_MAP.get(name, DevConfig)
