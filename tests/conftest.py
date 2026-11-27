import pytest


@pytest.fixture()
def client():
    from app import create_app, db

    db.init_schema()
    with db.connection() as conn:
        conn.execute("TRUNCATE registrations, events RESTART IDENTITY CASCADE")
    return create_app().test_client()


@pytest.fixture()
def event(client):
    response = client.post(
        "/api/events", json={"title": "DevOps Workshop", "venue": "Lab 204", "event_date": "2026-12-10", "capacity": 2}
    )
    return response.get_json()
