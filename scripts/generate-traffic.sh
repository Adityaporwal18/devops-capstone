#!/usr/bin/env bash
set -euo pipefail
interval="${1:-0.2}"
node="$(kubectl --context capstone get nodes -o jsonpath='{.items[0].status.addresses[0].address}')"
while true; do
  curl -s -o /dev/null --max-time 3 "http://${node}:30080/api/events" || true
  sleep "$interval"
done
