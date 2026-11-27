def register(client, event_id, email="aditya@example.com", name="Aditya"):
    return client.post(f"/api/events/{event_id}/registrations", json={"name": name, "email": email})


def test_liveness(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.get_json() == {"status": "alive"}


def test_readiness_checks_the_database(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ready"}


def test_version_reports_build_identity(client):
    body = client.get("/api/version").get_json()
    assert set(body) == {"version", "git_sha", "track"}


def test_responses_carry_track_header(client):
    assert client.get("/api/events").headers["X-EventHub-Track"] == "stable"


def test_create_event_is_stored_and_listed(client, event):
    assert event["seats_left"] == 2
    listed = client.get("/api/events").get_json()
    assert [item["title"] for item in listed] == ["DevOps Workshop"]


def test_create_event_rejects_invalid_data(client):
    response = client.post("/api/events", json={"title": "x", "venue": "Lab", "event_date": "2026-12-10", "capacity": 5})
    assert response.status_code == 400
    assert "title" in response.get_json()["error"]


def test_registration_reduces_seats(client, event):
    assert register(client, event["id"]).status_code == 201
    listed = client.get("/api/events").get_json()[0]
    assert (listed["registered"], listed["seats_left"]) == (1, 1)


def test_duplicate_email_is_rejected(client, event):
    register(client, event["id"])
    response = register(client, event["id"], email="ADITYA@example.com")
    assert response.status_code == 409
    assert "already registered" in response.get_json()["error"]


def test_full_event_rejects_registration(client, event):
    register(client, event["id"], email="one@example.com")
    register(client, event["id"], email="two@example.com")
    response = register(client, event["id"], email="three@example.com")
    assert response.status_code == 409
    assert response.get_json()["error"] == "event is full"


def test_registration_for_unknown_event(client):
    assert register(client, 999).status_code == 404


def test_registrations_are_listed(client, event):
    register(client, event["id"])
    people = client.get(f"/api/events/{event['id']}/registrations").get_json()
    assert [(person["name"], person["email"]) for person in people] == [("Aditya", "aditya@example.com")]


def test_delete_event_removes_it_and_its_registrations(client, event):
    register(client, event["id"])
    assert client.delete(f"/api/events/{event['id']}").status_code == 204
    assert client.get("/api/events").get_json() == []
    assert client.delete(f"/api/events/{event['id']}").status_code == 404


def test_metrics_expose_request_counter(client):
    client.get("/api/events")
    text = client.get("/metrics").get_data(as_text=True)
    assert "eventhub_http_requests_total" in text
    assert "eventhub_build_info" in text
