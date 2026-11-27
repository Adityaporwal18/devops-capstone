import re
from datetime import date

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_CAPACITY = 5000


class ValidationError(ValueError):
    pass


def _text(data, field, minimum, maximum):
    value = data.get(field)
    if not isinstance(value, str):
        raise ValidationError(f"{field} is required")
    value = value.strip()
    if not minimum <= len(value) <= maximum:
        raise ValidationError(f"{field} must be {minimum} to {maximum} characters")
    return value


def clean_event(data):
    if not isinstance(data, dict):
        raise ValidationError("a JSON object is required")
    capacity = data.get("capacity")
    if isinstance(capacity, bool) or not isinstance(capacity, int):
        raise ValidationError("capacity must be a whole number")
    if not 1 <= capacity <= MAX_CAPACITY:
        raise ValidationError(f"capacity must be 1 to {MAX_CAPACITY}")
    try:
        event_date = date.fromisoformat(str(data.get("event_date", "")))
    except ValueError:
        raise ValidationError("event_date must be a date in YYYY-MM-DD format") from None
    return {
        "title": _text(data, "title", 3, 120),
        "venue": _text(data, "venue", 2, 120),
        "event_date": event_date,
        "capacity": capacity,
    }


def clean_registration(data):
    if not isinstance(data, dict):
        raise ValidationError("a JSON object is required")
    name = _text(data, "name", 2, 80)
    email = _text(data, "email", 5, 120).lower()
    if not EMAIL_PATTERN.match(email):
        raise ValidationError("email is not valid")
    return {"name": name, "email": email}


def seats_left(capacity, registered):
    return capacity - registered


def is_full(capacity, registered):
    return registered >= capacity
