from __future__ import annotations

from flask import Blueprint, current_app, jsonify, render_template, request

from app.services.scrapers.aggregator import RentalAggregator
from app.utils.errors import ScrapeError

bp = Blueprint("rentals", __name__, url_prefix="/api/rentals")


@bp.get("/search")
def search():
    city = request.args.get("city", "Rio de Janeiro").strip()
    neighborhood = request.args.get("neighborhood") or None

    aggregator = RentalAggregator(
        db_path=current_app.config["RENTALS_DB_PATH"],
        ttl_hours=current_app.config["RENTALS_CACHE_TTL_HOURS"],
    )

    try:
        result = aggregator.search(city=city, neighborhood=neighborhood)
    except ScrapeError as exc:
        if request.args.get("format") == "json":
            return jsonify(error=str(exc), available=False), 503
        return render_template("partials/mercado_resultado.html", result=None, error=str(exc)), 503

    if request.args.get("format") == "json":
        return jsonify(result.to_dict())
    return render_template("partials/mercado_resultado.html", result=result, error=None)
