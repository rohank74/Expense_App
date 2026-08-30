# Expense App

A Flask-based personal finance application for tracking income, expenses, and monthly budgets.

## Features

- User registration, login, and logout
- Add, edit, and delete income or expense transactions
- Categorize transactions as Food, Transport, Shopping, Bills, Entertainment, or Other
- Dashboard with financial totals and recent activity
- Filter and review transaction history
- Export transactions to CSV
- Create, edit, and delete monthly category budgets
- Track spending progress and identify exceeded budgets

## Tech stack

- Python and Flask
- Flask-Login for authentication
- Flask-SQLAlchemy and SQLite for data storage
- Jinja templates and Bootstrap for the interface

## Run locally

1. Clone the repository and enter the project directory:

   ```bash
   git clone https://github.com/rohank74/Expense_App.git
   cd Expense_App
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   On Windows, activate it with:

   ```powershell
   .venv\Scripts\activate
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the application:

   ```bash
   python app.py
   ```

5. Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

The application creates and updates its SQLite database in `instance/expense_manager.db`.

## Project structure

```text
Expense_App/
├── app.py                 # Flask application, routes, and database models
├── requirements.txt       # Python dependencies
├── instance/
│   └── expense_manager.db # Local SQLite database
└── templates/             # Jinja HTML templates
```

## Development note

The current configuration runs Flask in debug mode and uses a development secret key. Change these settings before deploying the application to production.
