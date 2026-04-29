from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request
from pydantic import ValidationError

from app.schemas.opportunity import OpportunityRequest, OpportunityResponse
from app.services.opportunity_cost import compare_buy_vs_rent

bp = Blueprint("opportunity", __name__, url_prefix="/api/opportunity-cost")


@bp.post("")
def opportunity():
    payload = request.get_json(silent=True) if request.is_json else request.form.to_dict()
    try:
        req = OpportunityRequest.model_validate(payload or {})
    except ValidationError as exc:
        errors = [{"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]} for e in exc.errors()]
        return jsonify(errors=errors), 422

    result = compare_buy_vs_rent(req.to_domain())
    response = OpportunityResponse.from_result(result, scenario_b_mode=req.scenario_b_mode)

    if request.args.get("format") == "json":
        return jsonify(response.model_dump(mode="json"))
    return render_template("partials/custo_resultado.html", result=response)
