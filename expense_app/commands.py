from .extensions import db
from .models import Category


DEFAULT_CATEGORIES = (
    "Food",
    "Transport",
    "Shopping",
    "Bills",
    "Entertainment",
    "Other",
)


def seed_categories():
    for category_name in DEFAULT_CATEGORIES:
        if Category.query.filter_by(name=category_name).first() is None:
            db.session.add(Category(name=category_name))

    db.session.commit()


def register_commands(app):
    @app.cli.command("seed-categories")
    def seed_categories_command():
        seed_categories()
        print("Default categories initialized.")
