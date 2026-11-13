# Watches

A tiny Flask app that suggests one of my watches to wear each day.

Python rewrite of my older Rails app,
[rails-watch-picker](https://github.com/Shongi/rails-watch-picker), with
upgraded logic and no more seed files.

## How it works

- Every pick is logged in a `picks` table (one row per calendar day), so
  pressing the button twice on the same day always returns the same watch.
- The daily pick is chosen randomly **among the watches with the fewest
  total picks**. That single rule means every watch gets worn once before
  any watch repeats — no `selected` flags, no monthly resets.
- A newly added watch has zero picks, so it automatically joins the front
  of the rotation.

## Pages

- `/` — the collection grid, today's pick banner, and the pick button.
  Watches already worn this round are dimmed. Hover a card for the ✕
  button that removes a watch from the rotation (e.g. after selling it).
- `/today` — the watch of the day, full size.
- `/watches/new` — add a new watch (brand, name, photo upload). This
  replaces reseeding: the SQLite database is the source of truth.
- `/history` — every past pick with its date.

## Tech stack

- Python 3.14, Flask, Jinja templates and plain CSS
- SQLite through the standard-library `sqlite3` module (no ORM)
- gunicorn and Docker Compose for running it as a service
- pytest

## Setup

```bash
python -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/flask --app src.watches_app init-db
```

Optionally, load the starting collection (29 watches, photos bundled in
`src/watches_app/seed_images/`):

```bash
venv/bin/flask --app src.watches_app import-watches
```

The command is idempotent: watches that were already imported are skipped.
You can also skip it and add your own watches through `/watches/new`.

Set `SECRET_KEY` in the environment when running anywhere other than your
own machine. It signs the flash-message cookies, and the built-in fallback
is only meant for local development.

## Run

```bash
venv/bin/flask --app src.watches_app run --port 5001
```

Data lives in `instance/` (SQLite database + uploaded photos), which is
created automatically and ignored by git.

## Docker

```bash
docker compose up -d --build
```

Runs the app on http://localhost:5001 with gunicorn. `./instance` is
bind-mounted into the container, so the database and photos are shared
with a locally-run copy and survive rebuilds. The container timezone is
set in `compose.yaml` so the daily pick rolls over at local midnight.
With `restart: unless-stopped` it comes back up with Docker Desktop
after a reboot; stop it with `docker compose down`.

To load the starting collection into the container's database:

```bash
docker compose exec web flask --app src.watches_app import-watches
```

## Tests

```bash
venv/bin/python -m pytest
```

## License

The code is released under the [MIT License](LICENSE).
