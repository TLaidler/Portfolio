from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template

bp = Blueprint("main", __name__)


@bp.get("/")
def index() -> str:
    return render_template("index.html")


@bp.get("/simulador")
def simulador() -> str:
    return render_template("simulador.html")


@bp.get("/mercado")
def mercado() -> str:
    return render_template("mercado.html")


@bp.get("/custo-oportunidade")
def custo_oportunidade() -> str:
    return render_template("custo_oportunidade.html")


@bp.get("/api/health")
def health():
    bacen_path = Path(current_app.config["BACEN_CACHE_PATH"])
    bacen_age = None
    if bacen_path.exists():
        bacen_age = round(
            datetime.now(timezone.utc).timestamp() - bacen_path.stat().st_mtime, 1
        )
    return jsonify(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
        bacen_cache_age_seconds=bacen_age,
    )
