# Spec: Edit Expense

## Overview
Step 8 replaces the placeholder `GET /expenses/<id>/edit` route with a real
feature that lets a logged-in user update an existing expense they own. It
reuses the add-expense form layout and validation rules, pre-filled with the
expense's current values, and writes changes back via an `UPDATE` query in
`database/queries.py`. Once complete, edits are reflected immediately in the
profile page's transaction list, summary stats, and category breakdown.

## Depends on
- Step 1: Database setup (`expenses` table and `get_db()` exist)
- Step 3: Login / Logout (`session["user_id"]` is set on login)
- Step 5: Backend connection (`database/queries.py` pattern established)
- Step 7: Add Expenses (`add_expense.html` layout and validation rules to reuse)

## Routes
- `GET /expenses/<int:id>/edit` — render the edit-expense form pre-filled
  with the expense's current values — logged-in only, owner only
- `POST /expenses/<int:id>/edit` — validate and update the expense, redirect
  to `/profile` on success, re-render the form with an error on failure —
  logged-in only, owner only

Both methods are handled by the same `edit_expense(id)` view, replacing the
current placeholder. If the expense does not exist, or exists but belongs to
a different user, respond with a 404.

## Database changes
No new tables or columns. `get_recent_transactions` in
`database/queries.py` currently does not select `id`, so the profile page's
transaction rows have no expense id to link to. This spec adds `id` to that
query's `SELECT` and returned dict so `profile.html` can link each row to
its edit page.

## Templates
- **Create:** `templates/edit_expense.html` — same fields and layout as
  `add_expense.html` (amount, category select from `database.db.CATEGORIES`,
  date, optional description), pre-filled with the expense's current values.
  Extends `base.html`.
- **Modify:** `templates/profile.html` — wrap each transaction row (or add
  an actions cell) with a link to `{{ url_for('edit_expense', id=txn.id) }}`
  so users can reach the edit form from the transaction list.

## Files to change
- `app.py` — replace the placeholder `edit_expense(id)` view with a real
  `GET`/`POST` implementation
- `database/queries.py` — add `id` to `get_recent_transactions`'s SELECT and
  returned dict; add `get_expense_by_id(id, user_id)` and
  `update_expense(id, user_id, amount, category, date, description)`
- `templates/profile.html` — link each transaction row to its edit page

## Files to create
- `templates/edit_expense.html` — the edit-expense form

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
- `get_expense_by_id(id, user_id)` must filter by both `id` AND `user_id` —
  never trust the URL id alone to authorize access to another user's expense
- If the expense is missing or not owned by the current user, return a 404
  (e.g. via `abort(404)`), not a redirect that leaks whether the id exists
- Category must be one of `database.db.CATEGORIES` — reject anything else
  server-side, not just via the `<select>` element
- Amount must be a positive number (greater than 0); reject non-numeric or
  zero/negative input server-side
- Date must be a valid ISO date (`YYYY-MM-DD`) and not in the future
- Description is optional; store `NULL`/empty if not provided
- On validation failure, re-render `edit_expense.html` with an error message
  and the user's submitted values preserved (do not silently redirect)
- On success, redirect to `/profile`
- Query helpers in `database/queries.py` must call `get_db()` internally and
  close the connection before returning
- `update_expense` must include `WHERE id = ? AND user_id = ?` so a user can
  never update another user's expense even via a crafted request

## Definition of done
- [ ] Visiting `/expenses/<id>/edit` while logged out redirects to `/login`
- [ ] Visiting `/expenses/<id>/edit` for an expense owned by another user
      returns a 404
- [ ] Visiting `/expenses/<id>/edit` for a non-existent id returns a 404
- [ ] Visiting `/expenses/<id>/edit` for your own expense shows a form
      pre-filled with its current amount, category, date, and description
- [ ] Submitting the form with valid changes updates the row in `expenses`
      and redirects to `/profile`, where the transaction list, summary
      stats, and category breakdown reflect the new values
- [ ] Submitting with a negative or zero amount re-renders the form with an
      error and does not change the row
- [ ] Submitting with a category not in `database.db.CATEGORIES` re-renders
      the form with an error and does not change the row
- [ ] Submitting with a future date re-renders the form with an error and
      does not change the row
- [ ] The profile page's transaction rows link to their respective edit
      pages
