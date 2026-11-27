import os
import time

import psycopg

from app import create_app, db
from app.telemetry import log


def prepare_database(attempts=30):
    seed_demo = os.getenv("SEED_DEMO", "false").lower() == "true"
    for attempt in range(1, attempts + 1):
        try:
            db.init_schema(seed_demo=seed_demo)
            return
        except psycopg.OperationalError as error:
            log.warning("database not ready", extra={"fields": {"attempt": attempt, "error": str(error).strip()}})
            time.sleep(2)
    raise SystemExit("database did not become ready")


prepare_database()
app = create_app()
