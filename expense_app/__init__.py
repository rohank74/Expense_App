from flask import Flask

from .commands import register_commands
from .config import Config
from .extensions import csrf, db, login_manager, migrate


def create_app(config=None):
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(Config)

    if config:
        app.config.update(config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY environment variable is not set.")

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"

    from . import models
    from .auth.routes import bp as auth_bp
    from .budgets.routes import bp as budgets_bp
    from .dashboard.routes import bp as dashboard_bp
    from .transactions.routes import bp as transactions_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    register_commands(app)

    return app
