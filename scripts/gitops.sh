#!/usr/bin/env bash
set -euo pipefail
action="${1:?usage: gitops.sh <canary|promote|rollback> <image tag>}"
tag="${2:?image tag required}"
cd "$(dirname "$0")/.."

image="adityaporwal18/eventhub"
remote="git@github.com:Adityaporwal18/devops-capstone.git"
stable="deploy/k8s/app-stable.yaml"
canary="deploy/k8s/app-canary.yaml"
export GIT_SSH_COMMAND="ssh -i ${GITOPS_KEY:?GITOPS_KEY is not set} -o IdentitiesOnly=yes -o UserKnownHostsFile=${HOME}/.ssh/known_hosts"

set_image() { sed -i -E "s#(image: ${image}):[A-Za-z0-9._-]+#\1:${tag}#" "$1"; }
set_replicas() { sed -i -E "0,/^  replicas: [0-9]+/s//  replicas: $2/" "$1"; }

git fetch -q "$remote" main
git checkout -q --detach FETCH_HEAD

case "$action" in
  canary)
    set_image "$canary"
    set_replicas "$canary" 1
    message="deploy: canary ${tag} on 1 of 5 pods"
    ;;
  promote)
    set_image "$stable"
    set_replicas "$canary" 0
    message="deploy: promote ${tag} to stable"
    ;;
  rollback)
    set_replicas "$canary" 0
    message="deploy: roll back canary ${tag}"
    ;;
  *)
    echo "unknown action: $action" >&2
    exit 2
    ;;
esac

git add deploy/k8s
if ! git diff --cached --quiet; then
  git -c user.name="EventHub Jenkins" -c user.email="jenkins@eventhub.local" commit -q -m "${message} [skip ci]"
  git push -q "$remote" HEAD:main
fi
git rev-parse HEAD
