from datetime import date

import pytest

from app.rules import ValidationError, clean_event, clean_registration, is_full, seats_left

VALID_EVENT = {"title": "DevOps Workshop", "venue": "Lab 204", "event_date": "2026-12-10", "capacity": 40}


def test_clean_event_accepts_valid_data():
    event = clean_event(VALID_EVENT)
    assert event == {"title": "DevOps Workshop", "venue": "Lab 204", "event_date": date(2026, 12, 10), "capacity": 40}


def test_clean_event_trims_text():
    assert clean_event({**VALID_EVENT, "title": "  Hackathon  "})["title"] == "Hackathon"


@pytest.mark.parametrize("title", ["", "ab", "x" * 121, None, 42])
def test_clean_event_rejects_bad_title(title):
    with pytest.raises(ValidationError):
        clean_event({**VALID_EVENT, "title": title})


@pytest.mark.parametrize("capacity", [0, -5, 5001, "40", 12.5, True, None])
def test_clean_event_rejects_bad_capacity(capacity):
    with pytest.raises(ValidationError):
        clean_event({**VALID_EVENT, "capacity": capacity})


@pytest.mark.parametrize("event_date", ["", "10-12-2026", "2026-13-01", "tomorrow"])
def test_clean_event_rejects_bad_date(event_date):
    with pytest.raises(ValidationError):
        clean_event({**VALID_EVENT, "event_date": event_date})


def test_clean_event_requires_an_object():
    with pytest.raises(ValidationError):
        clean_event(None)


def test_clean_registration_lowercases_email():
    assert clean_registration({"name": "Aditya", "email": "Aditya@Example.COM"}) == {
        "name": "Aditya",
        "email": "aditya@example.com",
    }


@pytest.mark.parametrize("email", ["", "no-at-sign", "a@b", "two words@example.com"])
def test_clean_registration_rejects_bad_email(email):
    with pytest.raises(ValidationError):
        clean_registration({"name": "Aditya", "email": email})


def test_clean_registration_requires_name():
    with pytest.raises(ValidationError):
        clean_registration({"name": " ", "email": "a@example.com"})


def test_seats_left_counts_down():
    assert seats_left(40, 15) == 25


def test_seats_left_never_negative():
    assert seats_left(10, 12) == 0


def test_is_full():
    assert is_full(2, 2) is True
    assert is_full(2, 1) is False
