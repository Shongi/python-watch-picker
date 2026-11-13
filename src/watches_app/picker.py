"""Daily pick logic.

The watch of the day is chosen once per calendar day and logged in the
`picks` table. Candidates are the active watches with the fewest total
picks, so every watch gets worn once before any watch repeats — no reset
step is ever needed, and a newly added watch (zero picks) automatically
joins the front of the rotation.
"""

import random
import sqlite3
from datetime import date


def todays_pick(db: sqlite3.Connection, today: date):
    return db.execute(
        """
        SELECT w.*, p.picked_on FROM picks p
        JOIN watches w ON w.id = p.watch_id
        WHERE p.picked_on = ?
        """,
        (today.isoformat(),),
    ).fetchone()


def watches_with_counts(db: sqlite3.Connection):
    return db.execute(
        """
        SELECT w.*, COUNT(p.id) AS pick_count
        FROM watches w
        LEFT JOIN picks p ON p.watch_id = w.id
        WHERE w.archived = 0
        GROUP BY w.id
        ORDER BY w.brand, w.name
        """
    ).fetchall()


def pick_for(db: sqlite3.Connection, today: date):
    """Return today's watch, choosing and logging one if not chosen yet."""
    existing = todays_pick(db, today)
    if existing:
        return existing

    rows = watches_with_counts(db)
    if not rows:
        return None

    fewest = min(row["pick_count"] for row in rows)
    candidates = [row for row in rows if row["pick_count"] == fewest]
    chosen = random.choice(candidates)

    try:
        db.execute(
            "INSERT INTO picks (watch_id, picked_on) VALUES (?, ?)",
            (chosen["id"], today.isoformat()),
        )
        db.commit()
    except sqlite3.IntegrityError:
        # A concurrent request logged today's pick first; use that one.
        db.rollback()
    return todays_pick(db, today)
