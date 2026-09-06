from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Budget, Category, Transaction


class BudgetNotFoundError(ValueError):
    pass


class CategoryNotFoundError(ValueError):
    pass


class DuplicateBudgetError(ValueError):
    pass


def list_categories():
    return Category.query.order_by(Category.name).all()


def list_user_budgets(user_id):
    return Budget.query.filter_by(user_id=user_id).order_by(
        Budget.year.desc(),
        Budget.month.desc(),
        Budget.category_id.asc(),
    ).all()


def get_user_budget(budget_id, user_id):
    return Budget.query.filter_by(id=budget_id, user_id=user_id).first()


def calculate_budget_progress(user_id, budgets):
    progress_items = []
    for budget in budgets:
        month_start = date(budget.year, budget.month, 1)
        next_month_start = (
            date(budget.year + 1, 1, 1)
            if budget.month == 12
            else date(budget.year, budget.month + 1, 1)
        )
        amount_spent = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(
            Transaction.user_id == user_id,
            Transaction.category_id == budget.category_id,
            Transaction.transaction_type == "expense",
            Transaction.transaction_date >= month_start,
            Transaction.transaction_date < next_month_start,
        ).scalar()

        amount_spent = Decimal(str(amount_spent))
        budget_amount = Decimal(str(budget.amount))
        remaining_amount = budget_amount - amount_spent
        percentage_used = (
            amount_spent / budget_amount * Decimal("100")
            if budget_amount > 0
            else Decimal("0")
        )
        progress_items.append(
            {
                "budget": budget,
                "budget_amount": budget_amount,
                "amount_spent": amount_spent,
                "remaining_amount": remaining_amount,
                "percentage_used": float(percentage_used),
                "progress_percentage": min(max(float(percentage_used), 0), 100),
                "exceeded": amount_spent > budget_amount,
            }
        )
    return progress_items


def _validate_category(category_id):
    if db.session.get(Category, category_id) is None:
        raise CategoryNotFoundError


def _find_duplicate(user_id, data, excluded_budget_id=None):
    query = Budget.query.filter(
        Budget.user_id == user_id,
        Budget.category_id == data.category_id,
        Budget.month == data.month,
        Budget.year == data.year,
    )
    if excluded_budget_id is not None:
        query = query.filter(Budget.id != excluded_budget_id)
    return query.first()


def create_budget(user_id, data):
    _validate_category(data.category_id)
    if _find_duplicate(user_id, data) is not None:
        raise DuplicateBudgetError

    budget = Budget(
        user_id=user_id,
        category_id=data.category_id,
        amount=data.amount,
        month=data.month,
        year=data.year,
    )
    db.session.add(budget)
    _commit_budget_change()
    return budget


def update_budget(budget, data):
    _validate_category(data.category_id)
    if _find_duplicate(budget.user_id, data, budget.id) is not None:
        raise DuplicateBudgetError

    budget.category_id = data.category_id
    budget.amount = data.amount
    budget.month = data.month
    budget.year = data.year
    _commit_budget_change()
    return budget


def _commit_budget_change():
    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise DuplicateBudgetError from error


def delete_budget(budget):
    db.session.delete(budget)
    db.session.commit()
