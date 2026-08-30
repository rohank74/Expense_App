# Personal Expense & Budget Manager

個人の収入・支出・予算を管理するためのWebアプリケーションです。

ユーザーは自分のアカウントを作成し、収入や支出を登録・管理できます。

---

## 概要

このアプリでは、以下のことができます。

- ユーザー登録
- ログイン・ログアウト
- 収入の登録
- 支出の登録
- 取引の編集
- 取引の削除
- 取引のカテゴリ管理
- 月ごとの予算管理
- 収入・支出の確認
- グラフによるデータ表示
- CSVファイルへのエクスポート
- REST APIによるデータアクセス

---

# 使用した技術

## Backend

- Python
- Flask
- SQLAlchemy

## Database

- SQLite

## Frontend

- HTML
- CSS
- JavaScript
- Bootstrap

## Authentication

- Flask-Login
- Werkzeug Password Hashing

## Charts

- Chart.js

## Testing

- pytest

## Version Control

- Git
- GitHub

---

# 主な機能

## 1. ユーザー登録

ユーザーは自分のアカウントを作成できます。

登録には以下の情報を使用します。

- Name
- Email
- Password

パスワードはそのままデータベースに保存しません。

安全のため、パスワードをハッシュ化して保存します。

---

## 2. ログイン・ログアウト

登録したEmailとPasswordを使用してログインできます。

ログイン後は、ユーザー専用のページを利用できます。

ログアウトすると、ログインが必要なページにはアクセスできなくなります。

---

## 3. 取引の登録

ユーザーは以下の情報を登録できます。

- Income（収入）
- Expense（支出）
- Amount（金額）
- Description（説明）
- Date（日付）
- Category（カテゴリ）

例えば、

```text
Type: Expense
Amount: ¥1,200
Category: Food
Description: Lunch
Date: 2026-08-30
```

のようなデータを登録できます。

---

# 4. 取引の表示

登録した取引を一覧で確認できます。

表示される情報：

- Date
- Type
- Description
- Amount
- Category

新しい取引から順番に表示されます。

---

# 5. 取引の編集

登録した自分の取引を編集できます。

例えば、

```text
¥1,000
```

を

```text
¥1,200
```

に変更できます。

---

# 6. 取引の削除

不要になった取引を削除できます。

削除する前に確認メッセージが表示されます。

---

# 7. カテゴリ

取引にはカテゴリを設定できます。

最初に用意されているカテゴリは以下です。

- Food
- Transport
- Shopping
- Bills
- Entertainment
- Other

例えば、

```text
Food
 ├── Lunch
 ├── Dinner
 └── Restaurant
```

のように、支出を分かりやすく管理できます。

---

# 8. 月ごとの予算

ユーザーは月ごとの予算を設定できます。

例えば、

```text
August Budget

Budget: ¥100,000
Spent:  ¥72,000
Remaining: ¥28,000
```

のように、予算と実際の支出を比較できます。

---

# 9. Dashboard

Dashboardでは、ユーザーの金融情報を確認できます。

例えば、

```text
Total Income
Total Expenses
Balance
```

などを確認できます。

基本的な残高は、

```text
Balance = Income - Expenses
```

で計算します。

---

# 10. グラフ

Chart.jsを使用して、データをグラフで表示します。

グラフを使うことで、

- 収入
- 支出
- カテゴリごとの支出
- 予算の使用状況

などを分かりやすく確認できます。

---

# 11. CSV Export

取引データをCSVファイルとして保存できます。

CSVファイルはExcelなどでも開くことができます。

---

# 12. REST API

登録されている取引データにREST APIからアクセスできるようにします。

APIを使用することで、Web画面以外のアプリケーションからもデータを利用できます。

---

# セキュリティ

このアプリでは、ユーザーのデータを他のユーザーから守ることを重要視しています。

## Password

パスワードは平文で保存しません。

例えば、

```text
Password:
mypassword123
```

をそのままデータベースに保存することはありません。

代わりに、

```text
Password
   ↓
Hash
   ↓
Database
```

という形で保存します。

---

## Authentication

Authenticationは、

> 「このユーザーは誰ですか？」

を確認する仕組みです。

このアプリではFlask-Loginを使用します。

---

## Authorization

Authorizationは、

> 「このユーザーは、このデータを操作してもいいですか？」

を確認する仕組みです。

例えば、

```text
User 1
 ├── Transaction 1
 ├── Transaction 2
 └── Transaction 3

User 2
 ├── Transaction 4
 └── Transaction 5
```

User 1はUser 2のTransactionを編集・削除できません。

---

# データベース

SQLiteを使用しています。

SQLiteは、別のデータベースサーバーを起動する必要がない、シンプルなデータベースです。

データベースはプロジェクト内に保存されます。

```text
instance/
└── expense_manager.db
```

---

# プロジェクト構成

```text
Expense-app/
│
├── app.py
├── requirements.txt
├── README.md
│
├── instance/
│   └── expense_manager.db
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── login.html
│   ├── register.html
│   ├── add_transaction.html
│   ├── edit_transaction.html
│   ├── transactions.html
│   └── ...
│
├── static/
│   └── css/
│       └── style.css
│
├── tests/
│   └── ...
│
└── venv/
```

---

# 環境構築

## 1. Pythonを確認

```bash
python3 --version
```

---

## 2. 仮想環境を作成

```bash
python3 -m venv venv
```

---

## 3. 仮想環境を有効にする

Macの場合：

```bash
source venv/bin/activate
```

有効になると、ターミナルに、

```text
(venv)
```

と表示されます。

---

# 4. ライブラリをインストール

```bash
pip install -r requirements.txt
```

---

# アプリケーションを起動

仮想環境を有効にした状態で、

```bash
flask run
```

を実行します。

通常、以下のような表示が出ます。

```text
* Running on http://127.0.0.1:5000
```

ブラウザで以下を開きます。

```text
http://127.0.0.1:5000
```

---

# アプリケーションを停止

ターミナルで、

```text
Control + C
```

を押します。

---

# Git

Gitの状態を確認：

```bash
git status
```

ファイルを追加：

```bash
git add .
```

Commit：

```bash
git commit -m "Update Expense Manager"
```

---

# GitHub

GitHubのリポジトリを作成した後、ローカルプロジェクトと接続します。

```bash
git remote add origin <YOUR_GITHUB_REPOSITORY_URL>
```

その後、

```bash
git branch -M main
git push -u origin main
```

でGitHubにアップロードできます。

---

# テスト

pytestを使用してテストを実行します。

```bash
pytest
```

テストが成功すると、成功したテストの数が表示されます。

---

# このプロジェクトで学べること

このプロジェクトを通して、以下の技術を学ぶことができます。

- Python
- Flask
- Flask Routing
- Jinja Template
- Bootstrap
- SQLite
- SQLAlchemy
- Database Relationship
- CRUD
- User Authentication
- Authorization
- Password Hashing
- Session Management
- Form Validation
- Flash Messages
- Chart.js
- REST API
- CSV Export
- pytest
- Git
- GitHub

---

# 今後追加できる機能

今後、以下のような機能を追加することもできます。

- より高度な検索
- Transaction Filter
- Pagination
- より詳しいDashboard
- 支出カテゴリ別グラフ
- Budget Alert
- CSV Exportの改善
- REST APIの拡張
- テストの追加
- Docker対応
- Webアプリケーションの公開

---

# プロジェクトの目的

このプロジェクトは、PythonとFlaskを使用して、実際のWebアプリケーションを最初から段階的に開発することを目的としています。

単純なFlaskアプリケーションから始めて、

```text
Basic Flask App
       ↓
Web Interface
       ↓
Database
       ↓
User Management
       ↓
Authentication
       ↓
Transactions
       ↓
Categories
       ↓
Budgets
       ↓
Dashboard
       ↓
Charts
       ↓
REST API
       ↓
CSV Export
       ↓
Testing
```

という形で機能を少しずつ追加しています。

このプロジェクトは、**Python / Flask / SQLAlchemy / SQLiteを使ったWebアプリケーション開発のポートフォリオ**として使用できます。