#!/usr/bin/env bash
set -euo pipefail
kubectl="${KUBECTL:-kubectl --context capstone}"
job="eventhub-db-backup-manual-$(date +%H%M%S)"
$kubectl -n eventhub create job "$job" --from=cronjob/eventhub-db-backup > /dev/null
$kubectl -n eventhub wait --for=condition=complete "job/$job" --timeout=180s > /dev/null
$kubectl -n eventhub logs "job/$job"
