import os
from pathlib import Path

import click
from flask import Flask

from . import db as database
from . import views
from .importer import import_watches


def create_app(instance_path=None):
    app = Flask(
        __name__,
        instance_path=str(instance_path) if instance_path else None,
        instance_relative_config=True,
    )
    instance = Path(app.instance_path)
    upload_dir = instance / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    app.config.from_mapping(
        # Only signs flash cookies. Set SECRET_KEY in the environment for any
        # deployment; the fallback is for local development only.
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-insecure-key"),
        DATABASE=str(instance / "watches.sqlite"),
        UPLOAD_DIR=str(upload_dir),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    )

    app.teardown_appcontext(database.close_db)
    app.register_blueprint(views.bp)

    @app.cli.command("init-db")
    def init_db_command():
        """Create the database tables."""
        database.init_db()
        click.echo("Database initialized.")

    @app.cli.command("import-watches")
    @click.option(
        "--images-from",
        type=click.Path(exists=True, file_okay=False, path_type=Path),
        default=None,
        help="Read the photos from this folder instead of the bundled seed_images.",
    )
    def import_watches_command(images_from):
        """One-time import of the starting watch collection."""
        database.init_db()
        kwargs = {"image_dir": images_from} if images_from else {}
        imported, skipped, missing = import_watches(
            database.get_db(), Path(app.config["UPLOAD_DIR"]), **kwargs
        )
        click.echo(f"Imported {imported}, skipped {skipped} already present.")
        for path in missing:
            click.echo(f"Missing image, watch not imported: {path}")

    return app
