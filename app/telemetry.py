import json
import logging
import os
import random
import sys
import time

from flask import g, jsonify, request
from prometheus_client import Counter, Gauge, Histogram

VERSION = os.getenv("APP_VERSION", "dev")
GIT_SHA = os.getenv("GIT_SHA", "unknown")
TRACK = os.getenv("TRACK", "stable")
QUIET_ROUTES = {"/metrics", "/health/live", "/health/ready"}

REQUESTS = Counter("eventhub_http_requests_total", "HTTP requests handled", ["method", "route", "status"])
LATENCY = Histogram("eventhub_http_request_duration_seconds", "HTTP request duration in seconds", ["route"])
REGISTRATIONS = Counter("eventhub_registrations_total", "Registrations accepted")
DATABASE_UP = Gauge("eventhub_database_up", "1 when the last database check succeeded, otherwise 0")
BUILD_INFO = Gauge("eventhub_build_info", "Build information of the running instance", ["version", "git_sha", "track"])
BUILD_INFO.labels(VERSION, GIT_SHA, TRACK).set(1)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        entry = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "message": record.getMessage(),
            "version": VERSION,
            "track": TRACK,
        }
        entry.update(getattr(record, "fields", {}))
        return json.dumps(entry)


log = logging.getLogger("eventhub")
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(JsonFormatter())
log.handlers = [_handler]
log.setLevel(logging.INFO)
log.propagate = False


def install(app):
    fault_rate = float(os.getenv("FAULT_RATE", "0"))

    @app.before_request
    def start_request():
        g.started = time.perf_counter()
        if fault_rate and request.path.startswith("/api/") and random.random() < fault_rate:
            return jsonify(error="injected fault (FAULT_RATE test switch)"), 500
        return None

    @app.after_request
    def finish_request(response):
        route = request.url_rule.rule if request.url_rule else "unmatched"
        elapsed = time.perf_counter() - g.get("started", time.perf_counter())
        REQUESTS.labels(request.method, route, response.status_code).inc()
        LATENCY.labels(route).observe(elapsed)
        response.headers["X-EventHub-Track"] = TRACK
        response.headers["X-EventHub-Version"] = VERSION
        if route not in QUIET_ROUTES:
            level = logging.ERROR if response.status_code >= 500 else logging.INFO
            log.log(
                level,
                "request",
                extra={
                    "fields": {
                        "method": request.method,
                        "path": request.path,
                        "status": response.status_code,
                        "duration_ms": round(elapsed * 1000, 2),
                    }
                },
            )
        return response
