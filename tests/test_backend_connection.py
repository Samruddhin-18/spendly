import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database.db as db
from database.db import init_db, seed_db
from database.queries import (
    get_category_breakdown,
    get_recent_transactions,
    get_summary_stats,
    get_user_by_id,
)


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_spendly.db")
    monkeypatch.setattr(db, "DB_PATH", db_path)

    import database.queries as queries
    monkeypatch.setattr(queries, "get_db", db.get_db)

    init_db()
    seed_db()

    conn = db.get_db()
    user_id = conn.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()["id"]
    conn.close()

    return user_id


@pytest.fixture
def empty_user(temp_db):
    conn = db.get_db()
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("New User", "new@spendly.com", "hash"),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


# --------------------------------------------------------------------- #
# get_user_by_id
# --------------------------------------------------------------------- #

def test_get_user_by_id_valid(temp_db):
    user = get_user_by_id(temp_db)
    assert user["name"] == "Demo User"
    assert user["email"] == "demo@spendly.com"
    assert user["member_since"]


def test_get_user_by_id_missing(temp_db):
    assert get_user_by_id(999999) is None


# --------------------------------------------------------------------- #
# get_summary_stats
# --------------------------------------------------------------------- #

def test_get_summary_stats_with_expenses(temp_db):
    stats = get_summary_stats(temp_db)
    assert round(stats["total_spent"], 2) == 271.24
    assert stats["transaction_count"] == 8
    assert stats["top_category"] == "Bills"


def test_get_summary_stats_no_expenses(empty_user):
    stats = get_summary_stats(empty_user)
    assert stats == {"total_spent": 0, "transaction_count": 0, "top_category": "—"}


# --------------------------------------------------------------------- #
# get_recent_transactions
# --------------------------------------------------------------------- #

def test_get_recent_transactions_with_expenses(temp_db):
    txns = get_recent_transactions(temp_db)
    assert len(txns) == 8
    dates = [t["date"] for t in txns]
    assert dates == sorted(dates, reverse=True)
    for t in txns:
        assert set(t.keys()) == {"date", "description", "category", "amount"}


def test_get_recent_transactions_no_expenses(empty_user):
    assert get_recent_transactions(empty_user) == []


# --------------------------------------------------------------------- #
# get_category_breakdown
# --------------------------------------------------------------------- #

def test_get_category_breakdown_with_expenses(temp_db):
    breakdown = get_category_breakdown(temp_db)
    amounts = [c["amount"] for c in breakdown]
    assert amounts == sorted(amounts, reverse=True)
    assert sum(c["pct"] for c in breakdown) == 100
    for c in breakdown:
        assert isinstance(c["pct"], int)


def test_get_category_breakdown_no_expenses(empty_user):
    assert get_category_breakdown(empty_user) == []


# --------------------------------------------------------------------- #
# GET /profile route
# --------------------------------------------------------------------- #

@pytest.fixture
def client(temp_db, monkeypatch):
    import app as app_module
    monkeypatch.setattr(app_module, "init_db", lambda: None)
    monkeypatch.setattr(app_module, "seed_db", lambda: None)
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c, temp_db


def test_profile_unauthenticated_redirects(client):
    c, _ = client
    resp = c.get("/profile")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_profile_authenticated(client):
    c, user_id = client
    with c.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_name"] = "Demo User"

    resp = c.get("/profile")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)

    assert "Demo User" in body
    assert "demo@spendly.com" in body
    assert "₹" in body
    assert "271.24" in body
    assert "Bills" in body
