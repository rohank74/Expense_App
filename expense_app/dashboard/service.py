from datetime import date

from ..models import Transaction


def _month_bounds(year, month):
    month_start = date(year, month, 1)
    next_month_start = (
        date(year + 1, 1, 1)
        if month == 12
        else date(year, month + 1, 1)
    )
    return month_start, next_month_start


def _transactions_for_month(user_id, year, month):
    month_start, next_month_start = _month_bounds(year, month)
    return Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.transaction_date >= month_start,
        Transaction.transaction_date < next_month_start,
    ).all()


def build_dashboard(user_id, today=None):
    today = today or date.today()
    month_start, _ = _month_bounds(today.year, today.month)
    monthly_transactions = _transactions_for_month(user_id, today.year, today.month)

    total_income = sum(
        transaction.amount
        for transaction in monthly_transactions
        if transaction.transaction_type == "income"
    )
    total_expenses = sum(
        transaction.amount
        for transaction in monthly_transactions
        if transaction.transaction_type == "expense"
    )

    expense_totals = {}
    for transaction in monthly_transactions:
        if transaction.transaction_type != "expense":
            continue
        category_name = (
            transaction.category.name if transaction.category else "Uncategorized"
        )
        expense_totals[category_name] = (
            expense_totals.get(category_name, 0) + transaction.amount
        )
    expenses_by_category = sorted(
        expense_totals.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    monthly_chart_labels = []
    monthly_income_values = []
    monthly_expense_values = []
    for months_ago in range(5, -1, -1):
        absolute_month = today.year * 12 + today.month - 1 - months_ago
        year, zero_based_month = divmod(absolute_month, 12)
        month = zero_based_month + 1
        chart_month_start = date(year, month, 1)
        transactions = _transactions_for_month(user_id, year, month)

        monthly_chart_labels.append(chart_month_start.strftime("%b %Y"))
        monthly_income_values.append(
            float(
                sum(
                    transaction.amount
                    for transaction in transactions
                    if transaction.transaction_type == "income"
                )
            )
        )
        monthly_expense_values.append(
            float(
                sum(
                    transaction.amount
                    for transaction in transactions
                    if transaction.transaction_type == "expense"
                )
            )
        )

    recent_transactions = sorted(
        monthly_transactions,
        key=lambda transaction: (
            transaction.transaction_date,
            transaction.created_at,
        ),
        reverse=True,
    )[:5]

    return {
        "month_start": month_start,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "current_balance": total_income - total_expenses,
        "transaction_count": len(monthly_transactions),
        "expenses_by_category": expenses_by_category,
        "recent_transactions": recent_transactions,
        "expense_chart_labels": [name for name, _ in expenses_by_category],
        "expense_chart_values": [float(amount) for _, amount in expenses_by_category],
        "monthly_chart_labels": monthly_chart_labels,
        "monthly_income_values": monthly_income_values,
        "monthly_expense_values": monthly_expense_values,
    }
