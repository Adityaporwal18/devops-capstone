# EventHub Capstone - Evidence

All evidence on this page was captured on **27 November 2026** while building and running the platform in an **Ubuntu 24.04.5 LTS virtual machine** (Lima 2.3.0 on a MacBook Pro with Apple M1).

**How it was captured.** Terminal screenshots show the VM's shell session through a browser-based terminal (ttyd attached to tmux). Web screenshots (the application, Jenkins, Argo CD, Prometheus, Grafana, Docker Hub, GitHub) were taken with headless Google Chrome on the Mac through forwarded ports. The capture is automated. Terminal screenshots are cropped below the last line of output; nothing else is edited. Every terminal screenshot has a text log with the complete output under [evidence/logs](evidence/logs).

Evidence is grouped by the sections of the report. The number at the start of each file name gives the order in which the steps were actually run.

[Project overview](../README.md) | [Capstone report](../REPORT.md) | [Commands](../commands.txt)

| Section | Evidence |
|---|---|
| [3. Application and version control](#3-application-and-version-control) | E01-E04 |
| [4. Containerization](#4-containerization) | E05-E11 |
| [5. Infrastructure automation](#5-infrastructure-automation) | E12-E16 |
| [6. Kubernetes orchestration and GitOps](#6-kubernetes-orchestration-and-gitops) | E17-E24 |
| [7. CI/CD pipeline](#7-cicd-pipeline) | E25-E35 |
| [8. Automated testing as a pipeline gate](#8-automated-testing-as-a-pipeline-gate) | E36-E40 |
| [9. Canary deployment and automatic rollback](#9-canary-deployment-and-automatic-rollback) | E41-E52 |
| [10. Monitoring and logging](#10-monitoring-and-logging) | E53-E57 |
| [11. Security](#11-security) | E58-E60 |
| [12. Recoverability](#12-recoverability) | E61-E66 |

## 3. Application and version control

### E01 - Repository initialised with three commits

`git init` and three commits: the application, the tests with their container runner, and the Compose stack. `git ls-files` lists the tracked files.

![E01 Repository initialised with three commits](evidence/screenshots/01-project-files-and-first-commits.png)

Source: [Terminal log](evidence/logs/01-project-files-and-first-commits.txt)

### E02 - Unit and integration tests

`scripts/test.sh` builds the test image and runs both suites in containers: **28 unit tests** of the validation rules (no database) and **13 integration tests** of the API against a real PostgreSQL container. All pass.

![E02 Unit and integration tests](evidence/screenshots/02-unit-and-integration-tests.png)

Source: [Terminal log](evidence/logs/02-unit-and-integration-tests.txt)

### E03 - GitHub repository created and pushed

`gh repo create devops-capstone --public --source=. --push` creates `Adityaporwal18/devops-capstone` and pushes the three commits.

![E03 GitHub repository created and pushed](evidence/screenshots/09-create-github-repository-and-push.png)

Source: [Terminal log](evidence/logs/09-create-github-repository-and-push.txt)

### E04 - Commit history on GitHub

The commit list on GitHub after build #5. Commits by `Adityaporwal18` are source changes; commits by `EventHub Jenkins` are the deployment commits (`deploy: canary ...`, `deploy: promote ...`) that the pipeline pushed.

![E04 Commit history on GitHub](evidence/screenshots/62-github-commit-history.png)

## 4. Containerization

### E05 - Image build and Compose stack

The multi-stage Dockerfile (base, test, runtime) is shown. A random database password is written to `.env` (not committed), and `docker compose up -d --build` starts PostgreSQL and the application. The image `eventhub:0.1.0` is 235 MB on disk.

![E05 Image build and Compose stack](evidence/screenshots/03-docker-build-and-compose-up.png)

Source: [Terminal log](evidence/logs/03-docker-build-and-compose-up.txt)

### E06 - API, health check, metrics and JSON logs

The readiness check returns `ready`; `/api/version` reports version 0.1.0 and the Git commit. A registration is accepted (HTTP 201 body) and the same email is then rejected. `/metrics` shows one registration, the database gauge and the build info; the application logs are JSON lines.

![E06 API, health check, metrics and JSON logs](evidence/screenshots/04-api-health-metrics-and-logs.png)

Source: [Terminal log](evidence/logs/04-api-health-metrics-and-logs.txt)

### E07 - EventHub dashboard (Compose)

The EventHub dashboard served by the container, with the three demo events.

![E07 EventHub dashboard (Compose)](evidence/screenshots/05-eventhub-dashboard-compose.png)

### E08 - Container hardening

The process runs as UID 10001 (not root), the root filesystem is read-only (`touch` fails), all Linux capabilities are dropped and `no-new-privileges` is set.

![E08 Container hardening](evidence/screenshots/06-container-hardening.png)

Source: [Terminal log](evidence/logs/06-container-hardening.txt)

### E09 - First image pushed to Docker Hub

The image is tagged `adityaporwal18/eventhub:0.1.0` and pushed. The Compose stack is then stopped; its database volume remains.

![E09 First image pushed to Docker Hub](evidence/screenshots/07-push-first-image-to-docker-hub.png)

Source: [Terminal log](evidence/logs/07-push-first-image-to-docker-hub.txt)

### E10 - Repository on Docker Hub

The public Docker Hub page of `adityaporwal18/eventhub` with the tag `0.1.0`.

![E10 Repository on Docker Hub](evidence/screenshots/08-docker-hub-repository.png)

### E11 - Image tags published by the pipeline

Docker Hub after build #5: the pipeline has pushed one image per build, tagged with the short Git commit (`139f0d6`, `df2f16d`, ...).

![E11 Image tags published by the pipeline](evidence/screenshots/61-docker-hub-image-tags.png)

## 5. Infrastructure automation

### E12 - Ansible bootstrap, first run

The playbook checks the tools, starts the Minikube profile `capstone`, installs Argo CD v3.6.3, scales its three unused components to zero and waits for the rest. Recap: `ok=11 changed=4 failed=0`. The first tasks have scrolled off the screen; the text log has all of them.

![E12 Ansible bootstrap, first run](evidence/screenshots/10-ansible-bootstrap-first-run.png)

Source: [Terminal log](evidence/logs/10-ansible-bootstrap-first-run.txt)

### E13 - Cluster and Argo CD ready

The kubectl context is `capstone`, the node is Ready (Kubernetes v1.37.0) and the four Argo CD pods are Running.

![E13 Cluster and Argo CD ready](evidence/screenshots/11-cluster-and-argocd-ready.png)

Source: [Terminal log](evidence/logs/11-cluster-and-argocd-ready.txt)

### E14 - Ansible second run; Terraform init

Running the playbook again changes nothing (`ok=7 changed=0 skipped=4`). `terraform init` installs the providers, and `fmt -check` and `validate` succeed.

![E14 Ansible second run; Terraform init](evidence/screenshots/12-ansible-idempotent-and-terraform-init.png)

Source: [Terminal log](evidence/logs/12-ansible-idempotent-and-terraform-init.txt)

### E15 - Terraform plan and apply

The plan creates six resources: two namespaces, a resource quota, a limit range, a random password and the database Secret (its data is shown as a sensitive value). `terraform apply` adds all six.

![E15 Terraform plan and apply](evidence/screenshots/13-terraform-plan-and-apply.png)

Source: [Terminal log](evidence/logs/13-terraform-plan-and-apply.txt)

### E16 - Terraform resources in the cluster

The state lists the six resources. The namespaces exist, the quota allows 20 pods, and the Secret is described by key name and size only. A second `terraform plan` reports no differences.

![E16 Terraform resources in the cluster](evidence/screenshots/14-terraform-resources-in-cluster.png)

Source: [Terminal log](evidence/logs/14-terraform-resources-in-cluster.txt)

## 6. Kubernetes orchestration and GitOps

### E17 - Argo CD application created

The infrastructure code and manifests are committed and pushed. `infrastructure/argocd/application.yaml` points Argo CD at `deploy/k8s` on `main` with automated sync, prune and self-heal. After `kubectl apply` the application becomes Synced and Healthy.

![E17 Argo CD application created](evidence/screenshots/15-argocd-application-created.png)

Source: [Terminal log](evidence/logs/15-argocd-application-created.txt)

### E18 - Application running in Kubernetes

Argo CD created everything from Git: the stable Deployment (4/4), the canary Deployment (0 replicas), the PostgreSQL StatefulSet, the backup CronJob, two Services and two bound PersistentVolumeClaims. The pods are Running.

![E18 Application running in Kubernetes](evidence/screenshots/16-application-running-in-kubernetes.png)

Source: [Terminal log](evidence/logs/16-application-running-in-kubernetes.txt)

### E19 - Application reachable through the Service

Through a port-forward the application reports version 0.1.0 and readiness. Six requests through the NodePort are all answered by the `stable` track.

![E19 Application reachable through the Service](evidence/screenshots/17-application-reachable-through-service.png)

Source: [Terminal log](evidence/logs/17-application-reachable-through-service.txt)

### E20 - EventHub dashboard (Kubernetes)

The dashboard served from the cluster.

![E20 EventHub dashboard (Kubernetes)](evidence/screenshots/18-eventhub-dashboard-kubernetes.png)

### E21 - Argo CD resource tree

The Argo CD view of the application: Healthy, Synced to `main`, auto sync enabled, with the Deployments, StatefulSet, CronJob, Services and volume claims.

![E21 Argo CD resource tree](evidence/screenshots/19-argocd-application-tree.png)

### E22 - Monitoring and logging stack deployed by Argo CD

Terraform adds two more resources (the Grafana admin password and its Secret). The platform manifests are pushed and a second Argo CD application, `eventhub-platform`, deploys Prometheus, Grafana, Loki and Promtail. Both applications are Synced and Healthy.

![E22 Monitoring and logging stack deployed by Argo CD](evidence/screenshots/20-platform-stack-deployed.png)

Source: [Terminal log](evidence/logs/20-platform-stack-deployed.txt)

### E23 - Cluster state after build #5

Both Deployments reference image `139f0d6`, the application reports version 0.3.1, both Argo CD applications are Synced and Healthy, and Argo CD's history lists the eight Git revisions it deployed (a canary and a promote or rollback revision for each of four builds).

![E23 Cluster state after build #5](evidence/screenshots/60-final-cluster-state.png)

Source: [Terminal log](evidence/logs/60-final-cluster-state.txt)

### E24 - Argo CD after the releases

Argo CD after build #5: Healthy and Synced to the pipeline's promote commit `a617ff3`.

![E24 Argo CD after the releases](evidence/screenshots/63-argocd-final-application-tree.png)

## 7. CI/CD pipeline

### E25 - Tools and access for Jenkins

Trivy 0.76.2 is downloaded and its checksum verified. The `jenkins` account is added to the `docker` group and receives a copy of the Docker Hub login session. The existing sudo rule lets Jenkins run `kubectl` as the user that owns the cluster configuration.

![E25 Tools and access for Jenkins](evidence/screenshots/21-jenkins-tools-and-access.png)

Source: [Terminal log](evidence/logs/21-jenkins-tools-and-access.txt)

### E26 - Pipeline files committed

The Jenkinsfile, the GitOps and canary scripts, `release.env` (version 0.1.0, fault switch 0) and the Jenkins job definition are committed and pushed.

![E26 Pipeline files committed](evidence/screenshots/23-commit-pipeline-files.png)

Source: [Terminal log](evidence/logs/23-commit-pipeline-files.txt)

### E27 - Jenkins job configuration

The job `devops-capstone` (full page): Pipeline script from SCM, the GitHub repository, branch `*/main`, script path `Jenkinsfile`, Poll SCM, and the rule that polling ignores commits whose message contains `[skip ci]`. The Save/Apply bar is a floating element of the page.

![E27 Jenkins job configuration](evidence/screenshots/24-jenkins-job-configuration.png)

### E28 - Build #1 console - start

Build #1 is **Started by user Aditya Porwal** and checks out commit `ca391aa` from GitHub.

![E28 Build #1 console - start](evidence/screenshots/26-build-1-console-start.png)

Source: [Full console log](evidence/logs/jenkins-build-1-console.txt)

### E29 - Build #1 console - promoted

End of build #1: Argo CD synced the promote commit, the stable Deployment rolled out image `ca391aa`, the reports were archived and the build ends with **Finished: SUCCESS**.

![E29 Build #1 console - promoted](evidence/screenshots/30-build-1-promoted.png)

Source: [Full console log](evidence/logs/jenkins-build-1-console.txt)

### E30 - Build #1 stage view

Stage view of build #1 (2 min 23 s): Checkout SCM, Checkout, the Release pipeline group that contains the ten nested stages, and Post Actions, all successful.

![E30 Build #1 stage view](evidence/screenshots/31-build-1-pipeline-stages.png)

### E31 - Push release 0.2.0

Three commits (the statistics feature, OS security updates in the image, the traffic generator) are pushed at 21:29:49 IST. No build was started by hand.

![E31 Push release 0.2.0](evidence/screenshots/32-push-release-0.2.0.png)

Source: [Terminal log](evidence/logs/32-push-release-0.2.0.txt)

### E32 - Build #2 started by an SCM change

Build #2 begins with **Started by an SCM change**: polling found the pushed commits.

![E32 Build #2 started by an SCM change](evidence/screenshots/33-build-2-started-by-scm-change.png)

Source: [Full console log](evidence/logs/jenkins-build-2-console.txt)

### E33 - Build history

The job page after build #6: #1, #2, #5 and #6 succeeded; #3 (failing test) and #4 (faulty canary) failed as intended.

![E33 Build history](evidence/screenshots/53-jenkins-build-history.png)

### E34 - Operations commits rebased and pushed

The recovery tooling commit (written at 21:45:32) and the job-definition commit are rebased onto the pipeline's deployment commits and pushed. An earlier push of the first commit had been rejected because the pipeline had pushed in the meantime (see the recovery section).

![E34 Operations commits rebased and pushed](evidence/screenshots/66-rebase-and-push-operations-commits.png)

Source: [Terminal log](evidence/logs/66-rebase-and-push-operations-commits.txt)

### E35 - Polling ignores non-application commits

The Git polling log after the documentation push: the commits are ignored and the result is **No changes**, so documentation does not trigger a release.

![E35 Polling ignores non-application commits](evidence/screenshots/64-jenkins-polling-ignores-non-application-commits.png)

Source: [Polling log text](evidence/logs/jenkins-scm-polling-log.txt)

## 8. Automated testing as a pipeline gate

### E36 - Tests pass in the pipeline

Build #1: the integration tests run against a PostgreSQL container started for this build, and all 13 pass (after the 28 unit tests).

![E36 Tests pass in the pipeline](evidence/screenshots/27-build-1-tests-passed.png)

Source: [Full console log](evidence/logs/jenkins-build-1-console.txt)

### E37 - Commit with a bug

`seats_left` is changed so that it can return a negative number. The commit is pushed at 21:33:14 IST.

![E37 Commit with a bug](evidence/screenshots/37-push-commit-with-a-bug.png)

Source: [Terminal log](evidence/logs/37-push-commit-with-a-bug.txt)

### E38 - Build #3 - unit test fails

Build #3: `test_seats_left_never_negative` fails with `assert -2 == 0`; 1 failed, 27 passed.

![E38 Build #3 - unit test fails](evidence/screenshots/38-build-3-unit-test-fails.png)

Source: [Full console log](evidence/logs/jenkins-build-3-console.txt)

### E39 - Build #3 - pipeline stopped

The remaining stages are skipped, the post action reports that the running version is unchanged, and the build ends with **Finished: FAILURE**.

![E39 Build #3 - pipeline stopped](evidence/screenshots/39-build-3-pipeline-stopped.png)

Source: [Full console log](evidence/logs/jenkins-build-3-console.txt)

### E40 - Build #3 stage view

Stage view of build #3: Unit tests failed, and the nine later stages (Integration tests to Promote) did not run.

![E40 Build #3 stage view](evidence/screenshots/40-build-3-pipeline-stages.png)

## 9. Canary deployment and automatic rollback

### E41 - Build #1 - canary analysis

Build #1: with one canary pod next to four stable pods, 300 requests are sent through the Service. 61 reach the canary, none fail, and the decision is **PROMOTE**.

![E41 Build #1 - canary analysis](evidence/screenshots/29-build-1-canary-analysis.png)

Source: [Canary analysis report](evidence/logs/jenkins-build-1-canary-analysis.txt)

### E42 - Build #2 - canary analysis and promotion

Build #2 (release 0.2.0): 60 of 300 requests reach the canary with no failures; the release is promoted.

![E42 Build #2 - canary analysis and promotion](evidence/screenshots/34-build-2-canary-analysis-and-promotion.png)

Source: [Canary analysis report](evidence/logs/jenkins-build-2-canary-analysis.txt)

### E43 - Release 0.2.0 running

After build #2 both Deployments reference image `906fe38`, four stable pods are Running, and the application reports version 0.2.0 and serves the new `/api/stats` endpoint. The Completed pod is a scheduled database backup.

![E43 Release 0.2.0 running](evidence/screenshots/35-release-0.2.0-running-in-cluster.png)

Source: [Terminal log](evidence/logs/35-release-0.2.0-running-in-cluster.txt)

### E44 - Dashboard of version 0.2.0

The dashboard now shows the summary bar and the badge `version 0.2.0 - stable`.

![E44 Dashboard of version 0.2.0](evidence/screenshots/36-eventhub-dashboard-version-0.2.0.png)

### E45 - Push a faulty release

The bug is fixed, and release 0.3.0 is committed with `FAULT_RATE=0.5`: the application's fault switch makes half of its API requests return HTTP 500. Pushed at 21:35:22 IST.

![E45 Push a faulty release](evidence/screenshots/41-push-faulty-release-0.3.0.png)

Source: [Terminal log](evidence/logs/41-push-faulty-release-0.3.0.txt)

### E46 - Build #4 - canary analysis fails

Build #4: all tests and scans pass, and the canary is deployed. Of 300 requests, 72 reach the canary and **38 fail (52.8%)**; the 228 requests served by stable all succeed. Decision: **ROLLBACK**.

![E46 Build #4 - canary analysis fails](evidence/screenshots/42-build-4-canary-analysis-fails.png)

Source: [Canary analysis report](evidence/logs/jenkins-build-4-canary-analysis.txt) | [Full console log](evidence/logs/jenkins-build-4-console.txt)

### E47 - Build #4 - automatic rollback

The post action commits `deploy: roll back canary df2f16d`, Argo CD syncs it, the canary Deployment is back at 0 replicas, and the build ends with **Finished: FAILURE**. The stable Deployment still runs `906fe38`.

![E47 Build #4 - automatic rollback](evidence/screenshots/43-build-4-automatic-rollback.png)

Source: [Full console log](evidence/logs/jenkins-build-4-console.txt)

### E48 - Build #4 stage view

Stage view of build #4: the stages up to Deploy canary succeeded, Canary analysis failed and Promote did not run.

![E48 Build #4 stage view](evidence/screenshots/44-build-4-pipeline-stages.png)

### E49 - After the rollback

The pipeline's commits show the canary deployed at 21:36:57 and rolled back at 21:37:24. Stable runs `906fe38` with 4/4 pods and the canary has 0. All 100 test requests return HTTP 200 from the stable track, version 0.2.0.

![E49 After the rollback](evidence/screenshots/45-after-rollback-stable-serves-all-traffic.png)

Source: [Terminal log](evidence/logs/45-after-rollback-stable-serves-all-traffic.txt)

### E50 - Push the fixed release

Release 0.3.1 sets `FAULT_RATE=0`; a second commit fixes two dashboard queries. Pushed at 21:40:46 IST.

![E50 Push the fixed release](evidence/screenshots/51-push-fixed-release-0.3.1.png)

Source: [Terminal log](evidence/logs/51-push-fixed-release-0.3.1.txt)

### E51 - Build #5 - fixed release promoted

Build #5: 50 of 300 requests reach the canary with no failures; release 0.3.1 is promoted.

![E51 Build #5 - fixed release promoted](evidence/screenshots/52-build-5-fixed-release-promoted.png)

Source: [Canary analysis report](evidence/logs/jenkins-build-5-canary-analysis.txt)

### E52 - Dashboard of the promoted release

The dashboard served by the promoted release after the recovery drill, with 3 events and the 5 restored registrations.

![E52 Dashboard of the promoted release](evidence/screenshots/65-eventhub-dashboard-final-version.png)

## 10. Monitoring and logging

### E53 - Prometheus targets

Prometheus's target page after build #4: the four stable pods are discovered through the Kubernetes API and are UP, each with its `track` label.

![E53 Prometheus targets](evidence/screenshots/48-prometheus-targets.png)

### E54 - Prometheus alert rules

The three alert rules (high error rate, instance down, database down). At the moment of this screenshot, after the rollback, all three are inactive.

![E54 Prometheus alert rules](evidence/screenshots/49-prometheus-alert-rules.png)

### E55 - Error rate by track in Prometheus

The Prometheus graph of failed API requests in percent, by track, over 30 minutes: the spike belongs to the canary of build #4.

![E55 Error rate by track in Prometheus](evidence/screenshots/50-prometheus-error-rate-by-track.png)

### E56 - Grafana dashboard

The provisioned dashboard over 45 minutes. Request rate by track shows the canary share during each release; the failure panel shows the faulty canary near 70% while stable stays at 0%, and a small stable peak at the end from the database restart of the recovery drill. The Loki panels show log volume by level and the newest log lines.

![E56 Grafana dashboard](evidence/screenshots/47-grafana-dashboard-during-releases.png)

### E57 - Metrics, alert history and logs as numbers

Queries over the last 40 minutes. Prometheus: stable served 5,520 good requests to `/api/events` and 17 HTTP 503 (during the database restart of the drill); the canary served 177 good and 50 HTTP 500. The high-error-rate alert was pending and firing for both tracks at some point. Loki: log lines by track and level, and two ERROR lines from the faulty canary, version 0.3.0.

![E57 Metrics, alert history and logs as numbers](evidence/screenshots/46-metrics-alerts-and-logs-queries.png)

Source: [Terminal log](evidence/logs/46-metrics-alerts-and-logs-queries.txt)

## 11. Security

### E58 - GitHub host key and deploy key

GitHub's host key is stored for Jenkins; its fingerprint `SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU` is the one GitHub publishes. A new key pair is registered as a read-write deploy key of this repository only.

![E58 GitHub host key and deploy key](evidence/screenshots/22-github-host-key-and-deploy-key.png)

Source: [Terminal log](evidence/logs/22-github-host-key-and-deploy-key.txt)

### E59 - Jenkins credential store

The Jenkins credential store lists `eventhub-gitops-key` (SSH key used for GitOps commits). Jenkins does not display the key. `lab4-api-key` is from an earlier lab.

![E59 Jenkins credential store](evidence/screenshots/25-jenkins-credentials.png)

### E60 - Image scan in build #1

The Trivy report summary in build #1 for image `ca391aa`: the Debian layer has one finding and the Python packages have none.

![E60 Image scan in build #1](evidence/screenshots/28-build-1-security-scans.png)

Source: [Trivy report, build #1](evidence/logs/jenkins-build-1-trivy.txt) | [Trivy report, build #2](evidence/logs/jenkins-build-2-trivy.txt) | [Bandit report](evidence/logs/jenkins-build-1-bandit.txt) | [pip-audit report](evidence/logs/jenkins-build-1-pip-audit.txt)

## 12. Recoverability

### E61 - Recovery targets written before the drill

`docs/recovery-targets.md` is shown and committed at 21:45:32, before the drill. In this capture `git pull --rebase` fails because one file was not yet committed, so the push is rejected (the pipeline had pushed its own commits). The commit was pushed later, after a rebase.

![E61 Recovery targets written before the drill](evidence/screenshots/54-recovery-targets-defined-first.png)

Source: [Terminal log](evidence/logs/54-recovery-targets-defined-first.txt)

### E62 - Application pod failure

One of the four stable pods is deleted. Kubernetes starts a replacement and all four are Ready again after **7,253 ms**.

![E62 Application pod failure](evidence/screenshots/55-pod-failure-self-healing.png)

Source: [Terminal log](evidence/logs/55-pod-failure-self-healing.txt)

### E63 - Manual drift repaired by Argo CD

The stable Deployment is scaled to 1 by hand at 21:46:26. Argo CD restores the Git value: 4 desired at 21:46:33 and 4/4 Ready at 21:46:47.

![E63 Manual drift repaired by Argo CD](evidence/screenshots/56-argocd-repairs-manual-drift.png)

Source: [Terminal log](evidence/logs/56-argocd-repairs-manual-drift.txt)

### E64 - Backup, then data loss

Five registrations are created (HTTP 201). The fingerprint is 3 events, 5 registrations, checksum `2ad539bc...`. A backup is taken (1,415 bytes). The tables are then emptied: 0 events, 0 registrations.

![E64 Backup, then data loss](evidence/screenshots/57-backup-then-data-loss.png)

Source: [Terminal log](evidence/logs/57-backup-then-data-loss.txt)

### E65 - Timed restore and verification

`restore-db.sh` restores the newest backup in **4,597 ms**. The fingerprint is again 3 events, 5 registrations and the same checksum, and the API reports them.

![E65 Timed restore and verification](evidence/screenshots/58-timed-restore-and-verification.png)

Source: [Terminal log](evidence/logs/58-timed-restore-and-verification.txt)

### E66 - Database pod recreated

The database pod is deleted and is Ready again after **11,741 ms**. The fingerprint is unchanged because the data is on the persistent volume.

![E66 Database pod recreated](evidence/screenshots/59-database-pod-recreated-data-kept.png)

Source: [Terminal log](evidence/logs/59-database-pod-recreated-data-kept.txt)
