from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .forms import FormValidationError, parse_budget_form
from .service import (
    CategoryNotFoundError,
    DuplicateBudgetError,
    calculate_budget_progress,
    create_budget as create_budget_record,
    delete_budget as delete_budget_record,
    get_user_budget,
    list_categories,
    list_user_budgets,
    update_budget as update_budget_record,
)


bp = Blueprint("budgets", __name__)


def _render_budget_page(edit_budget=None):
    budgets = list_user_budgets(current_user.id)
    return render_template(
        "budget.html",
        budgets=calculate_budget_progress(current_user.id, budgets),
        categories=list_categories(),
        edit_budget=edit_budget,
        current_year=date.today().year,
    )


@bp.route("/budgets", methods=["GET", "POST"])
@login_required
def budgets():
    if request.method == "POST":
        try:
            data = parse_budget_form(request.form)
            create_budget_record(current_user.id, data)
        except FormValidationError as error:
            flash(str(error), "danger")
            return _render_budget_page()
        except CategoryNotFoundError:
            flash("Please select a valid category.", "danger")
            return _render_budget_page()
        except DuplicateBudgetError:
            flash("A budget already exists for this category and month.", "danger")
            return redirect(url_for("budgets.budgets"))

        flash("Budget created successfully.", "success")
        return redirect(url_for("budgets.budgets"))

    return _render_budget_page()


@bp.route("/budgets/edit/<int:budget_id>", methods=["GET", "POST"])
@login_required
def edit_budget(budget_id):
    budget = get_user_budget(budget_id, current_user.id)
    if budget is None:
        flash("Budget not found.", "danger")
        return redirect(url_for("budgets.budgets"))

    if request.method == "POST":
        try:
            data = parse_budget_form(request.form)
            update_budget_record(budget, data)
        except FormValidationError as error:
            flash(str(error), "danger")
            return _render_budget_page(edit_budget=budget)
        except CategoryNotFoundError:
            flash("Please select a valid category.", "danger")
            return _render_budget_page(edit_budget=budget)
        except DuplicateBudgetError:
            flash("A budget already exists for this category and month.", "danger")
            return redirect(url_for("budgets.edit_budget", budget_id=budget.id))

        flash("Budget updated successfully.", "success")
        return redirect(url_for("budgets.budgets"))

    return _render_budget_page(edit_budget=budget)


@bp.route("/budgets/delete/<int:budget_id>", methods=["POST"])
@login_required
def delete_budget(budget_id):
    budget = get_user_budget(budget_id, current_user.id)
    if budget is None:
        flash("Budget not found.", "danger")
    else:
        delete_budget_record(budget)
        flash("Budget deleted successfully.", "success")
    return redirect(url_for("budgets.budgets"))
