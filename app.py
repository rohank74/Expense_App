from datetime import datetime, date

from decimal import Decimal, InvalidOperation

import re

import csv

import io

from flask import Flask, render_template, request, redirect, url_for, flash, Response

from flask_sqlalchemy import SQLAlchemy

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy.exc import IntegrityError

from sqlalchemy import inspect, text, func


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expense_manager.db"

app.config["SECRET_KEY"] = "expense-manager-dev-secret-2026"

db = SQLAlchemy(app)


login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"


# ---------------------------------------------------------
# User model
# ---------------------------------------------------------

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100)
    )

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    transactions = db.relationship(
        "Transaction",
        back_populates="user"
    )

    def set_password(self, password):

        self.password_hash = generate_password_hash(password)

    def check_password(self, password):

        return check_password_hash(
            self.password_hash,
            password
        )


# ---------------------------------------------------------
# Category model
# ---------------------------------------------------------

class Category(db.Model):

    __tablename__ = "categories"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    transactions = db.relationship(
        "Transaction",
        back_populates="category"
    )


# ---------------------------------------------------------
# Transaction model
# ---------------------------------------------------------

class Transaction(db.Model):

    __tablename__ = "transactions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        nullable=True
    )

    amount = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    transaction_type = db.Column(
        db.String(10),
        nullable=False
    )

    description = db.Column(
        db.String(255),
        nullable=True
    )

    transaction_date = db.Column(
        db.Date,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User",
        back_populates="transactions"
    )

    category = db.relationship(
        "Category",
        back_populates="transactions"
    )


# ---------------------------------------------------------
# Budget model
# STEP 14 - Monthly budget management
# ---------------------------------------------------------

class Budget(db.Model):

    __tablename__ = "budgets"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        nullable=False
    )

    amount = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    month = db.Column(
        db.Integer,
        nullable=False
    )

    year = db.Column(
        db.Integer,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User",
        backref="budgets"
    )

    category = db.relationship(
        "Category",
        backref="budgets"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "category_id",
            "month",
            "year",
            name="uq_budget_user_category_month_year"
        ),
    )


# ---------------------------------------------------------
# Flask-Login user loader
# ---------------------------------------------------------

@login_manager.user_loader
def load_user(user_id):

    return db.session.get(
        User,
        int(user_id)
    )


# ---------------------------------------------------------
# Email validation
# ---------------------------------------------------------

def is_valid_email(email):

    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return re.match(
        email_pattern,
        email
    ) is not None


# ---------------------------------------------------------
# STEP 11 database setup
# ---------------------------------------------------------

def setup_categories():

    db.create_all()

    inspector = inspect(
        db.engine
    )

    transaction_columns = [
        column["name"]
        for column in inspector.get_columns(
            "transactions"
        )
    ]

    if "category_id" not in transaction_columns:

        with db.engine.connect() as connection:

            connection.execute(
                text(
                    "ALTER TABLE transactions "
                    "ADD COLUMN category_id INTEGER"
                )
            )

            connection.commit()

    default_categories = [
        "Food",
        "Transport",
        "Shopping",
        "Bills",
        "Entertainment",
        "Other"
    ]

    for category_name in default_categories:

        existing_category = Category.query.filter_by(
            name=category_name
        ).first()

        if existing_category is None:

            category = Category(
                name=category_name
            )

            db.session.add(category)

    db.session.commit()

    other_category = Category.query.filter_by(
        name="Other"
    ).first()

    transactions_without_category = Transaction.query.filter(
        Transaction.category_id.is_(None)
    ).all()

    for transaction in transactions_without_category:

        transaction.category_id = other_category.id

    db.session.commit()


# ---------------------------------------------------------
# Dashboard
# STEP 13 + STEP 16
# ---------------------------------------------------------

@app.route("/")
@login_required
def dashboard():

    today = date.today()

    # -----------------------------------------------------
    # Current calendar month
    # -----------------------------------------------------

    month_start = today.replace(
        day=1
    )

    if today.month == 12:

        next_month_start = date(
            today.year + 1,
            1,
            1
        )

    else:

        next_month_start = date(
            today.year,
            today.month + 1,
            1
        )


    # -----------------------------------------------------
    # Current user's transactions for current month
    # -----------------------------------------------------

    monthly_transactions = Transaction.query.filter(

        Transaction.user_id == current_user.id,

        Transaction.transaction_date >= month_start,

        Transaction.transaction_date < next_month_start

    ).all()


    # -----------------------------------------------------
    # Total income
    # -----------------------------------------------------

    total_income = sum(

        transaction.amount

        for transaction in monthly_transactions

        if transaction.transaction_type == "income"

    )


    # -----------------------------------------------------
    # Total expenses
    # -----------------------------------------------------

    total_expenses = sum(

        transaction.amount

        for transaction in monthly_transactions

        if transaction.transaction_type == "expense"

    )


    # -----------------------------------------------------
    # Current balance
    # -----------------------------------------------------

    current_balance = (

        total_income - total_expenses

    )


    # -----------------------------------------------------
    # Number of transactions
    # -----------------------------------------------------

    transaction_count = len(

        monthly_transactions

    )


    # -----------------------------------------------------
    # Expenses by category
    # -----------------------------------------------------

    expenses_by_category = {}

    for transaction in monthly_transactions:

        if transaction.transaction_type != "expense":

            continue

        category_name = (

            transaction.category.name

            if transaction.category

            else "Uncategorized"

        )

        if category_name not in expenses_by_category:

            expenses_by_category[category_name] = 0

        expenses_by_category[category_name] += (

            transaction.amount

        )


    expenses_by_category = sorted(

        expenses_by_category.items(),

        key=lambda item: item[1],

        reverse=True

    )


    # -----------------------------------------------------
    # STEP 16
    # Expense distribution chart data
    # -----------------------------------------------------

    expense_chart_labels = [

        category_name

        for category_name, amount

        in expenses_by_category

    ]

    expense_chart_values = [

        float(amount)

        for category_name, amount

        in expenses_by_category

    ]


    # -----------------------------------------------------
    # STEP 16
    # Monthly income vs expenses chart
    #
    # Last 6 calendar months
    # -----------------------------------------------------

    monthly_chart_labels = []

    monthly_income_values = []

    monthly_expense_values = []


    for months_ago in range(5, -1, -1):

        year = today.year

        month = today.month - months_ago

        while month <= 0:

            month += 12

            year -= 1


        chart_month_start = date(

            year,

            month,

            1

        )


        if month == 12:

            chart_next_month_start = date(

                year + 1,

                1,

                1

            )

        else:

            chart_next_month_start = date(

                year,

                month + 1,

                1

            )


        month_transactions = Transaction.query.filter(

            Transaction.user_id == current_user.id,

            Transaction.transaction_date >= chart_month_start,

            Transaction.transaction_date < chart_next_month_start

        ).all()


        month_income = sum(

            transaction.amount

            for transaction in month_transactions

            if transaction.transaction_type == "income"

        )


        month_expenses = sum(

            transaction.amount

            for transaction in month_transactions

            if transaction.transaction_type == "expense"

        )


        monthly_chart_labels.append(

            chart_month_start.strftime("%b %Y")

        )

        monthly_income_values.append(

            float(month_income)

        )

        monthly_expense_values.append(

            float(month_expenses)

        )


    # -----------------------------------------------------
    # Recent transactions
    # -----------------------------------------------------

    recent_transactions = sorted(

        monthly_transactions,

        key=lambda transaction: (

            transaction.transaction_date,

            transaction.created_at

        ),

        reverse=True

    )[:5]


    return render_template(

        "dashboard.html",

        month_start=month_start,

        total_income=total_income,

        total_expenses=total_expenses,

        current_balance=current_balance,

        transaction_count=transaction_count,

        expenses_by_category=expenses_by_category,

        recent_transactions=recent_transactions,

        # STEP 16 chart data

        expense_chart_labels=expense_chart_labels,

        expense_chart_values=expense_chart_values,

        monthly_chart_labels=monthly_chart_labels,

        monthly_income_values=monthly_income_values,

        monthly_expense_values=monthly_expense_values

    )


# ---------------------------------------------------------
# Database test
# ---------------------------------------------------------

@app.route("/database-test")
def database_test():

    try:

        with db.engine.connect():

            return "Database connection successful."

    except Exception as error:

        return (

            f"Database connection failed: {error}",

            500

        )


# ---------------------------------------------------------
# Registration
# ---------------------------------------------------------

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )


        if not name:

            flash(
                "Name is required.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        if not email:

            flash(
                "Email is required.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        if not password:

            flash(
                "Password is required.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        if not confirm_password:

            flash(
                "Please confirm your password.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        if not is_valid_email(email):

            flash(
                "Please enter a valid email address.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "An account with this email already exists.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        password_hash = generate_password_hash(
            password
        )

        user = User(
            name=name,
            email=email,
            password_hash=password_hash
        )


        try:

            db.session.add(user)

            db.session.commit()

        except IntegrityError:

            db.session.rollback()

            flash(
                "An account with this email already exists.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        flash(
            "Registration successful. Please log in.",
            "success"
        )

        return redirect(
            url_for("login")
        )


    return render_template(
        "register.html"
    )


# ---------------------------------------------------------
# Login
# ---------------------------------------------------------

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )


        if not email or not password:

            flash(
                "Email and password are required.",
                "danger"
            )

            return render_template(
                "login.html"
            )


        user = User.query.filter_by(
            email=email
        ).first()


        if user is None or not user.check_password(
            password
        ):

            flash(
                "Invalid email or password.",
                "danger"
            )

            return render_template(
                "login.html"
            )


        login_user(user)

        return redirect(
            url_for("dashboard")
        )


    return render_template(
        "login.html"
    )


# ---------------------------------------------------------
# Logout
# ---------------------------------------------------------

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("login")
    )


# ---------------------------------------------------------
# Display transactions
# STEP 12 - Search, filter and sort
# ---------------------------------------------------------

@app.route("/transactions")
@login_required
def transactions():

    category_id = request.args.get(
        "category_id",
        "",
        type=str
    )

    transaction_type = request.args.get(
        "transaction_type",
        "",
        type=str
    )

    start_date = request.args.get(
        "start_date",
        "",
        type=str
    )

    end_date = request.args.get(
        "end_date",
        "",
        type=str
    )

    search = request.args.get(
        "search",
        "",
        type=str
    ).strip()

    sort_by = request.args.get(
        "sort_by",
        "date_desc",
        type=str
    )


    query = Transaction.query.filter(
        Transaction.user_id == current_user.id
    )


    if category_id:

        try:

            category_id_value = int(
                category_id
            )

            query = query.filter(
                Transaction.category_id ==
                category_id_value
            )

        except ValueError:

            category_id = ""


    if transaction_type in [
        "income",
        "expense"
    ]:

        query = query.filter(
            Transaction.transaction_type ==
            transaction_type
        )

    else:

        transaction_type = ""


    if start_date:

        try:

            start_date_value = date.fromisoformat(
                start_date
            )

            query = query.filter(
                Transaction.transaction_date >=
                start_date_value
            )

        except ValueError:

            start_date = ""


    if end_date:

        try:

            end_date_value = date.fromisoformat(
                end_date
            )

            query = query.filter(
                Transaction.transaction_date <=
                end_date_value
            )

        except ValueError:

            end_date = ""


    if search:

        query = query.filter(
            Transaction.description.ilike(
                f"%{search}%"
            )
        )


    if sort_by == "date_asc":

        query = query.order_by(
            Transaction.transaction_date.asc(),
            Transaction.created_at.asc()
        )

    elif sort_by == "amount_desc":

        query = query.order_by(
            Transaction.amount.desc(),
            Transaction.transaction_date.desc()
        )

    elif sort_by == "amount_asc":

        query = query.order_by(
            Transaction.amount.asc(),
            Transaction.transaction_date.desc()
        )

    else:

        sort_by = "date_desc"

        query = query.order_by(
            Transaction.transaction_date.desc(),
            Transaction.created_at.desc()
        )


    user_transactions = query.all()


    categories = Category.query.order_by(
        Category.name
    ).all()


    return render_template(

        "transactions.html",

        transactions=user_transactions,

        categories=categories,

        category_id=category_id,

        transaction_type=transaction_type,

        start_date=start_date,

        end_date=end_date,

        search=search,

        sort_by=sort_by

    )


# ---------------------------------------------------------
# Export transactions to CSV
# STEP 17
# ---------------------------------------------------------

@app.route("/transactions/export")
@login_required
def export_transactions():

    # Get ONLY the logged-in user's transactions.

    user_transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Transaction.transaction_date.desc(),
        Transaction.created_at.desc()
    ).all()


    # Create an in-memory text file.

    output = io.StringIO()


    # Create CSV writer.

    writer = csv.writer(output)


    # Write CSV header.

    writer.writerow([
        "Date",
        "Type",
        "Category",
        "Description",
        "Amount"
    ])


    # Write the user's transactions.

    for transaction in user_transactions:

        category_name = (

            transaction.category.name

            if transaction.category

            else "Uncategorized"

        )

        writer.writerow([
            transaction.transaction_date.isoformat(),
            transaction.transaction_type,
            category_name,
            transaction.description or "",
            transaction.amount
        ])


    # Move back to the beginning of the generated CSV.

    output.seek(0)


    # Return the CSV as a downloadable file.

    return Response(

        output.getvalue(),

        mimetype="text/csv",

        headers={

            "Content-Disposition":
            "attachment; filename=transactions.csv"

        }

    )


# ---------------------------------------------------------
# Add transaction
# ---------------------------------------------------------

@app.route(
    "/transactions/add",
    methods=["GET", "POST"]
)
@login_required
def add_transaction():

    categories = Category.query.order_by(
        Category.name
    ).all()


    if request.method == "POST":

        transaction_type = request.form.get(
            "transaction_type",
            ""
        ).strip()

        amount_text = request.form.get(
            "amount",
            ""
        ).strip()

        category_id_text = request.form.get(
            "category_id",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        transaction_date_text = request.form.get(
            "transaction_date",
            ""
        ).strip()


        if transaction_type not in [
            "income",
            "expense"
        ]:

            flash(
                "Transaction type must be income or expense.",
                "danger"
            )

            return render_template(
                "add_transaction.html",
                categories=categories
            )


        try:

            amount = Decimal(
                amount_text
            )

        except (
            InvalidOperation,
            ValueError
        ):

            flash(
                "Please enter a valid amount.",
                "danger"
            )

            return render_template(
                "add_transaction.html",
                categories=categories
            )


        if amount <= 0:

            flash(
                "Amount must be greater than zero.",
                "danger"
            )

            return render_template(
                "add_transaction.html",
                categories=categories
            )


        try:

            category_id = int(
                category_id_text
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Please select a category.",
                "danger"
            )

            return render_template(
                "add_transaction.html",
                categories=categories
            )


        category = db.session.get(
            Category,
            category_id
        )


        if category is None:

            flash(
                "Please select a valid category.",
                "danger"
            )

            return render_template(
                "add_transaction.html",
                categories=categories
            )


        try:

            transaction_date = date.fromisoformat(
                transaction_date_text
            )

        except ValueError:

            flash(
                "Please enter a valid date.",
                "danger"
            )

            return render_template(
                "add_transaction.html",
                categories=categories
            )


        transaction = Transaction(

            user_id=current_user.id,

            category_id=category.id,

            amount=amount,

            transaction_type=transaction_type,

            description=description if description else None,

            transaction_date=transaction_date

        )


        db.session.add(
            transaction
        )

        db.session.commit()


        flash(
            "Transaction added successfully.",
            "success"
        )

        return redirect(
            url_for("add_transaction")
        )


    return render_template(
        "add_transaction.html",
        categories=categories
    )


# ---------------------------------------------------------
# Edit transaction
# ---------------------------------------------------------

@app.route(
    "/transactions/edit/<int:transaction_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_transaction(transaction_id):

    transaction = Transaction.query.filter_by(

        id=transaction_id,

        user_id=current_user.id

    ).first()


    if transaction is None:

        flash(
            "Transaction not found.",
            "danger"
        )

        return redirect(
            url_for("transactions")
        )


    categories = Category.query.order_by(
        Category.name
    ).all()


    if request.method == "POST":

        transaction_type = request.form.get(
            "transaction_type",
            ""
        ).strip()

        amount_text = request.form.get(
            "amount",
            ""
        ).strip()

        category_id_text = request.form.get(
            "category_id",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        transaction_date_text = request.form.get(
            "transaction_date",
            ""
        ).strip()


        if transaction_type not in [
            "income",
            "expense"
        ]:

            flash(
                "Transaction type must be income or expense.",
                "danger"
            )

            return render_template(
                "edit_transaction.html",
                transaction=transaction,
                categories=categories
            )


        try:

            amount = float(
                amount_text
            )

            if amount <= 0:

                raise ValueError

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Amount must be greater than zero.",
                "danger"
            )

            return render_template(
                "edit_transaction.html",
                transaction=transaction,
                categories=categories
            )


        try:

            category_id = int(
                category_id_text
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Please select a category.",
                "danger"
            )

            return render_template(
                "edit_transaction.html",
                transaction=transaction,
                categories=categories
            )


        category = db.session.get(
            Category,
            category_id
        )


        if category is None:

            flash(
                "Please select a valid category.",
                "danger"
            )

            return render_template(
                "edit_transaction.html",
                transaction=transaction,
                categories=categories
            )


        try:

            transaction_date = datetime.strptime(
                transaction_date_text,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            flash(
                "Please enter a valid date.",
                "danger"
            )

            return render_template(
                "edit_transaction.html",
                transaction=transaction,
                categories=categories
            )


        transaction.transaction_type = transaction_type

        transaction.amount = amount

        transaction.category_id = category.id

        transaction.description = (
            description or None
        )

        transaction.transaction_date = (
            transaction_date
        )


        db.session.commit()


        flash(
            "Transaction updated successfully.",
            "success"
        )

        return redirect(
            url_for("transactions")
        )


    return render_template(
        "edit_transaction.html",
        transaction=transaction,
        categories=categories
    )


# ---------------------------------------------------------
# Delete transaction
# ---------------------------------------------------------

@app.route(
    "/transactions/delete/<int:transaction_id>",
    methods=["POST"]
)
@login_required
def delete_transaction(transaction_id):

    transaction = Transaction.query.filter_by(

        id=transaction_id,

        user_id=current_user.id

    ).first()


    if transaction is None:

        flash(
            "Transaction not found.",
            "danger"
        )

        return redirect(
            url_for("transactions")
        )


    db.session.delete(
        transaction
    )

    db.session.commit()


    flash(
        "Transaction deleted successfully.",
        "success"
    )

    return redirect(
        url_for("transactions")
    )


# ---------------------------------------------------------
# Budget management
# STEP 14 + STEP 15
# ---------------------------------------------------------

def get_budget_progress(user_budgets):

    budget_progress = []


    for budget in user_budgets:

        if budget.month == 12:

            next_month_start = date(

                budget.year + 1,

                1,

                1

            )

        else:

            next_month_start = date(

                budget.year,

                budget.month + 1,

                1

            )


        month_start = date(

            budget.year,

            budget.month,

            1

        )


        amount_spent = db.session.query(

            func.coalesce(

                func.sum(Transaction.amount),

                0

            )

        ).filter(

            Transaction.user_id == current_user.id,

            Transaction.category_id == budget.category_id,

            Transaction.transaction_type == "expense",

            Transaction.transaction_date >= month_start,

            Transaction.transaction_date < next_month_start

        ).scalar()


        amount_spent = Decimal(

            str(amount_spent)

        )


        budget_amount = Decimal(

            str(budget.amount)

        )


        remaining_amount = (

            budget_amount - amount_spent

        )


        percentage_used = (

            amount_spent /

            budget_amount *

            Decimal("100")

        )


        progress_percentage = min(

            max(

                float(percentage_used),

                0

            ),

            100

        )


        budget_progress.append({

            "budget": budget,

            "budget_amount": budget_amount,

            "amount_spent": amount_spent,

            "remaining_amount": remaining_amount,

            "percentage_used": float(percentage_used),

            "progress_percentage": progress_percentage,

            "exceeded": amount_spent > budget_amount

        })


    return budget_progress


@app.route(
    "/budgets",
    methods=["GET", "POST"]
)
@login_required
def budgets():

    categories = Category.query.order_by(
        Category.name
    ).all()


    if request.method == "POST":

        category_id_text = request.form.get(
            "category_id",
            ""
        ).strip()

        amount_text = request.form.get(
            "amount",
            ""
        ).strip()

        month_text = request.form.get(
            "month",
            ""
        ).strip()

        year_text = request.form.get(
            "year",
            ""
        ).strip()


        try:

            category_id = int(
                category_id_text
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Please select a valid category.",
                "danger"
            )

            return render_template(
                "budget.html",
                budgets=[],
                categories=categories,
                current_year=date.today().year
            )


        category = db.session.get(
            Category,
            category_id
        )


        if category is None:

            flash(
                "Please select a valid category.",
                "danger"
            )

            return render_template(
                "budget.html",
                budgets=[],
                categories=categories,
                current_year=date.today().year
            )


        try:

            amount = Decimal(
                amount_text
            )

        except (
            InvalidOperation,
            ValueError
        ):

            flash(
                "Please enter a valid budget amount.",
                "danger"
            )

            return render_template(
                "budget.html",
                budgets=[],
                categories=categories,
                current_year=date.today().year
            )


        if amount <= 0:

            flash(
                "Budget amount must be greater than zero.",
                "danger"
            )

            return render_template(
                "budget.html",
                budgets=[],
                categories=categories,
                current_year=date.today().year
            )


        try:

            month = int(
                month_text
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Please select a valid month.",
                "danger"
            )

            return render_template(
                "budget.html",
                budgets=[],
                categories=categories,
                current_year=date.today().year
            )


        if month < 1 or month > 12:

            flash(
                "Month must be between 1 and 12.",
                "danger"
            )

            return render_template(
                "budget.html",
                budgets=[],
                categories=categories,
                current_year=date.today().year
            )


        try:

            year = int(
                year_text
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Please enter a valid year.",
                "danger"
            )

            return render_template(
                "budget.html",
                budgets=[],
                categories=categories,
                current_year=date.today().year
            )


        if year < 1:

            flash(
                "Year must be valid.",
                "danger"
            )

            return render_template(
                "budget.html",
                budgets=[],
                categories=categories,
                current_year=date.today().year
            )


        existing_budget = Budget.query.filter_by(

            user_id=current_user.id,

            category_id=category_id,

            month=month,

            year=year

        ).first()


        if existing_budget:

            flash(
                "A budget already exists for this category and month.",
                "danger"
            )

            return redirect(
                url_for("budgets")
            )


        budget = Budget(

            user_id=current_user.id,

            category_id=category_id,

            amount=amount,

            month=month,

            year=year

        )


        db.session.add(
            budget
        )


        try:

            db.session.commit()

        except IntegrityError:

            db.session.rollback()

            flash(
                "A budget already exists for this category and month.",
                "danger"
            )

            return redirect(
                url_for("budgets")
            )


        flash(
            "Budget created successfully.",
            "success"
        )

        return redirect(
            url_for("budgets")
        )


    user_budgets = Budget.query.filter_by(

        user_id=current_user.id

    ).order_by(

        Budget.year.desc(),

        Budget.month.desc(),

        Budget.category_id.asc()

    ).all()


    budget_progress = get_budget_progress(

        user_budgets

    )


    return render_template(

        "budget.html",

        budgets=budget_progress,

        categories=categories,

        current_year=date.today().year

    )


# ---------------------------------------------------------
# Edit budget
# ---------------------------------------------------------

@app.route(
    "/budgets/edit/<int:budget_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_budget(budget_id):

    budget = Budget.query.filter_by(

        id=budget_id,

        user_id=current_user.id

    ).first()


    if budget is None:

        flash(
            "Budget not found.",
            "danger"
        )

        return redirect(
            url_for("budgets")
        )


    categories = Category.query.order_by(
        Category.name
    ).all()


    user_budgets = Budget.query.filter_by(

        user_id=current_user.id

    ).order_by(

        Budget.year.desc(),

        Budget.month.desc(),

        Budget.category_id.asc()

    ).all()


    budget_progress = get_budget_progress(

        user_budgets

    )


    if request.method == "POST":

        category_id_text = request.form.get(
            "category_id",
            ""
        ).strip()

        amount_text = request.form.get(
            "amount",
            ""
        ).strip()

        month_text = request.form.get(
            "month",
            ""
        ).strip()

        year_text = request.form.get(
            "year",
            ""
        ).strip()


        try:

            category_id = int(
                category_id_text
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Please select a valid category.",
                "danger"
            )

            return render_template(
                "budget.html",
                budgets=budget_progress,
                categories=categories,
                edit_budget=budget,
                current_year=date.today().year
            )


        category = db.session.get(
            Category,
            category_id
        )


        if category is None:

            flash(
                "Please select a valid category.",
                "danger"
            )

            return render_template(
                "budget.html",
                budgets=budget_progress,
                categories=categories,
                edit_budget=budget,
                current_year=date.today().year
            )


        try:

            amount = Decimal(
                amount_text
            )

        except (
            InvalidOperation,
            ValueError
        ):

            flash(
                "Please enter a valid budget amount.",
                "danger"
            )

            return render_template(
                "budget.html",
                budgets=budget_progress,
                categories=categories,
                edit_budget=budget,
                current_year=date.today().year
            )


        if amount <= 0:

            flash(
                "Budget amount must be greater than zero.",
                "danger"
            )

            return render_template(
                "budget.html",
                budgets=budget_progress,
                categories=categories,
                edit_budget=budget,
                current_year=date.today().year
            )


        try:

            month = int(
                month_text
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Please select a valid month.",
                "danger"
            )

            return render_template(
                "budget.html",
                budgets=budget_progress,
                categories=categories,
                edit_budget=budget,
                current_year=date.today().year
            )


        if month < 1 or month > 12:

            flash(
                "Month must be between 1 and 12.",
                "danger"
            )

            return render_template(
                "budget.html",
                budgets=budget_progress,
                categories=categories,
                edit_budget=budget,
                current_year=date.today().year
            )


        try:

            year = int(
                year_text
            )

        except (
            ValueError,
            TypeError
        ):

            flash(
                "Please enter a valid year.",
                "danger"
            )

            return render_template(
                "budget.html",
                budgets=budget_progress,
                categories=categories,
                edit_budget=budget,
                current_year=date.today().year
            )


        if year < 1:

            flash(
                "Year must be valid.",
                "danger"
            )

            return render_template(
                "budget.html",
                budgets=budget_progress,
                categories=categories,
                edit_budget=budget,
                current_year=date.today().year
            )


        duplicate_budget = Budget.query.filter(

            Budget.user_id == current_user.id,

            Budget.category_id == category_id,

            Budget.month == month,

            Budget.year == year,

            Budget.id != budget.id

        ).first()


        if duplicate_budget:

            flash(
                "A budget already exists for this category and month.",
                "danger"
            )

            return redirect(
                url_for(
                    "edit_budget",
                    budget_id=budget.id
                )
            )


        budget.category_id = category_id

        budget.amount = amount

        budget.month = month

        budget.year = year


        try:

            db.session.commit()

        except IntegrityError:

            db.session.rollback()

            flash(
                "A budget already exists for this category and month.",
                "danger"
            )

            return redirect(
                url_for(
                    "edit_budget",
                    budget_id=budget.id
                )
            )


        flash(
            "Budget updated successfully.",
            "success"
        )

        return redirect(
            url_for("budgets")
        )


    return render_template(

        "budget.html",

        budgets=budget_progress,

        categories=categories,

        edit_budget=budget,

        current_year=date.today().year

    )


# ---------------------------------------------------------
# Delete budget
# ---------------------------------------------------------

@app.route(
    "/budgets/delete/<int:budget_id>",
    methods=["POST"]
)
@login_required
def delete_budget(budget_id):

    budget = Budget.query.filter_by(

        id=budget_id,

        user_id=current_user.id

    ).first()


    if budget is None:

        flash(
            "Budget not found.",
            "danger"
        )

        return redirect(
            url_for("budgets")
        )


    db.session.delete(
        budget
    )

    db.session.commit()


    flash(
        "Budget deleted successfully.",
        "success"
    )

    return redirect(
        url_for("budgets")
    )


# ---------------------------------------------------------
# Start application
# ---------------------------------------------------------

if __name__ == "__main__":

    with app.app_context():

        setup_categories()

    app.run(
        debug=True
    )