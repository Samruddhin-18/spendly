import sqlite3
from datetime import date

from werkzeug.security import generate_password_hash

DB_PATH = "spendly.db"

CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()
    existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing > 0:
        conn.close()
        return

    password_hash = generate_password_hash("demo123")
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", password_hash),
        )
    except sqlite3.IntegrityError:
        conn.close()
        return
    user_id = cursor.lastrowid

    today = date.today()
    sample_expenses = [
        (25.50, "Food", 1, "Groceries"),
        (12.00, "Transport", 3, "Bus pass"),
        (89.99, "Bills", 5, "Electricity bill"),
        (40.00, "Health", 7, "Pharmacy"),
        (15.75, "Entertainment", 9, "Movie tickets"),
        (60.20, "Shopping", 11, "New shoes"),
        (9.50, "Other", 13, "Miscellaneous"),
        (18.30, "Food", 15, "Restaurant dinner"),
    ]

    for amount, category, day_of_month, description in sample_expenses:
        day = min(day_of_month, 28)
        expense_date = today.replace(day=day).isoformat()
        conn.execute(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, amount, category, expense_date, description),
        )

    conn.commit()
    conn.close()
