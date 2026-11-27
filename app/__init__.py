import psycopg
from flask import Flask, jsonify, render_template, request
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from . import db, telemetry
from .rules import ValidationError, clean_event, clean_registration, seats_left


def present_event(event):
    return {
        **event,
        "event_date": event["event_date"].isoformat(),
        "seats_left": seats_left(event["capacity"], event["registered"]),
    }


def present_registration(registration):
    return {**registration, "created_at": registration["created_at"].isoformat()}


def create_app():
    app = Flask(__name__)
    telemetry.install(app)

    @app.get("/")
    def home():
        return render_template("index.html", version=telemetry.VERSION, track=telemetry.TRACK)

    @app.get("/api/events")
    def list_events():
        return jsonify([present_event(event) for event in db.list_events()])

    @app.post("/api/events")
    def create_event():
        event = db.create_event(clean_event(request.get_json(silent=True)))
        telemetry.log.info("event created", extra={"fields": {"event_id": event["id"]}})
        return jsonify(present_event(event)), 201

    @app.delete("/api/events/<int:event_id>")
    def delete_event(event_id):
        db.delete_event(event_id)
        return "", 204

    @app.get("/api/events/<int:event_id>/registrations")
    def list_registrations(event_id):
        return jsonify([present_registration(row) for row in db.list_registrations(event_id)])

    @app.post("/api/events/<int:event_id>/registrations")
    def register(event_id):
        registration = db.register(event_id, clean_registration(request.get_json(silent=True)))
        telemetry.REGISTRATIONS.inc()
        telemetry.log.info("registration accepted", extra={"fields": {"event_id": event_id}})
        return jsonify(present_registration(registration)), 201

    @app.get("/api/version")
    def version():
        return jsonify(version=telemetry.VERSION, git_sha=telemetry.GIT_SHA, track=telemetry.TRACK)

    @app.get("/health/live")
    def live():
        return jsonify(status="alive")

    @app.get("/health/ready")
    def ready():
        try:
            db.ping()
        except psycopg.OperationalError:
            telemetry.DATABASE_UP.set(0)
            return jsonify(status="database unavailable"), 503
        telemetry.DATABASE_UP.set(1)
        return jsonify(status="ready")

    @app.get("/metrics")
    def metrics():
        return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

    @app.errorhandler(ValidationError)
    def invalid(error):
        return jsonify(error=str(error)), 400

    @app.errorhandler(db.NotFound)
    def not_found(_error):
        return jsonify(error="event not found"), 404

    @app.errorhandler(db.EventFull)
    def full(_error):
        return jsonify(error="event is full"), 409

    @app.errorhandler(db.AlreadyRegistered)
    def duplicate(_error):
        return jsonify(error="this email is already registered for the event"), 409

    @app.errorhandler(psycopg.OperationalError)
    def database_down(_error):
        telemetry.DATABASE_UP.set(0)
        return jsonify(error="database unavailable"), 503

    return app
