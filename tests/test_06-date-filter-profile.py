"""
Tests for Step 6: Date Filter for Profile Page.

Derived from .claude/specs/06-date-filter-profile.md — NOT from reading
app.py's profile() view or queries.py's filtering implementation logic.

Covers:
- get_summary_stats / get_recent_transactions / get_category_breakdown
  accepting date_from/date_to directly (DB-level)
- GET /profile query-param driven filtering (route-level)
- Presets (This Month / Last 3 Months / Last 6 Months / All Time)
- Validation: malformed dates, date_from > date_to, open-ended ranges
- Empty-range behavior
- Category breakdown percentages summing to 100
"""

import os
import sys
from datetime import date, timedelta

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database.db as db
from database.db import init_db, seed_db
from database.queries import (
    get_category_breakdown,
    get_recent_transactions,
    get_summary_stats,
)


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


def seed_dates():
    """Reconstruct the expense dates seed_db() creates, for range math."""
    today = date.today()
    days = [1, 3, 5, 7, 9, 11, 13, 15]
    return [today.replace(day=min(d, 28)) for d in days]


# --------------------------------------------------------------------- #
# DB-level: get_summary_stats with date_from/date_to
# --------------------------------------------------------------------- #

class TestGetSummaryStatsDateFilter:
    def test_no_filter_matches_unfiltered_behavior(self, temp_db):
        unfiltered = get_summary_stats(temp_db)
        filtered = get_summary_stats(temp_db, date_from=None, date_to=None)
        assert filtered == unfiltered

    def test_full_range_includes_all_expenses(self, temp_db):
        today = date.today()
        start = today.replace(day=1).isoformat()
        end = today.isoformat()
        stats = get_summary_stats(temp_db, date_from=start, date_to=end)
        assert stats["transaction_count"] == 8
        assert round(stats["total_spent"], 2) == 271.24

    def test_narrow_range_returns_subset(self, temp_db):
        today = date.today()
        d1 = today.replace(day=1).isoformat()
        d3 = today.replace(day=3).isoformat()
        stats = get_summary_stats(temp_db, date_from=d1, date_to=d3)
        # day 1 (Food 25.50) and day 3 (Transport 12.00) fall in range
        assert stats["transaction_count"] == 2
        assert round(stats["total_spent"], 2) == 37.50

    def test_empty_range_returns_zeroed_stats(self, temp_db):
        future_start = (date.today() + timedelta(days=100)).isoformat()
        future_end = (date.today() + timedelta(days=110)).isoformat()
        stats = get_summary_stats(temp_db, date_from=future_start, date_to=future_end)
        assert stats == {"total_spent": 0, "transaction_count": 0, "top_category": "—"}

    def test_no_expenses_user_with_range(self, empty_user):
        stats = get_summary_stats(empty_user, date_from="2020-01-01", date_to="2030-01-01")
        assert stats == {"total_spent": 0, "transaction_count": 0, "top_category": "—"}


# --------------------------------------------------------------------- #
# DB-level: get_recent_transactions with date_from/date_to
# --------------------------------------------------------------------- #

class TestGetRecentTransactionsDateFilter:
    def test_no_filter_matches_unfiltered_behavior(self, temp_db):
        unfiltered = get_recent_transactions(temp_db)
        filtered = get_recent_transactions(temp_db, date_from=None, date_to=None)
        assert filtered == unfiltered

    def test_narrow_range_returns_subset_ordered_desc(self, temp_db):
        today = date.today()
        d1 = today.replace(day=1).isoformat()
        d9 = today.replace(day=9).isoformat()
        txns = get_recent_transactions(temp_db, date_from=d1, date_to=d9)
        dates = [t["date"] for t in txns]
        assert len(txns) == 5  # days 1, 3, 5, 7, 9 (date_to is inclusive)
        assert dates == sorted(dates, reverse=True)

    def test_empty_range_returns_empty_list(self, temp_db):
        future_start = (date.today() + timedelta(days=100)).isoformat()
        future_end = (date.today() + timedelta(days=110)).isoformat()
        txns = get_recent_transactions(temp_db, date_from=future_start, date_to=future_end)
        assert txns == []

    def test_limit_respected_within_range(self, temp_db):
        today = date.today()
        d1 = today.replace(day=1).isoformat()
        d15 = today.replace(day=15).isoformat()
        txns = get_recent_transactions(temp_db, limit=2, date_from=d1, date_to=d15)
        assert len(txns) == 2


# --------------------------------------------------------------------- #
# DB-level: get_category_breakdown with date_from/date_to
# --------------------------------------------------------------------- #

class TestGetCategoryBreakdownDateFilter:
    def test_no_filter_matches_unfiltered_behavior(self, temp_db):
        unfiltered = get_category_breakdown(temp_db)
        filtered = get_category_breakdown(temp_db, date_from=None, date_to=None)
        assert filtered == unfiltered

    def test_percentages_sum_to_100_in_range(self, temp_db):
        today = date.today()
        d1 = today.replace(day=1).isoformat()
        d15 = today.replace(day=15).isoformat()
        breakdown = get_category_breakdown(temp_db, date_from=d1, date_to=d15)
        assert breakdown, "Expected non-empty breakdown for full seeded range"
        assert sum(c["pct"] for c in breakdown) == 100
        for c in breakdown:
            assert isinstance(c["pct"], int)

    def test_empty_range_returns_empty_list(self, temp_db):
        future_start = (date.today() + timedelta(days=100)).isoformat()
        future_end = (date.today() + timedelta(days=110)).isoformat()
        breakdown = get_category_breakdown(temp_db, date_from=future_start, date_to=future_end)
        assert breakdown == []

    def test_narrow_range_subset_categories(self, temp_db):
        today = date.today()
        d1 = today.replace(day=1).isoformat()
        d1b = today.replace(day=1).isoformat()
        breakdown = get_category_breakdown(temp_db, date_from=d1, date_to=d1b)
        assert len(breakdown) == 1
        assert breakdown[0]["name"] == "Food"
        assert breakdown[0]["pct"] == 100


# --------------------------------------------------------------------- #
# Route-level: GET /profile auth guard
# --------------------------------------------------------------------- #

def test_profile_with_date_params_unauthenticated_redirects(client):
    c, _ = client
    resp = c.get("/profile?date_from=2026-01-01&date_to=2026-01-31")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


# --------------------------------------------------------------------- #
# Route-level: no filter params => Step 5 unfiltered behavior
# --------------------------------------------------------------------- #

def test_profile_no_params_matches_unfiltered(auth_client):
    c, _ = auth_client
    resp = c.get("/profile")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "271.24" in body
    assert "Bills" in body
    assert "₹" in body


# --------------------------------------------------------------------- #
# Route-level: happy path presets and custom range
# --------------------------------------------------------------------- #

def test_profile_this_month_preset_filters_correctly(auth_client):
    c, user_id = auth_client
    today = date.today()
    start = today.replace(day=1).isoformat()
    end = today.isoformat()

    resp = c.get(f"/profile?date_from={start}&date_to={end}")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)

    expected = get_summary_stats(user_id, date_from=start, date_to=end)
    assert f"{expected['total_spent']:.2f}" in body
    assert str(expected["transaction_count"]) in body


def test_profile_last_3_months_preset_filters_correctly(auth_client):
    c, user_id = auth_client
    today = date.today()
    start = (today - timedelta(days=90)).isoformat()
    end = today.isoformat()

    resp = c.get(f"/profile?date_from={start}&date_to={end}")
    assert resp.status_code == 200
    # All seeded expenses fall within the last 90 days (seeded relative to "today")
    body = resp.get_data(as_text=True)
    assert "271.24" in body


def test_profile_last_6_months_preset_filters_correctly(auth_client):
    c, user_id = auth_client
    today = date.today()
    start = (today - timedelta(days=182)).isoformat()
    end = today.isoformat()

    resp = c.get(f"/profile?date_from={start}&date_to={end}")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "271.24" in body


def test_profile_all_time_preset_no_params_shows_everything(auth_client):
    c, _ = auth_client
    resp = c.get("/profile")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "271.24" in body


def test_profile_custom_range_filters_all_three_sections(auth_client):
    c, user_id = auth_client
    today = date.today()
    d1 = today.replace(day=1).isoformat()
    d3 = today.replace(day=3).isoformat()

    resp = c.get(f"/profile?date_from={d1}&date_to={d3}")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)

    # Stats section: 2 transactions, 37.50 total
    assert "37.50" in body
    assert "₹" in body
    # Transactions section: only Groceries and Bus pass should show
    assert "Groceries" in body
    assert "Bus pass" in body
    # Electricity bill (day 5) should be excluded
    assert "Electricity bill" not in body


# --------------------------------------------------------------------- #
# Validation: malformed dates fall back to unfiltered
# --------------------------------------------------------------------- #

def test_profile_malformed_date_from_falls_back_unfiltered(auth_client):
    c, _ = auth_client
    resp = c.get("/profile?date_from=not-a-date&date_to=2026-12-31")
    assert resp.status_code == 200, "Malformed date must not crash the app"
    body = resp.get_data(as_text=True)
    assert "271.24" in body


def test_profile_malformed_date_to_falls_back_unfiltered(auth_client):
    c, _ = auth_client
    resp = c.get("/profile?date_from=2026-01-01&date_to=garbage")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "271.24" in body


def test_profile_both_dates_malformed_falls_back_unfiltered(auth_client):
    c, _ = auth_client
    resp = c.get("/profile?date_from=xx&date_to=yy")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "271.24" in body


# --------------------------------------------------------------------- #
# Validation: date_from > date_to falls back + flash error
# --------------------------------------------------------------------- #

def test_profile_date_from_after_date_to_falls_back_and_flashes(auth_client):
    c, _ = auth_client
    today = date.today()
    later = today.isoformat()
    earlier = today.replace(day=1).isoformat()

    # date_from (later) > date_to (earlier)
    resp = c.get(f"/profile?date_from={later}&date_to={earlier}", follow_redirects=True)
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)

    assert "Start date must be before end date." in body, (
        "Expected flash error message when date_from > date_to"
    )
    # Falls back to unfiltered view
    assert "271.24" in body


# --------------------------------------------------------------------- #
# Only one of date_from/date_to supplied (open-ended range)
# --------------------------------------------------------------------- #

def test_profile_only_date_from_supplied(auth_client):
    """Per spec: a lone date_from filters as an open-ended range (>= date_from)."""
    c, user_id = auth_client
    today = date.today()
    start = today.replace(day=7).isoformat()

    resp = c.get(f"/profile?date_from={start}")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "₹" in body

    expected = get_summary_stats(user_id, date_from=start, date_to=None)
    assert f"{expected['total_spent']:.2f}" in body
    # day 5 (Bills) falls before date_from and must be excluded
    assert expected["transaction_count"] < 8


def test_profile_only_date_to_supplied(auth_client):
    """Per spec: a lone date_to filters as an open-ended range (<= date_to)."""
    c, user_id = auth_client
    today = date.today()
    end = today.replace(day=7).isoformat()

    resp = c.get(f"/profile?date_to={end}")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "₹" in body

    expected = get_summary_stats(user_id, date_from=None, date_to=end)
    assert f"{expected['total_spent']:.2f}" in body
    assert expected["transaction_count"] < 8


# --------------------------------------------------------------------- #
# Empty range: no matching expenses
# --------------------------------------------------------------------- #

def test_profile_empty_range_shows_zero_state(auth_client):
    c, _ = auth_client
    future_start = (date.today() + timedelta(days=100)).isoformat()
    future_end = (date.today() + timedelta(days=110)).isoformat()

    resp = c.get(f"/profile?date_from={future_start}&date_to={future_end}")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "0.00" in body
    assert "₹0.00" in body


def test_profile_empty_range_no_exceptions_for_new_user(client):
    """A logged-in user with zero expenses anywhere must not error on a filtered request."""
    c, _ = client
    conn = db.get_db()
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("No Expenses", "noexp@spendly.com", "hash"),
    )
    conn.commit()
    new_user_id = cursor.lastrowid
    conn.close()

    with c.session_transaction() as sess:
        sess["user_id"] = new_user_id
        sess["user_name"] = "No Expenses"

    resp = c.get("/profile?date_from=2026-01-01&date_to=2026-01-31")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "₹0.00" in body


# --------------------------------------------------------------------- #
# Category breakdown percentages sum to 100% within a filtered range (route)
# --------------------------------------------------------------------- #

def test_profile_category_breakdown_percentages_sum_100_filtered(auth_client):
    c, user_id = auth_client
    today = date.today()
    start = today.replace(day=1).isoformat()
    end = today.isoformat()

    resp = c.get(f"/profile?date_from={start}&date_to={end}")
    assert resp.status_code == 200

    breakdown = get_category_breakdown(user_id, date_from=start, date_to=end)
    assert breakdown
    assert sum(item["pct"] for item in breakdown) == 100
