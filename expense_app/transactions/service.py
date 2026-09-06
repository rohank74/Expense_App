import csv
import io

from ..extensions import db
from ..models import Category, Transaction


class CategoryNotFoundError(ValueError):
    pass


def list_categories():
    return Category.query.order_by(Category.name).all()


def get_user_transaction(transaction_id, user_id):
    return Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()


def list_user_transactions(user_id, filters):
    query = Transaction.query.filter(Transaction.user_id == user_id)

    if filters.category_id is not None:
        query = query.filter(Transaction.category_id == filters.category_id)
    if filters.transaction_type:
        query = query.filter(Transaction.transaction_type == filters.transaction_type)
    if filters.start_date is not None:
        query = query.filter(Transaction.transaction_date >= filters.start_date)
    if filters.end_date is not None:
        query = query.filter(Transaction.transaction_date <= filters.end_date)
    if filters.search:
        query = query.filter(Transaction.description.ilike(f"%{filters.search}%"))

    ordering = {
        "date_asc": (Transaction.transaction_date.asc(), Transaction.created_at.asc()),
        "amount_desc": (Transaction.amount.desc(), Transaction.transaction_date.desc()),
        "amount_asc": (Transaction.amount.asc(), Transaction.transaction_date.desc()),
        "date_desc": (Transaction.transaction_date.desc(), Transaction.created_at.desc()),
    }
    return query.order_by(*ordering[filters.sort_by]).all()


def create_transaction(user_id, data):
    category = db.session.get(Category, data.category_id)
    if category is None:
        raise CategoryNotFoundError

    transaction = Transaction(
        user_id=user_id,
        category_id=category.id,
        amount=data.amount,
        transaction_type=data.transaction_type,
        description=data.description,
        transaction_date=data.transaction_date,
    )
    db.session.add(transaction)
    db.session.commit()
    return transaction


def update_transaction(transaction, data):
    category = db.session.get(Category, data.category_id)
    if category is None:
        raise CategoryNotFoundError

    transaction.category_id = category.id
    transaction.amount = data.amount
    transaction.transaction_type = data.transaction_type
    transaction.description = data.description
    transaction.transaction_date = data.transaction_date
    db.session.commit()
    return transaction


def delete_transaction(transaction):
    db.session.delete(transaction)
    db.session.commit()


def export_user_transactions(user_id):
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(
        Transaction.transaction_date.desc(),
        Transaction.created_at.desc(),
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Type", "Category", "Description", "Amount"])
    for transaction in transactions:
        writer.writerow(
            [
                transaction.transaction_date.isoformat(),
                transaction.transaction_type,
                transaction.category.name if transaction.category else "Uncategorized",
                transaction.description or "",
                transaction.amount,
            ]
        )
    return output.getvalue()
