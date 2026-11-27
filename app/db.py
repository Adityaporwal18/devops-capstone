import os
from contextlib import contextmanager
from datetime import date

import psycopg
from psycopg.rows import dict_row

from .rules import is_full

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    venue TEXT NOT NULL,
    event_date DATE NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS registrations (
    id BIGSERIAL PRIMARY KEY,
    event_id BIGINT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (event_id, email)
);
"""

DEMO_EVENTS = [
    ("DevOps Workshop", "Lab 204, Block A", date(2026, 12, 10), 40),
    ("Cloud Computing Seminar", "Main Auditorium", date(2026, 12, 15), 200),
    ("Hackathon Kick-off", "Innovation Centre", date(2027, 1, 9), 60),
]

ALL_EVENTS = """
SELECT e.id, e.title, e.venue, e.event_date, e.capacity, count(r.id)::int AS registered
FROM events e LEFT JOIN registrations r ON r.event_id = e.id
GROUP BY e.id ORDER BY e.event_date, e.id
"""

ONE_EVENT = """
SELECT e.id, e.title, e.venue, e.event_date, e.capacity, count(r.id)::int AS registered
FROM events e LEFT JOIN registrations r ON r.event_id = e.id
WHERE e.id = %s GROUP BY e.id
"""


class NotFound(Exception):
    pass


class EventFull(Exception):
    pass


class AlreadyRegistered(Exception):
    pass


@contextmanager
def connection():
    with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=3, row_factory=dict_row) as conn:
        yield conn


def init_schema(seed_demo=False):
    with connection() as conn:
        conn.execute("SELECT pg_advisory_xact_lock(4611)")
        conn.execute(SCHEMA)
        empty = conn.execute("SELECT count(*) AS n FROM events").fetchone()["n"] == 0
        if seed_demo and empty:
            conn.cursor().executemany(
                "INSERT INTO events (title, venue, event_date, capacity) VALUES (%s, %s, %s, %s)", DEMO_EVENTS
            )


def ping():
    with connection() as conn:
        conn.execute("SELECT 1")


def stats():
    with connection() as conn:
        return conn.execute(
            "SELECT (SELECT count(*) FROM events)::int AS events, "
            "(SELECT count(*) FROM registrations)::int AS registrations, "
            "(SELECT COALESCE(sum(capacity), 0) FROM events)::int AS seats"
        ).fetchone()


def list_events():
    with connection() as conn:
        return conn.execute(ALL_EVENTS).fetchall()


def get_event(event_id):
    with connection() as conn:
        event = conn.execute(ONE_EVENT, (event_id,)).fetchone()
    if event is None:
        raise NotFound
    return event


def create_event(event):
    with connection() as conn:
        created = conn.execute(
            "INSERT INTO events (title, venue, event_date, capacity) VALUES (%s, %s, %s, %s) RETURNING id",
            (event["title"], event["venue"], event["event_date"], event["capacity"]),
        ).fetchone()
    return get_event(created["id"])


def delete_event(event_id):
    with connection() as conn:
        deleted = conn.execute("DELETE FROM events WHERE id = %s RETURNING id", (event_id,)).fetchone()
    if deleted is None:
        raise NotFound


def list_registrations(event_id):
    get_event(event_id)
    with connection() as conn:
        return conn.execute(
            "SELECT id, name, email, created_at FROM registrations WHERE event_id = %s ORDER BY id", (event_id,)
        ).fetchall()


def register(event_id, registration):
    with connection() as conn:
        event = conn.execute("SELECT capacity FROM events WHERE id = %s FOR UPDATE", (event_id,)).fetchone()
        if event is None:
            raise NotFound
        registered = conn.execute(
            "SELECT count(*)::int AS n FROM registrations WHERE event_id = %s", (event_id,)
        ).fetchone()["n"]
        if is_full(event["capacity"], registered):
            raise EventFull
        try:
            return conn.execute(
                "INSERT INTO registrations (event_id, name, email) VALUES (%s, %s, %s) "
                "RETURNING id, name, email, created_at",
                (event_id, registration["name"], registration["email"]),
            ).fetchone()
        except psycopg.errors.UniqueViolation:
            raise AlreadyRegistered from None
