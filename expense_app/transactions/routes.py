from flask import Blueprint, Response, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .forms import FormValidationError, parse_transaction_filters, parse_transaction_form
from .service import (
    CategoryNotFoundError,
    create_transaction as create_transaction_record,
    delete_transaction as delete_transaction_record,
    export_user_transactions,
    get_user_transaction,
    list_categories,
    list_user_transactions,
    update_transaction as update_transaction_record,
)


bp = Blueprint("transactions", __name__)


@bp.route("/transactions")
@login_required
def transactions():
    filters = parse_transaction_filters(request.args)
    return render_template(
        "transactions.html",
        transactions=list_user_transactions(current_user.id, filters),
        categories=list_categories(),
        **filters.template_context(),
    )


@bp.route("/transactions/export")
@login_required
def export_transactions():
    return Response(
        export_user_transactions(current_user.id),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )


@bp.route("/transactions/add", methods=["GET", "POST"])
@login_required
def add_transaction():
    categories = list_categories()
    if request.method == "POST":
        try:
            data = parse_transaction_form(request.form)
            create_transaction_record(current_user.id, data)
        except FormValidationError as error:
            flash(str(error), "danger")
            return render_template("add_transaction.html", categories=categories)
        except CategoryNotFoundError:
            flash("Please select a valid category.", "danger")
            return render_template("add_transaction.html", categories=categories)

        flash("Transaction added successfully.", "success")
        return redirect(url_for("transactions.add_transaction"))

    return render_template("add_transaction.html", categories=categories)


@bp.route("/transactions/edit/<int:transaction_id>", methods=["GET", "POST"])
@login_required
def edit_transaction(transaction_id):
    transaction = get_user_transaction(transaction_id, current_user.id)
    if transaction is None:
        flash("Transaction not found.", "danger")
        return redirect(url_for("transactions.transactions"))

    categories = list_categories()
    if request.method == "POST":
        try:
            data = parse_transaction_form(request.form)
            update_transaction_record(transaction, data)
        except FormValidationError as error:
            flash(str(error), "danger")
            return render_template(
                "edit_transaction.html",
                transaction=transaction,
                categories=categories,
            )
        except CategoryNotFoundError:
            flash("Please select a valid category.", "danger")
            return render_template(
                "edit_transaction.html",
                transaction=transaction,
                categories=categories,
            )

        flash("Transaction updated successfully.", "success")
        return redirect(url_for("transactions.transactions"))

    return render_template(
        "edit_transaction.html",
        transaction=transaction,
        categories=categories,
    )


@bp.route("/transactions/delete/<int:transaction_id>", methods=["POST"])
@login_required
def delete_transaction(transaction_id):
    transaction = get_user_transaction(transaction_id, current_user.id)
    if transaction is None:
        flash("Transaction not found.", "danger")
    else:
        delete_transaction_record(transaction)
        flash("Transaction deleted successfully.", "success")
    return redirect(url_for("transactions.transactions"))
