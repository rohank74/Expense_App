import unittest
from decimal import Decimal

from expense_app import create_app
from expense_app.commands import seed_categories
from expense_app.extensions import db
from expense_app.models import Budget, Category, Transaction, User


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-only-secret",
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "WTF_CSRF_ENABLED": False,
            }
        )
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        seed_categories()

        self.user = User(
            name="Test User",
            email="test@example.com",
            password_hash="",
        )
        self.user.set_password("test-password")
        db.session.add(self.user)
        db.session.commit()

        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.user.id)
            session["_fresh"] = True

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()

    def test_existing_pages_and_methods_are_preserved(self):
        expected_statuses = {
            "/": 200,
            "/database-test": 200,
            "/transactions": 200,
            "/transactions/export": 200,
            "/transactions/add": 200,
            "/budgets": 200,
            "/logout": 405,
        }

        for path, expected_status in expected_statuses.items():
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, expected_status)

    def test_transaction_create_and_edit_use_decimal(self):
        food = Category.query.filter_by(name="Food").one()
        response = self.client.post(
            "/transactions/add",
            data={
                "transaction_type": "expense",
                "amount": "12.34",
                "category_id": str(food.id),
                "description": "Lunch",
                "transaction_date": "2026-09-06",
            },
        )
        self.assertEqual(response.status_code, 302)

        transaction = Transaction.query.one()
        self.assertEqual(transaction.amount, Decimal("12.34"))

        response = self.client.post(
            f"/transactions/edit/{transaction.id}",
            data={
                "transaction_type": "expense",
                "amount": "15.67",
                "category_id": str(food.id),
                "description": "Updated lunch",
                "transaction_date": "2026-09-06",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(db.session.get(Transaction, transaction.id).amount, Decimal("15.67"))

    def test_budget_creation_uses_shared_validation_and_service(self):
        food = Category.query.filter_by(name="Food").one()
        response = self.client.post(
            "/budgets",
            data={
                "category_id": str(food.id),
                "amount": "5000.50",
                "month": "9",
                "year": "2026",
            },
        )

        self.assertEqual(response.status_code, 302)
        budget = Budget.query.one()
        self.assertEqual(budget.amount, Decimal("5000.50"))


class CsrfTests(unittest.TestCase):
    def test_post_without_csrf_token_is_rejected(self):
        app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-only-secret",
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "WTF_CSRF_ENABLED": True,
            }
        )

        response = app.test_client().post(
            "/login",
            data={"email": "test@example.com", "password": "test"},
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
