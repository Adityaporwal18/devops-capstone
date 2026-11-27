#!/usr/bin/env bash
set -uo pipefail
requests="${1:-300}"
max_error_percent="${MAX_ERROR_PERCENT:-2}"
max_avg_ms="${MAX_AVG_MS:-500}"
min_canary_requests="${MIN_CANARY_REQUESTS:-20}"
kubectl="${KUBECTL:-kubectl}"
report="${REPORT:-reports/canary-analysis.txt}"

analyse() {
  local node url headers code seconds track
  declare -A total errors micros
  for track in stable canary; do
    total[$track]=0
    errors[$track]=0
    micros[$track]=0
  done
  node="$($kubectl get nodes -o jsonpath='{.items[0].status.addresses[0].address}')"
  url="http://${node}:30080/api/events"
  headers="$(mktemp)"

  for _ in $(seq 1 "$requests"); do
    : > "$headers"
    read -r code seconds < <(curl -s --max-time 5 -o /dev/null -D "$headers" -w '%{http_code} %{time_total}\n' "$url" || echo "000 0")
    track="$(tr -d '\r' < "$headers" | awk 'tolower($1) == "x-eventhub-track:" { print $2 }')"
    [ "$track" = "canary" ] || track="stable"
    total[$track]=$(( total[$track] + 1 ))
    [ "$code" = "200" ] || errors[$track]=$(( errors[$track] + 1 ))
    micros[$track]=$(( micros[$track] + $(awk -v s="$seconds" 'BEGIN { printf "%d", s * 1000000 }') ))
  done
  rm -f "$headers"

  echo "Canary analysis: ${requests} requests to ${url}"
  printf '%-8s %9s %8s %11s %9s\n' track requests failed error-rate avg-ms
  for track in stable canary; do
    awk -v t="$track" -v n="${total[$track]}" -v e="${errors[$track]}" -v us="${micros[$track]}" 'BEGIN {
      printf "%-8s %9d %8d %10.1f%% %9.1f\n", t, n, e, (n ? e * 100 / n : 0), (n ? us / n / 1000 : 0) }'
  done
  echo "Policy: roll back if the canary's error rate is above ${max_error_percent}%, its average response time is"
  echo "        above ${max_avg_ms} ms, or it received fewer than ${min_canary_requests} requests."

  awk -v n="${total[canary]}" -v e="${errors[canary]}" -v us="${micros[canary]}" \
      -v me="$max_error_percent" -v ma="$max_avg_ms" -v mn="$min_canary_requests" 'BEGIN {
    if (n < mn) { print "DECISION: ROLLBACK - not enough canary traffic to judge the release"; exit 1 }
    if (e * 100 / n > me) { printf "DECISION: ROLLBACK - canary error rate %.1f%% is above %s%%\n", e * 100 / n, me; exit 1 }
    if (us / n / 1000 > ma) { printf "DECISION: ROLLBACK - canary average response time %.1f ms is above %s ms\n", us / n / 1000, ma; exit 1 }
    print "DECISION: PROMOTE - the canary is within the policy"
  }'
}

mkdir -p "$(dirname "$report")"
analyse 2>&1 | tee "$report"
exit "${PIPESTATUS[0]}"
