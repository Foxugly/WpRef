from __future__ import annotations

import os
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, CommandError, call_command


class Command(BaseCommand):
    help = "DEV ONLY: delete sqlite DB + delete migration files 00*.py + recreate DB + seed dev data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--noinput",
            action="store_true",
            help="Do not prompt for confirmation.",
        )
        parser.add_argument(
            "--seed-command",
            default="init_dev_data",
            help="Name of the seed BaseCommand to run after migrate (default: init_dev_data).",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Refusing to run because DEBUG=False (DEV ONLY).")

        db_path = self._get_sqlite_db_path()
        if db_path is None:
            raise CommandError("This command supports sqlite only (DATABASES['default']['ENGINE'] must be sqlite3).")

        if not options["noinput"]:
            self.stdout.write(self.style.WARNING("⚠️ This will DELETE your sqlite DB and migration files (00*.py)."))
            answer = input("Type 'YES' to continue: ").strip()
            if answer != "YES":
                self.stdout.write("Aborted.")
                return

        self._delete_sqlite_db(db_path)
        self._delete_migration_files()

        # Recreate DB schema
        call_command("makemigrations")
        call_command("migrate")

        # Seed
        seed_cmd = options["seed_command"]
        call_command(seed_cmd)

        self.stdout.write(self.style.SUCCESS("✅ reset_sqlite_and_seed done"))

    def _get_sqlite_db_path(self) -> Path | None:
        cfg = settings.DATABASES.get("default", {})
        if cfg.get("ENGINE") != "django.db.backends.sqlite3":
            return None
        name = cfg.get("NAME")
        if not name:
            return None
        return Path(name)

    def _delete_sqlite_db(self, db_path: Path) -> None:
        if db_path.exists():
            db_path.unlink()
            self.stdout.write(self.style.SUCCESS(f"✔ Deleted DB: {db_path}"))
        else:
            self.stdout.write(f"✔ DB not found (ok): {db_path}")

    def _delete_migration_files(self) -> None:
        # Supprime uniquement les fichiers 00*.py dans tous les dossiers migrations, en gardant __init__.py
        base_dir = Path(settings.BASE_DIR)

        deleted = 0
        for mig_dir in base_dir.rglob("migrations"):
            if not mig_dir.is_dir():
                continue

            for py in mig_dir.glob("00*.py"):
                # garde __init__.py au cas où (normalement il ne matche pas 00*.py, mais safe)
                if py.name == "__init__.py":
                    continue
                try:
                    py.unlink()
                    deleted += 1
                except OSError:
                    pass

            # Optionnel: supprimer __pycache__ du dossier migrations
            pycache = mig_dir / "__pycache__"
            if pycache.exists() and pycache.is_dir():
                for f in pycache.glob("*"):
                    try:
                        f.unlink()
                    except OSError:
                        pass
                try:
                    pycache.rmdir()
                except OSError:
                    pass

        self.stdout.write(self.style.SUCCESS(f"✔ Deleted migration files: {deleted} file(s)"))
