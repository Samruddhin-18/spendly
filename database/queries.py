from database.db import get_db


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


def get_summary_stats(user_id):
    """Return dict with total_spent, transaction_count, top_category for user_id.

    If the user has no expenses, returns
    {"total_spent": 0, "transaction_count": 0, "top_category": "—"}.
    """
    db = get_db()
    total_row = db.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    count_row = db.execute(
        "SELECT COUNT(*) FROM expenses WHERE user_id = ?", (user_id,)
    ).fetchone()
    top_row = db.execute(
        "SELECT category, SUM(amount) as total FROM expenses "
        "WHERE user_id = ? GROUP BY category ORDER BY total DESC LIMIT 1",
        (user_id,),
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


def get_recent_transactions(user_id, limit=10):
    """Return list of dicts (date, description, category, amount) for user_id,
    ordered newest-first. Returns [] if the user has no expenses.
    """
    conn = get_db()
    rows = conn.execute(
        "SELECT date, description, category, amount FROM expenses "
        "WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_category_breakdown(user_id):
    """Return list of dicts (name, amount, pct) per category for user_id,
    ordered by amount descending. pct values are integers summing to exactly 100
    (rounding remainder absorbed by the largest category). Returns [] if the
    user has no expenses.
    """
    conn = get_db()
    rows = conn.execute(
        "SELECT category, SUM(amount) as total FROM expenses "
        "WHERE user_id = ? GROUP BY category ORDER BY total DESC",
        (user_id,),
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
