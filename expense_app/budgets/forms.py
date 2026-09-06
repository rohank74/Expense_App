from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


class FormValidationError(ValueError):
    pass


@dataclass(frozen=True)
class BudgetData:
    category_id: int
    amount: Decimal
    month: int
    year: int


def parse_budget_form(form):
    try:
        category_id = int(form.get("category_id", "").strip())
    except (TypeError, ValueError):
        raise FormValidationError("Please select a valid category.") from None

    try:
        amount = Decimal(form.get("amount", "").strip())
    except (InvalidOperation, ValueError):
        raise FormValidationError("Please enter a valid budget amount.") from None

    if not amount.is_finite() or amount <= 0:
        raise FormValidationError("Budget amount must be greater than zero.")

    try:
        month = int(form.get("month", "").strip())
    except (TypeError, ValueError):
        raise FormValidationError("Please select a valid month.") from None

    if month < 1 or month > 12:
        raise FormValidationError("Month must be between 1 and 12.")

    try:
        year = int(form.get("year", "").strip())
    except (TypeError, ValueError):
        raise FormValidationError("Please enter a valid year.") from None

    if year < 1:
        raise FormValidationError("Year must be valid.")

    return BudgetData(
        category_id=category_id,
        amount=amount,
        month=month,
        year=year,
    )
