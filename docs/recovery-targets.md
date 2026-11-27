# Recovery targets

These targets were written down before the recovery drill was run.

| Objective | Target | How it is measured |
|---|---|---|
| RPO - database | At most 30 minutes of data loss | The backup CronJob runs every 30 minutes; an extra backup can be started by hand |
| RTO - database restore | Data restored within 5 minutes | Millisecond timer in `scripts/restore-db.sh`, checked with `scripts/db-fingerprint.sh` |
| RTO - application pod failure | Replaced and Ready within 60 seconds | Time from deleting a pod to 4 of 4 pods Ready |
| RTO - faulty release | Canary removed within 2 minutes of its deployment | Git commit times of the canary and rollback commits made by the pipeline |
| Configuration drift | Corrected within 60 seconds | Time from a manual `kubectl scale` to Argo CD restoring the Git value |

**RTO** (Recovery Time Objective) is the longest acceptable time to restore service.
**RPO** (Recovery Point Objective) is the largest acceptable data loss, expressed as time since the last good backup.
