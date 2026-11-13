import uuid
from datetime import date
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

from . import picker
from .db import get_db

bp = Blueprint("watches", __name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@bp.get("/")
def index():
    db = get_db()
    watches = picker.watches_with_counts(db)
    today = picker.todays_pick(db, date.today())
    fewest = min((w["pick_count"] for w in watches), default=0)
    return render_template(
        "index.html", watches=watches, today=today, fewest=fewest
    )


@bp.post("/pick")
def pick():
    watch = picker.pick_for(get_db(), date.today())
    if watch is None:
        flash("No watches in the collection yet — add one first!")
        return redirect(url_for("watches.index"))
    return redirect(url_for("watches.today"))


@bp.get("/today")
def today():
    watch = picker.todays_pick(get_db(), date.today())
    if watch is None:
        return redirect(url_for("watches.index"))
    return render_template("today.html", watch=watch)


@bp.route("/watches/new", methods=["GET", "POST"])
def new_watch():
    if request.method == "POST":
        brand = request.form.get("brand", "").strip()
        name = request.form.get("name", "").strip()
        photo = request.files.get("photo")

        if not brand or not name or not photo or not photo.filename:
            flash("Brand, name and a photo are all required.")
            return render_template("new_watch.html", brand=brand, name=name)

        ext = Path(photo.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            flash(f"Unsupported image type “{ext}” — use jpg, png or webp.")
            return render_template("new_watch.html", brand=brand, name=name)

        stem = secure_filename(f"{brand}_{name}").lower() or "watch"
        filename = f"{stem}_{uuid.uuid4().hex[:8]}{ext}"
        photo.save(Path(current_app.config["UPLOAD_DIR"]) / filename)

        db = get_db()
        db.execute(
            "INSERT INTO watches (brand, name, image_filename) VALUES (?, ?, ?)",
            (brand, name, filename),
        )
        db.commit()
        flash(f"{brand} {name} added to the collection.")
        return redirect(url_for("watches.index"))

    return render_template("new_watch.html", brand="", name="")


@bp.post("/watches/<int:watch_id>/archive")
def archive(watch_id):
    db = get_db()
    db.execute("UPDATE watches SET archived = 1 WHERE id = ?", (watch_id,))
    db.commit()
    flash("Watch removed from the rotation.")
    return redirect(url_for("watches.index"))


@bp.get("/history")
def history():
    picks = get_db().execute(
        """
        SELECT p.picked_on, w.brand, w.name, w.image_filename
        FROM picks p JOIN watches w ON w.id = p.watch_id
        ORDER BY p.picked_on DESC
        """
    ).fetchall()
    return render_template("history.html", picks=picks)


@bp.get("/images/<path:filename>")
def image(filename):
    return send_from_directory(current_app.config["UPLOAD_DIR"], filename)
