# Spec: Registration

## Overview
This step wires up the existing `register.html` form to a real registration flow. Currently `GET /register` renders the template but there is no handler for creating a user — this feature adds server-side validation, password hashing, and persistence of new users into the `users` table established in Step 1, plus a session so the user is considered logged in immediately after registering.

## Depends on
- Step 1 (DB setup) — requires `database/db.py` with `get_db()`, `init_db()`, and the `users` table already in place.

## Routes
- `GET /register` — render the registration form (already exists, no change to behavior) — public
- `POST /register` — validate input, create the user, log them in, redirect to a logged-in landing point — public

## Database changes
No database changes. The existing `users` table (`id`, `name`, `email`, `password_hash`, `created_at`) already supports registration as-is.

## Templates
**Modify:** templates/register.html

- Change the form `action` to `url_for('register')` with `method="post"`
- Add `name` attributes to all inputs:
  `name`, `email`, `password`, `confirm_password`
- Add a block to display a flash error message
  (e.g. "Email already registered",
  "Passwords do not match")
- Keep all existing visual design

## Files to change
- `app.py` — replace the stub `register()` view with a view that handles `GET` and `POST`, validates input, hashes the password, inserts the user, sets the session, and redirects on success

## Files to create
- None

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (`generate_password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate on the server even though the form has `required`/`type=email` attributes client-side
- Catch `sqlite3.IntegrityError` on duplicate email and re-render the form with an error instead of a 500
- Use Flask's `session` for login state (add `app.secret_key`)

## Definition of done
- [ ] Submitting the register form with valid, unique details creates a row in `users` with a hashed (not plaintext) password
- [ ] Submitting with an email that already exists shows an error on the page instead of crashing
- [ ] Submitting with a missing field (name/email/password) shows a validation error instead of crashing
- [ ] After successful registration, the user is redirected away from `/register` (not shown the form again)
- [ ] Password is never visible in plaintext in the database
- [ ] App starts and runs without errors
