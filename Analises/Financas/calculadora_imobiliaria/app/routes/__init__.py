from __future__ import annotations

from flask import Flask


def register_blueprints(app: Flask) -> None:
    from app.routes.main import bp as main_bp
    from app.routes.simulation import bp as simulation_bp
    from app.routes.bacen import bp as bacen_bp
    from app.routes.opportunity import bp as opportunity_bp
    from app.routes.rentals import bp as rentals_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(simulation_bp)
    app.register_blueprint(bacen_bp)
    app.register_blueprint(opportunity_bp)
    app.register_blueprint(rentals_bp)
