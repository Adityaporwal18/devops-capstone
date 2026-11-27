#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker build -q --target test -t eventhub-test . > /dev/null
echo "== unit tests (no database) =="
docker run --rm eventhub-test pytest -q tests/test_rules.py
echo "== integration tests (API + PostgreSQL) =="
trap 'docker compose -f compose.test.yml down -v > /dev/null 2>&1' EXIT
docker compose -f compose.test.yml run --rm --build --quiet-pull tests 2> /dev/null
