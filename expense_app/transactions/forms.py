from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation


class FormValidationError(ValueError):
    pass


@dataclass(frozen=True)
class TransactionData:
    transaction_type: str
    amount: Decimal
    category_id: int
    description: str | None
    transaction_date: date


@dataclass(frozen=True)
class TransactionFilters:
    category_id: int | None
    category_id_text: str
    transaction_type: str
    start_date: date | None
    start_date_text: str
    end_date: date | None
    end_date_text: str
    search: str
    sort_by: str

    def template_context(self):
        return {
            "category_id": self.category_id_text,
            "transaction_type": self.transaction_type,
            "start_date": self.start_date_text,
            "end_date": self.end_date_text,
            "search": self.search,
            "sort_by": self.sort_by,
        }


def parse_transaction_form(form):
    transaction_type = form.get("transaction_type", "").strip()
    if transaction_type not in {"income", "expense"}:
        raise FormValidationError("Transaction type must be income or expense.")

    amount_text = form.get("amount", "").strip()
    try:
        amount = Decimal(amount_text)
    except (InvalidOperation, ValueError):
        raise FormValidationError("Please enter a valid amount.") from None

    if not amount.is_finite() or amount <= 0:
        raise FormValidationError("Amount must be greater than zero.")

    try:
        category_id = int(form.get("category_id", "").strip())
    except (TypeError, ValueError):
        raise FormValidationError("Please select a category.") from None

    try:
        transaction_date = date.fromisoformat(
            form.get("transaction_date", "").strip()
        )
    except ValueError:
        raise FormValidationError("Please enter a valid date.") from None

    description = form.get("description", "").strip() or None
    return TransactionData(
        transaction_type=transaction_type,
        amount=amount,
        category_id=category_id,
        description=description,
        transaction_date=transaction_date,
    )


def parse_transaction_filters(args):
    category_id_text = args.get("category_id", "", type=str)
    try:
        category_id = int(category_id_text) if category_id_text else None
    except ValueError:
        category_id = None
        category_id_text = ""

    transaction_type = args.get("transaction_type", "", type=str)
    if transaction_type not in {"income", "expense"}:
        transaction_type = ""

    start_date_text = args.get("start_date", "", type=str)
    try:
        start_date = date.fromisoformat(start_date_text) if start_date_text else None
    except ValueError:
        start_date = None
        start_date_text = ""

    end_date_text = args.get("end_date", "", type=str)
    try:
        end_date = date.fromisoformat(end_date_text) if end_date_text else None
    except ValueError:
        end_date = None
        end_date_text = ""

    sort_by = args.get("sort_by", "date_desc", type=str)
    if sort_by not in {"date_desc", "date_asc", "amount_desc", "amount_asc"}:
        sort_by = "date_desc"

    return TransactionFilters(
        category_id=category_id,
        category_id_text=category_id_text,
        transaction_type=transaction_type,
        start_date=start_date,
        start_date_text=start_date_text,
        end_date=end_date,
        end_date_text=end_date_text,
        search=args.get("search", "", type=str).strip(),
        sort_by=sort_by,
    )
