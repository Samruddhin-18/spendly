from database.db import get_db


def _date_filter_clause(user_id, date_from, date_to):
    """Build a WHERE clause + params list filtering by user_id and an
    optional, independently-bounded date range (either bound may be
    supplied alone for an open-ended range)."""
    where = "WHERE user_id = ?"
    params = [user_id]
    if date_from:
        where += " AND date >= ?"
        params.append(date_from)
    if date_to:
        where += " AND date <= ?"
        params.append(date_to)
    return where, params


def get_user_by_id(user_id):
    """Return dict with name, email, member_since (e.g. 'January 2026') for user_id.

    Returns None if no user with that id exists.
    Formats member_since from users.created_at.
    """
    from datetime import datetime

    db = get_db()
    row = db.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    db.close()

    if row is None:
        return None

    created_at = row["created_at"]
    dt = datetime.strptime(created_at[:10], "%Y-%m-%d")
    member_since = dt.strftime("%B %Y")

    return {
        "name": row["name"],
        "email": row["email"],
        "member_since": member_since,
    }


def get_summary_stats(user_id, date_from=None, date_to=None):
    """Return dict with total_spent, transaction_count, top_category for user_id.

    If the user has no expenses, returns
    {"total_spent": 0, "transaction_count": 0, "top_category": "—"}.
    """
    where, params = _date_filter_clause(user_id, date_from, date_to)

    db = get_db()
    total_row = db.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses " + where, params
    ).fetchone()
    count_row = db.execute(
        "SELECT COUNT(*) FROM expenses " + where, params
    ).fetchone()
    top_row = db.execute(
        "SELECT category, SUM(amount) as total FROM expenses " + where + " "
        "GROUP BY category ORDER BY total DESC LIMIT 1",
        params,
    ).fetchone()
    db.close()

    transaction_count = count_row[0]

    if transaction_count == 0:
        return {"total_spent": 0, "transaction_count": 0, "top_category": "—"}

    return {
        "total_spent": float(total_row[0]),
        "transaction_count": int(transaction_count),
        "top_category": top_row["category"],
    }


def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    """Return list of dicts (date, description, category, amount) for user_id,
    ordered newest-first. Returns [] if the user has no expenses.
    """
    where, params = _date_filter_clause(user_id, date_from, date_to)
    params.append(limit)

    conn = get_db()
    rows = conn.execute(
        "SELECT id, date, description, category, amount FROM expenses " + where + " "
        "ORDER BY date DESC, id DESC LIMIT ?",
        params,
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_expense(user_id, amount, category, date, description):
    """Insert a new expense row for user_id. Returns the new expense id."""
    db = get_db()
    try:
        cursor = db.execute(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, amount, category, date, description or None),
        )
        db.commit()
        return cursor.lastrowid
    finally:
        db.close()


def get_expense_by_id(id, user_id):
    """Return dict (id, amount, category, date, description) for the expense,
    or None if it doesn't exist or isn't owned by user_id."""
    db = get_db()
    row = db.execute(
        "SELECT id, amount, category, date, description FROM expenses "
        "WHERE id = ? AND user_id = ?",
        (id, user_id),
    ).fetchone()
    db.close()
    return dict(row) if row else None


def update_expense(id, user_id, amount, category, date, description):
    """Update an existing expense owned by user_id. No-op if not owned."""
    db = get_db()
    try:
        db.execute(
            """
            UPDATE expenses SET amount = ?, category = ?, date = ?, description = ?
            WHERE id = ? AND user_id = ?
            """,
            (amount, category, date, description or None, id, user_id),
        )
        db.commit()
    finally:
        db.close()


def get_category_breakdown(user_id, date_from=None, date_to=None):
    """Return list of dicts (name, amount, pct) per category for user_id,
    ordered by amount descending. pct values are integers summing to exactly 100
    (rounding remainder absorbed by the largest category). Returns [] if the
    user has no expenses.
    """
    where, params = _date_filter_clause(user_id, date_from, date_to)

    conn = get_db()
    rows = conn.execute(
        "SELECT category, SUM(amount) as total FROM expenses " + where + " "
        "GROUP BY category ORDER BY total DESC",
        params,
    ).fetchall()
    conn.close()

    if not rows:
        return []

    grand_total = sum(row["total"] for row in rows)

    result = [
        {"name": row["category"], "amount": row["total"], "pct": round(row["total"] / grand_total * 100)}
        for row in rows
    ]

    remainder = 100 - sum(item["pct"] for item in result)
    if remainder != 0:
        largest = max(result, key=lambda item: item["amount"])
        largest["pct"] += remainder

    return result
