# Spec: Login and Logout

## Overview
This step wires up the existing `login.html` form to a real authentication flow and implements session teardown. Currently `GET /login` renders the template but there is no handler for verifying credentials, and `/logout` is a placeholder string. This feature adds server-side credential verification against the `users` table (established in Step 1) and a `session.clear()` based logout, completing the authentication loop that Step 2 (registration) started.

## Depends on
- Step 1 (DB setup) — requires `database/db.py` with `get_db()` and the `users` table.
- Step 2 (Registration) — requires `password_hash` rows created via `generate_password_hash`, and the `session["user_id"]` / `session["user_name"]` convention established there.

## Routes
- `GET /login` — render the login form (already exists, no change to behavior) — public
- `POST /login` — validate credentials, verify password hash, set session, redirect to landing — public
- `GET /logout` — clear the session and redirect to landing (replaces the stub) — logged-in

## Database changes
No database changes. The existing `users` table (`id`, `name`, `email`, `password_hash`, `created_at`) already supports login as-is.

## Templates
**Modify:** templates/login.html

- Add a block to display a flash error message (e.g. "Invalid email or password"), matching the pattern used in `register.html`'s `auth-error` div
- Keep all existing visual design and the existing `action="/login"` / `name` attributes (already present)

## Files to change
- `app.py` — replace the stub `login()` view with a view that handles `GET` and `POST`: on `POST`, look up the user by email, verify the password with `check_password_hash`, set `session["user_id"]`/`session["user_name"]` on success or re-render with an error on failure; replace the stub `logout()` view with one that calls `session.clear()` and redirects to `landing`

## Files to create
- None

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (`generate_password_hash` / `check_password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Do not reveal whether the failure was "no such email" vs "wrong password" — use one generic error message for both
- Use Flask's `session` for login state, consistent with the registration flow

## Definition of done
- [ ] Submitting the login form with the seeded demo credentials (`demo@spendly.com` / `demo123`) logs in and redirects away from `/login`
- [ ] Submitting with a wrong password shows a generic error instead of crashing
- [ ] Submitting with a non-existent email shows the same generic error instead of crashing
- [ ] Visiting `/logout` after logging in clears the session and redirects to the landing page
- [ ] App starts and runs without errors
