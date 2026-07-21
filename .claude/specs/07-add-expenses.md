# Spec: Add Expenses

## Overview
Step 7 replaces the placeholder `GET /expenses/add` route with a real feature
that lets a logged-in user record a new expense. This is the first write
path in Spendly beyond registration — it introduces a form-backed `POST`
route, an insert query in `database/queries.py`, and a dedicated template.
Once complete, expenses entered here appear immediately in the profile
page's transaction list, summary stats, and category breakdown (Step 5).

## Depends on
- Step 1: Database setup (`expenses` table and `get_db()` exist)
- Step 3: Login / Logout (`session["user_id"]` is set on login)
- Step 5: Backend connection (`database/queries.py` pattern established)

## Routes
- `GET /expenses/add` — render the add-expense form — logged-in only
- `POST /expenses/add` — validate and insert a new expense, redirect to
  `/profile` on success, re-render the form with an error on failure —
  logged-in only

Both methods are handled by the same `add_expense()` view, replacing the
current placeholder.

## Database changes
No database changes. The existing `expenses` table already has all required
columns (`user_id`, `amount`, `category`, `date`, `description`,
`created_at`).

## Templates
- **Create:** `templates/add_expense.html` — form with fields for amount,
  category (select, populated from `database.db.CATEGORIES`), date
  (defaulting to today), and description (optional). Extends `base.html`
  and follows the card-based layout used in `profile.html`.
- **Modify:** `templates/base.html` — add a nav link to `/expenses/add` if
  the nav does not already expose it for logged-in users.

## Files to change
- `app.py` — replace the placeholder `add_expense()` view with a real
  `GET`/`POST` implementation
- `templates/base.html` — add nav link to the add-expense page (only if
  missing)

## Files to create
- `templates/add_expense.html` — the add-expense form
- `database/queries.py` — add `create_expense(user_id, amount, category, date, description)`
  function that inserts a row and returns the new expense id

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`
- Parameterised queries only — never string-format values into SQL
- Passwords hashed with werkzeug (not applicable to this feature, but no
  regressions to existing auth routes)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No inline styles
- Category must be one of `database.db.CATEGORIES` — reject anything else
  server-side, not just via the `<select>` element
- Amount must be a positive number (greater than 0); reject non-numeric or
  zero/negative input server-side
- Date must be a valid ISO date (`YYYY-MM-DD`) and not in the future
- Description is optional; store `NULL`/empty if not provided
- On validation failure, re-render `add_expense.html` with an error message
  and the user's submitted values preserved (do not silently redirect)
- On success, redirect to `/profile` (a flash message confirming the add is
  a nice-to-have, not required)
- Query helper in `database/queries.py` must call `get_db()` internally and
  close the connection before returning

## Definition of done
- [ ] Visiting `/expenses/add` while logged out redirects to `/login`
- [ ] Visiting `/expenses/add` while logged in shows a form with amount,
      category, date, and description fields
- [ ] Submitting the form with a valid amount, category, and date creates a
      new row in `expenses` for the current user
- [ ] After a successful submit, the browser redirects to `/profile` and the
      new expense appears in the transaction list and updates the summary
      stats and category breakdown
- [ ] Submitting with a negative or zero amount re-renders the form with an
      error and does not insert a row
- [ ] Submitting with a category not in `database.db.CATEGORIES` re-renders
      the form with an error and does not insert a row
- [ ] Submitting with a future date re-renders the form with an error and
      does not insert a row
- [ ] Submitting with an empty description succeeds and the transaction list
      shows the row without a description (no error)
