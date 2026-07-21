"""
Tests for Step 7: Add Expense.

Derived from .claude/specs/07-add-expenses.md — NOT from reading app.py's
add_expense() view or queries.py's create_expense() implementation logic.

Covers:
- GET /expenses/add auth guard and happy path (form fields present)
- POST /expenses/add auth guard
- POST happy path: valid expense created, redirect to /profile, DB row matches
- Validation: negative/zero amount, invalid category, future date all
  re-render the form with an error and do not insert a row
- Empty description succeeds and stores without a description
"""

import os
import sys
from datetime import date, timedelta

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database.db as db
from database.db import CATEGORIES, init_db, seed_db


# --------------------------------------------------------------------- #
# Fixtures (mirrors tests/test_backend_connection.py conventions)
# --------------------------------------------------------------------- #

@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_spendly.db")
    monkeypatch.setattr(db, "DB_PATH", db_path)

    import database.queries as queries
    monkeypatch.setattr(queries, "get_db", db.get_db)

    init_db()
    seed_db()

    conn = db.get_db()
    user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
    ).fetchone()["id"]
    conn.close()

    return user_id


@pytest.fixture
def client(temp_db, monkeypatch):
    import app as app_module
    monkeypatch.setattr(app_module, "init_db", lambda: None)
    monkeypatch.setattr(app_module, "seed_db", lambda: None)
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c, temp_db


@pytest.fixture
def auth_client(client):
    """Logged-in client bound to the seeded demo user."""
    c, user_id = client
    with c.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_name"] = "Demo User"
    return c, user_id


def count_expenses(user_id):
    conn = db.get_db()
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM expenses WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return row["n"]


def fetch_latest_expense(user_id):
    conn = db.get_db()
    row = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()
    return row


# --------------------------------------------------------------------- #
# GET /expenses/add — auth guard
# --------------------------------------------------------------------- #

def test_get_add_expense_unauthenticated_redirects_to_login(client):
    c, _ = client
    resp = c.get("/expenses/add")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


# --------------------------------------------------------------------- #
# GET /expenses/add — happy path
# --------------------------------------------------------------------- #

def test_get_add_expense_authenticated_shows_form(auth_client):
    c, _ = auth_client
    resp = c.get("/expenses/add")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)

    assert "amount" in body.lower(), "Expected an amount field in the form"
    assert "category" in body.lower(), "Expected a category field in the form"
    assert "date" in body.lower(), "Expected a date field in the form"
    assert "description" in body.lower(), "Expected a description field in the form"

    # Category select should be populated from database.db.CATEGORIES
    for category in CATEGORIES:
        assert category in body, f"Expected category '{category}' option in form"


# --------------------------------------------------------------------- #
# POST /expenses/add — auth guard
# --------------------------------------------------------------------- #

def test_post_add_expense_unauthenticated_redirects_to_login(client):
    c, _ = client
    resp = c.post(
        "/expenses/add",
        data={
            "amount": "10.00",
            "category": "Food",
            "date": date.today().isoformat(),
            "description": "Snacks",
        },
    )
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


# --------------------------------------------------------------------- #
# POST /expenses/add — happy path
# --------------------------------------------------------------------- #

def test_post_add_expense_valid_creates_row_and_redirects(auth_client):
    c, user_id = auth_client
    before_count = count_expenses(user_id)

    resp = c.post(
        "/expenses/add",
        data={
            "amount": "42.50",
            "category": "Food",
            "date": date.today().isoformat(),
            "description": "Lunch with friends",
        },
    )

    assert resp.status_code == 302, "Expected redirect on successful add"
    assert resp.headers["Location"].endswith("/profile"), (
        "Expected redirect to /profile on success"
    )

    after_count = count_expenses(user_id)
    assert after_count == before_count + 1, "Expected exactly one new expense row"

    row = fetch_latest_expense(user_id)
    assert row["user_id"] == user_id
    assert round(row["amount"], 2) == 42.50
    assert row["category"] == "Food"
    assert row["date"] == date.today().isoformat()
    assert row["description"] == "Lunch with friends"


def test_post_add_expense_amount_matches_profile_stats(auth_client):
    c, user_id = auth_client

    resp = c.post(
        "/expenses/add",
        data={
            "amount": "100.00",
            "category": "Shopping",
            "date": date.today().isoformat(),
            "description": "New shoes",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)

    # Seeded total is 271.24; new expense should push total to 371.24
    assert "371.24" in body, "Expected profile total to reflect the newly added expense"
    assert "New shoes" in body, "Expected new expense description in transaction list"


# --------------------------------------------------------------------- #
# POST /expenses/add — validation: amount
# --------------------------------------------------------------------- #

@pytest.mark.parametrize("bad_amount", ["-5", "0", "0.00", "-0.01"])
def test_post_add_expense_non_positive_amount_rejected(auth_client, bad_amount):
    c, user_id = auth_client
    before_count = count_expenses(user_id)

    resp = c.post(
        "/expenses/add",
        data={
            "amount": bad_amount,
            "category": "Food",
            "date": date.today().isoformat(),
            "description": "Should fail",
        },
    )

    assert resp.status_code == 200, "Expected form re-render (200), not a redirect"
    body = resp.get_data(as_text=True)
    assert "amount" in body.lower(), "Expected an error related to the amount field"

    assert count_expenses(user_id) == before_count, "No row should be inserted on invalid amount"


def test_post_add_expense_non_numeric_amount_rejected(auth_client):
    c, user_id = auth_client
    before_count = count_expenses(user_id)

    resp = c.post(
        "/expenses/add",
        data={
            "amount": "not-a-number",
            "category": "Food",
            "date": date.today().isoformat(),
            "description": "Should fail",
        },
    )

    assert resp.status_code == 200
    assert count_expenses(user_id) == before_count


# --------------------------------------------------------------------- #
# POST /expenses/add — validation: category
# --------------------------------------------------------------------- #

def test_post_add_expense_invalid_category_rejected(auth_client):
    c, user_id = auth_client
    before_count = count_expenses(user_id)

    resp = c.post(
        "/expenses/add",
        data={
            "amount": "20.00",
            "category": "NotARealCategory",
            "date": date.today().isoformat(),
            "description": "Should fail",
        },
    )

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "categ" in body.lower(), "Expected an error related to the category field"

    assert count_expenses(user_id) == before_count, "No row should be inserted for invalid category"


# --------------------------------------------------------------------- #
# POST /expenses/add — validation: date
# --------------------------------------------------------------------- #

def test_post_add_expense_future_date_rejected(auth_client):
    c, user_id = auth_client
    before_count = count_expenses(user_id)

    future_date = (date.today() + timedelta(days=5)).isoformat()

    resp = c.post(
        "/expenses/add",
        data={
            "amount": "20.00",
            "category": "Food",
            "date": future_date,
            "description": "Should fail",
        },
    )

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "date" in body.lower(), "Expected an error related to the date field"

    assert count_expenses(user_id) == before_count, "No row should be inserted for a future date"


def test_post_add_expense_malformed_date_rejected(auth_client):
    c, user_id = auth_client
    before_count = count_expenses(user_id)

    resp = c.post(
        "/expenses/add",
        data={
            "amount": "20.00",
            "category": "Food",
            "date": "not-a-date",
            "description": "Should fail",
        },
    )

    assert resp.status_code == 200
    assert count_expenses(user_id) == before_count


# --------------------------------------------------------------------- #
# POST /expenses/add — optional description
# --------------------------------------------------------------------- #

def test_post_add_expense_empty_description_succeeds(auth_client):
    c, user_id = auth_client
    before_count = count_expenses(user_id)

    resp = c.post(
        "/expenses/add",
        data={
            "amount": "15.75",
            "category": "Transport",
            "date": date.today().isoformat(),
            "description": "",
        },
    )

    assert resp.status_code == 302, "Empty description must not be treated as an error"
    assert resp.headers["Location"].endswith("/profile")

    after_count = count_expenses(user_id)
    assert after_count == before_count + 1

    row = fetch_latest_expense(user_id)
    assert round(row["amount"], 2) == 15.75
    assert row["category"] == "Transport"
    assert not row["description"], "Expected empty/NULL description when none provided"
