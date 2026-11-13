import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pytest

from src.watches_app import create_app
from src.watches_app import picker
from src.watches_app.db import get_db, init_db


@pytest.fixture
def app(tmp_path):
    app = create_app(instance_path=tmp_path / "instance")
    app.config["TESTING"] = True
    with app.app_context():
        init_db()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def add_watch(db, brand="Brand", name="Name", image="img.jpg"):
    cursor = db.execute(
        "INSERT INTO watches (brand, name, image_filename) VALUES (?, ?, ?)",
        (brand, name, image),
    )
    db.commit()
    return cursor.lastrowid


def test_pick_is_stable_for_the_day(app):
    with app.app_context():
        db = get_db()
        for i in range(3):
            add_watch(db, name=f"Watch {i}")
        today = date.today()
        first = picker.pick_for(db, today)
        for _ in range(5):
            assert picker.pick_for(db, today)["id"] == first["id"]


def test_full_rotation_before_any_repeat(app):
    with app.app_context():
        db = get_db()
        ids = {add_watch(db, name=f"Watch {i}") for i in range(5)}
        day = date(2026, 1, 1)

        first_round = {picker.pick_for(db, day + timedelta(days=i))["id"] for i in range(5)}
        assert first_round == ids

        second_round = {picker.pick_for(db, day + timedelta(days=5 + i))["id"] for i in range(5)}
        assert second_round == ids


def test_new_watch_joins_front_of_rotation(app):
    with app.app_context():
        db = get_db()
        add_watch(db, name="Old")
        picker.pick_for(db, date(2026, 1, 1))
        new_id = add_watch(db, name="New")
        assert picker.pick_for(db, date(2026, 1, 2))["id"] == new_id


def test_archived_watch_is_never_picked(app):
    with app.app_context():
        db = get_db()
        keep = add_watch(db, name="Keep")
        gone = add_watch(db, name="Gone")
        db.execute("UPDATE watches SET archived = 1 WHERE id = ?", (gone,))
        db.commit()
        day = date(2026, 1, 1)
        for i in range(4):
            assert picker.pick_for(db, day + timedelta(days=i))["id"] == keep


def test_pick_with_no_watches_returns_none(app):
    with app.app_context():
        assert picker.pick_for(get_db(), date.today()) is None


def test_index_empty_state(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"No watches yet" in response.data


def test_pick_endpoint_redirects_to_today(app, client):
    with app.app_context():
        add_watch(get_db())
    response = client.post("/pick", follow_redirects=True)
    assert b"The watch for the day is" in response.data
    response = client.get("/")
    assert b"Today&#39;s watch" in response.data or b"Today's watch" in response.data


def test_add_watch_via_form(app, client, tmp_path):
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"fake image bytes")
    response = client.post(
        "/watches/new",
        data={"brand": "Seiko", "name": "SKX007", "photo": photo.open("rb")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"Seiko SKX007 added" in response.data
    with app.app_context():
        row = get_db().execute("SELECT * FROM watches").fetchone()
        assert row["brand"] == "Seiko"
        uploads = app.config["UPLOAD_DIR"]
        assert (row["image_filename"]).startswith("seiko_skx007_")
        import os
        assert row["image_filename"] in os.listdir(uploads)


def test_add_watch_rejects_bad_extension(client, tmp_path):
    bad = tmp_path / "notes.txt"
    bad.write_text("not an image")
    response = client.post(
        "/watches/new",
        data={"brand": "X", "name": "Y", "photo": bad.open("rb")},
        content_type="multipart/form-data",
    )
    assert "Unsupported image type".encode() in response.data


def test_archive_endpoint(app, client):
    with app.app_context():
        watch_id = add_watch(get_db())
    client.post(f"/watches/{watch_id}/archive")
    with app.app_context():
        assert get_db().execute(
            "SELECT archived FROM watches WHERE id = ?", (watch_id,)
        ).fetchone()["archived"] == 1


def test_history_lists_picks(app, client):
    with app.app_context():
        db = get_db()
        add_watch(db, brand="Sinn", name="903 St")
        picker.pick_for(db, date.today())
    response = client.get("/history")
    assert b"Sinn" in response.data


def test_import_bundled_collection(app):
    from src.watches_app.importer import SEED_WATCHES, import_watches

    with app.app_context():
        db = get_db()
        upload_dir = Path(app.config["UPLOAD_DIR"])
        imported, skipped, missing = import_watches(db, upload_dir)
        assert (imported, skipped, missing) == (len(SEED_WATCHES), 0, [])
        assert len(list(upload_dir.iterdir())) == len(SEED_WATCHES)

        # Running it again is a no-op.
        assert import_watches(db, upload_dir) == (0, len(SEED_WATCHES), [])
