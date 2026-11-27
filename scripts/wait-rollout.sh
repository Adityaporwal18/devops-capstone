#!/usr/bin/env bash
set -euo pipefail
revision="${1:?usage: wait-rollout.sh <git revision> <deployment>...}"
shift
kubectl="${KUBECTL:-kubectl}"

$kubectl -n argocd annotate application eventhub argocd.argoproj.io/refresh=hard --overwrite > /dev/null
state=""
for _ in $(seq 1 80); do
  state="$($kubectl -n argocd get application eventhub -o jsonpath='{.status.sync.revision} {.status.sync.status}')"
  [ "$state" = "$revision Synced" ] && break
  sleep 3
done
if [ "$state" != "$revision Synced" ]; then
  echo "Argo CD did not sync revision ${revision} (state: ${state})" >&2
  exit 1
fi
echo "Argo CD synced Git revision ${revision:0:7}"
for deployment in "$@"; do
  $kubectl -n eventhub rollout status "deployment/${deployment}" --timeout=300s
done
