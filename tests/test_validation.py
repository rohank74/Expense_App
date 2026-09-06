import unittest
from decimal import Decimal

from werkzeug.datastructures import MultiDict

from expense_app.budgets.forms import parse_budget_form
from expense_app.transactions.forms import (
    FormValidationError,
    parse_transaction_form,
)


class ValidationTests(unittest.TestCase):
    def test_transaction_amount_is_always_decimal(self):
        data = parse_transaction_form(
            MultiDict(
                {
                    "transaction_type": "expense",
                    "amount": "12.34",
                    "category_id": "1",
                    "description": "Lunch",
                    "transaction_date": "2026-09-06",
                }
            )
        )

        self.assertIsInstance(data.amount, Decimal)
        self.assertEqual(data.amount, Decimal("12.34"))

    def test_transaction_rejects_non_positive_amount(self):
        with self.assertRaisesRegex(
            FormValidationError,
            "Amount must be greater than zero",
        ):
            parse_transaction_form(
                MultiDict(
                    {
                        "transaction_type": "expense",
                        "amount": "0",
                        "category_id": "1",
                        "transaction_date": "2026-09-06",
                    }
                )
            )

    def test_budget_parser_converts_all_types(self):
        data = parse_budget_form(
            MultiDict(
                {
                    "category_id": "2",
                    "amount": "5000.50",
                    "month": "9",
                    "year": "2026",
                }
            )
        )

        self.assertEqual(data.category_id, 2)
        self.assertEqual(data.amount, Decimal("5000.50"))
        self.assertEqual(data.month, 9)
        self.assertEqual(data.year, 2026)


if __name__ == "__main__":
    unittest.main()
