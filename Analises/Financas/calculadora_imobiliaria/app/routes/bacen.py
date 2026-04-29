from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from app.services.bacen_client import BacenClient

bp = Blueprint("bacen", __name__, url_prefix="/api/bacen")


def _client() -> BacenClient:
    return BacenClient(
        cache_path=current_app.config["BACEN_CACHE_PATH"],
        cache_ttl=current_app.config["BACEN_CACHE_TTL_SECONDS"],
        defaults={
            "selic": current_app.config["DEFAULT_SELIC_ANNUAL"],
            "ipca": current_app.config["DEFAULT_IPCA_ANNUAL"],
            "cdi": current_app.config["DEFAULT_CDI_ANNUAL"],
        },
    )


@bp.get("/selic")
def selic():
    rate, is_stale, fetched_at = _client().get_latest_selic_annual()
    return jsonify(value=str(rate), is_stale=is_stale, fetched_at=fetched_at)


@bp.get("/ipca")
def ipca():
    rate, is_stale, fetched_at = _client().get_latest_ipca_12m()
    return jsonify(value=str(rate), is_stale=is_stale, fetched_at=fetched_at)


@bp.get("/cdi")
def cdi():
    rate, is_stale, fetched_at = _client().get_latest_cdi_annual()
    return jsonify(value=str(rate), is_stale=is_stale, fetched_at=fetched_at)
