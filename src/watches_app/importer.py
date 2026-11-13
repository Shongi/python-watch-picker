"""One-time import of the starting watch collection.

The collection and its photos (in seed_images/) come from the older Rails
version of this app: https://github.com/Shongi/rails-watch-picker

Copies each photo into the upload folder and inserts the watch row.
Idempotent: watches that already exist (same brand + name) are skipped.
After this has run once, the database is the source of truth and new
watches are added through the web form.
"""

import shutil
from pathlib import Path

SEED_IMAGE_DIR = Path(__file__).parent / "seed_images"

# Mirrors db/seeds.rb in the Rails app.
SEED_WATCHES = [
    ("Orient", "Triton", "triton.jpeg"),
    ("Hamilton", "Khaki Field King", "king.jpeg"),
    ("Glycine", "Airman GMT", "airman.jpeg"),
    ("Citizen", "Promaster Nighthawk", "nighthawk.jpeg"),
    ("Bulova", "Lunar Pilot", "lunar_pilot.jpeg"),
    ("Casio", "G-Shock GW-B5600HR-1", "gshock.jpeg"),
    ("Zelos", "Swordfish 40 SS Frost", "swordfish_ss.jpeg"),
    ("Zelos", "Swordfish 40 Bronze Meteorite", "swordfish_bronze.jpeg"),
    ("Zelos", "Hammerhead 3 Burnt Orange", "hammerhead_ss.jpeg"),
    ("Zelos", "Mako V3 Titanium Storm Grey", "mako.jpeg"),
    ("Zelos", "Skyraider 2 Ti Forged Carbon", "skyraider.jpeg"),
    ("Hemel", "Airfoil Panda", "airfoil.jpeg"),
    ("Christopher Ward", "C63 Sealander GMT", "c63.jpeg"),
    ("Zelos", "Comet Tuxedo", "comet.jpeg"),
    ("Zelos", "Hammerhead 3 Bronze SW Limited Edition", "hammerhead_bronze.jpeg"),
    ("Formex", "Essence Leggera FortyOne Electric Blue", "essence_leggera.jpeg"),
    ("Baltany", "Vintage Military Chronograph", "baltany.jpeg"),
    ("Sinn", "903 St", "903.jpeg"),
    ("RZE", "Resolute Workbench Edition", "resolute.jpeg"),
    ("Helm", "Vanuatu", "vanuatu.jpeg"),
    ("Christopher Ward", "Twelve (Ti) Astral Blue", "twelve.jpeg"),
    ("Zelos", "Aurora Field Damascus", "aurora.jpeg"),
    ("Studio Underd0g", "Field Steffany Blue", "underd0g.jpeg"),
    ("Zelos", "Blacktip Ti Aventurine", "blacktip.jpeg"),
    ("Zelos", "Eagle 2 Ti Arctic", "eagle.jpeg"),
    ("Christopher Ward", "C63 Valour", "c63_valour.jpeg"),
    ("Zelos", "Helmsman 10th Anniversary Edition", "helmsman_10th_ae.jpeg"),
    ("Erebus", "Accent", "erebus.jpg"),
    ("Revelot", "Terra", "revelot.jpg"),
]


def import_watches(db, upload_dir: Path, image_dir: Path = SEED_IMAGE_DIR):
    imported, skipped, missing = 0, 0, []
    for brand, name, filename in SEED_WATCHES:
        exists = db.execute(
            "SELECT 1 FROM watches WHERE brand = ? AND name = ?", (brand, name)
        ).fetchone()
        if exists:
            skipped += 1
            continue

        source = image_dir / filename
        if not source.exists():
            missing.append(str(source))
            continue

        shutil.copy2(source, upload_dir / filename)
        db.execute(
            "INSERT INTO watches (brand, name, image_filename) VALUES (?, ?, ?)",
            (brand, name, filename),
        )
        imported += 1

    db.commit()
    return imported, skipped, missing
