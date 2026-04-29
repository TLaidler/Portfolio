from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request
from pydantic import ValidationError

from app.schemas.simulation import SimulationRequest, ScheduleResponse
from app.services.amortization import build_schedule

bp = Blueprint("simulation", __name__, url_prefix="/api/simulate")


def _wants_json() -> bool:
    if request.args.get("format") == "json":
        return True
    accept = request.accept_mimetypes
    return accept.best == "application/json" and accept[accept.best] >= accept["text/html"]


@bp.post("")
def simulate():
    payload = request.get_json(silent=True) if request.is_json else request.form.to_dict()
    try:
        req = SimulationRequest.model_validate(payload or {})
    except ValidationError as exc:
        errors = [{"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]} for e in exc.errors()]
        return jsonify(errors=errors), 422

    schedule = build_schedule(
        property_value=req.property_value,
        down_payment=req.down_payment,
        annual_rate=req.annual_rate,
        term_months=req.effective_term_months,
        system=req.system,
        rate_convention=req.rate_convention,
    )
    response = ScheduleResponse.from_schedule(schedule, monthly_income=req.monthly_income)

    if _wants_json() or request.args.get("format") == "json":
        return jsonify(response.model_dump(mode="json"))
    return render_template("partials/simulador_resultado.html", result=response)
