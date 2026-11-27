#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
kubectl="${KUBECTL:-kubectl --context capstone}"
start="$(date +%s%3N)"
$kubectl -n eventhub delete pod eventhub-db-restore --ignore-not-found > /dev/null
$kubectl apply -f deploy/recovery/restore-pod.yaml > /dev/null
$kubectl -n eventhub wait --for=jsonpath='{.status.phase}'=Succeeded pod/eventhub-db-restore --timeout=240s > /dev/null
end="$(date +%s%3N)"
$kubectl -n eventhub logs eventhub-db-restore
$kubectl -n eventhub delete pod eventhub-db-restore > /dev/null
echo "restore took: $(( end - start )) ms"
