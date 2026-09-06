from flask import Blueprint, render_template
from flask_login import current_user, login_required

from ..extensions import db
from .service import build_dashboard


bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html", **build_dashboard(current_user.id))


@bp.route("/database-test")
def database_test():
    try:
        with db.engine.connect():
            return "Database connection successful."
    except Exception as error:
        return f"Database connection failed: {error}", 500
