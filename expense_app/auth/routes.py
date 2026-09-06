from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from .forms import FormValidationError, parse_login_form, parse_registration_form
from .service import DuplicateEmailError, authenticate_user, register_user


bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            data = parse_registration_form(request.form)
            register_user(data)
        except FormValidationError as error:
            flash(str(error), "danger")
            return render_template("register.html")
        except DuplicateEmailError:
            flash("An account with this email already exists.", "danger")
            return render_template("register.html")

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            data = parse_login_form(request.form)
        except FormValidationError as error:
            flash(str(error), "danger")
            return render_template("login.html")

        user = authenticate_user(data)
        if user is None:
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        login_user(user)
        return redirect(url_for("dashboard.dashboard"))

    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
