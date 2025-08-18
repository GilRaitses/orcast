---
title: ORCAST Cloud Billing Incident Report
date: 2025-08-18
authors:
  - Gil Raitses
status: Final
---

## Executive Summary

On 2025-08-18, unexpected Google Cloud charges (~$500) were observed. Investigation identified the primary cost driver as a Cloud Run GPU service (`orcast-gemma3-gpu`) in project `orca-466204` running on an NVIDIA L4 GPU (8 vCPU, 32 GiB RAM). The service was publicly invokable and experienced repeated worker timeouts/restarts, keeping the GPU active and accruing costs. Additionally, the production backend (`orcast-production-backend`) had `minScale=1`, maintaining an always-on instance and contributing baseline cost. BigQuery usage was minimal and not a significant cost source.

Immediate remediation steps locked down and then removed the GPU service, and scaled the production backend to zero when idle. A budget and billing export dataset were set up to prevent recurrence and improve visibility.

## Impact

- Billing impact: Approximately $500 in charges on the attached billing account for project `orca-466204`.
- Affected resources:
  - Cloud Run GPU: `orcast-gemma3-gpu` (region: `europe-west4`)
  - Cloud Run backend: `orcast-production-backend` (region: `us-west1`, previously `minScale=1`)
  - BigQuery: sporadic short queries, not material to cost

## Detection

- User-reported unexpected charges prompted investigation.
- Verified active services and configurations using `gcloud` and examined Cloud Run logs for the GPU service.

## Timeline (UTC)

- 2025-08-18 03:27–03:54: Cloud Run logs show repeated worker timeouts and restarts on `orcast-gemma3-gpu`, keeping the GPU active.
- 2025-08-18 ~03:55: Services enumerated; GPU service resources confirmed (1× L4 GPU, 8 vCPU, 32 GiB RAM, timeout 600s, concurrency 4).
- 2025-08-18 ~03:58: Attempt to enable CPU throttling rejected (GPU requires throttling off by design).
- 2025-08-18 ~04:00: Public access removed from GPU service and ingress restricted; production backend set to `minScale=0`.
- 2025-08-18 ~04:02: Budget API enabled; BigQuery dataset `billing_export` created for billing export; budget created for `orca-466204`.
- 2025-08-18 ~04:05: GPU service deleted to fully stop GPU spend.

## Root Cause Analysis

- Primary: Cloud Run GPU service (`orcast-gemma3-gpu`) publicly reachable with GPU resources provisioned; repeated timeouts/restarts and test traffic kept the service warm and billable.
- Contributing:
  - `orcast-production-backend` configured with `minScale=1`, creating a steady baseline cost.
  - No budget alert configured prior to incident.
  - Public invoker (`allUsers`) allowed on the GPU service and ingress not restricted.

## Corrective and Preventive Actions

Actions completed on 2025-08-18 (UTC):

1. Cloud Run GPU service access hardened (then removed):
   - Removed public invocation:
     ```bash
     gcloud run services remove-iam-policy-binding orcast-gemma3-gpu \
       --region=europe-west4 \
       --member="allUsers" \
       --role="roles/run.invoker"
     ```
   - Restricted ingress to internal/LB only:
     ```bash
     gcloud run services update orcast-gemma3-gpu \
       --region=europe-west4 \
       --ingress=internal-and-cloud-load-balancing
     ```
   - Deleted the GPU service to fully stop spend:
     ```bash
     gcloud run services delete orcast-gemma3-gpu \
       --region=europe-west4 --quiet
     ```

2. Scaled production backend to zero when idle:
   ```bash
   gcloud run services update orcast-production-backend \
     --region=us-west1 \
     --min-instances=0
   ```

3. Cost visibility and guardrails:
   - Enabled Budgets API:
     ```bash
     gcloud services enable billingbudgets.googleapis.com \
       --project=orca-466204
     ```
   - Created budget (alerts at 50%, 90%, 100%) for `orca-466204` under billing account `01EA83-AD2B99-EEEBC1`:
     ```bash
     gcloud beta billing budgets create \
       --billing-account=01EA83-AD2B99-EEEBC1 \
       --display-name="ORCAST Budget - orca-466204" \
       --budget-amount=400USD \
       --threshold-rule=percent=0.5 \
       --threshold-rule=percent=0.9 \
       --threshold-rule=percent=1.0 \
       --filter-projects=projects/orca-466204
     ```
   - Created BigQuery dataset for billing export:
     ```bash
     bq --project_id=orca-466204 --location=US mk -d billing_export
     ```
     Note: Enabling the actual Billing Export to BigQuery is performed at the billing account level in the Cloud Console (requires Billing Admin). Point export to `orca-466204.billing_export` once approved.

4. Known constraint documented:
   - CPU throttling cannot be enabled on GPU Cloud Run services. Attempt to set `--cpu-throttling` was rejected as expected; mitigation was to restrict/disable access and then delete the service.

## Verification

- GPU service deleted:
  ```bash
  gcloud run services list --platform=managed --region=europe-west4
  # orcast-gemma3-gpu no longer listed
  ```
- Production backend autoscaling:
  ```bash
  gcloud run services describe orcast-production-backend \
    --region=us-west1 --format="yaml(spec.template.metadata.annotations)"
  # Confirm no autoscaling.knative.dev/minScale annotation (defaults to 0)
  ```
- Logs show no new GPU service activity after deletion.

## Recommendations

- Keep GPU services disabled unless actively needed; when needed, gate access via IAM and internal ingress, and remove public invokers.
- Maintain `minScale=0` for services that do not require warm capacity.
- Keep budgets and alerts in place; enable Billing Export to BigQuery for ongoing monitoring and retrospective analysis.
- Introduce a pre-deploy checklist/runbook for high-cost resources (GPU) including cost flags, IAM, and ingress review.

## Appendix

### Post‑Incident Updates (Notifications and Export)

- Email notification channel created for budget alerts:
  - `projects/orca-466204/notificationChannels/16159749288106136205`
  - Attached to budget `billingAccounts/01EA83-AD2B99-EEEBC1/budgets/de9ef4e5-a06b-46a4-b25e-832f09db1226` (alerts at 50%, 90%, 100%).
- BigQuery dataset created for billing export: `orca-466204.billing_export` (region: US).
- Action required: Enable Billing Export to BigQuery in Console (Billing Admin permission):
  1) Open Cloud Console → Billing → Your billing account `01EA83-AD2B99-EEEBC1`.
  2) In left nav, choose “Billing export”.
  3) Under “BigQuery export”, click “Edit settings”.
  4) Select project `orca-466204`, dataset `billing_export`.
  5) Enable both “Detailed usage cost data” and “Pricing data” (recommended).
  6) Save. Data will start flowing within ~24 hours.

### Projects and Billing Accounts

- Project `orca-466204` → Billing Account `01EA83-AD2B99-EEEBC1` (billing enabled)
- Project `orca-904de`   → Billing Account `01F108-29CA32-AFFF6C` (billing enabled)

### GPU Service Configuration (prior to deletion)

```
Service: orcast-gemma3-gpu (region: europe-west4)
Resources: nvidia.com/gpu=1 (L4), cpu=8, memory=32Gi, concurrency=4, timeout=600s
Annotations: run.googleapis.com/cpu-throttling=false, autoscaling.knative.dev/maxScale=1
```

### Excerpts from Cloud Run Logs (UTC)

Repeated worker timeouts and SIGKILL events (2025-08-18 03:27–03:54), indicating restarts and sustained activation of the GPU instance.

```
2025-08-18 03:27:36 [INFO] Booting worker ...
2025-08-18 03:28:03 [CRITICAL] WORKER TIMEOUT ...
2025-08-18 03:28:05 [ERROR] Worker ... sent SIGKILL! Perhaps out of memory?
...
2025-08-18 03:54:16 [CRITICAL] WORKER TIMEOUT ...
```

### BigQuery Activity Snapshot

Short-lived queries on 2025-07-19 with minimal durations; not a significant contributor to the incident cost.


