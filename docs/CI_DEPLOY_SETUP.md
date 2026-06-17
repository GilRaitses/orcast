# CI deploy setup

Why GitHub Actions deploy jobs fail and how to fix them.

## Firebase Hosting (orcast.org)

**Symptom:** `403 Firebase Management API has not been used...` or `Caller does not have required permission`

**Fix:**

1. Open [Firebase console](https://console.firebase.google.com/) → project **orca-904de**
2. Enable [Firebase Management API](https://console.firebase.google.com/project/orca-904de/settings/general)
3. In GCP IAM for project `orca-904de`, grant the CI service account:
   - Firebase Hosting Admin
   - Service Usage Consumer
4. Regenerate a service account key (Project settings → Service accounts → Generate new private key)
5. Update GitHub secret `FIREBASE_SERVICE_ACCOUNT_ORCA_904DE` with the full JSON

**Local deploy (fastest for orcast.org tonight):**

```bash
firebase login
bash tools/deployment/firebase/deploy.sh
```

## Cloudflare Worker (orcast.org API proxy)

**Symptom:** `CLOUDFLARE_API_TOKEN environment variable` missing

**Fix:** Add GitHub repo secrets:

- `CLOUDFLARE_API_TOKEN` — token with Workers deploy permission
- `CLOUDFLARE_ACCOUNT_ID` — from Cloudflare dashboard sidebar

Until set, the Cloudflare workflow skips deploy with a notice (CI stays green).

## AWS backend CI

Runs pytest + `cfn-lint` on `infra/aws/template.yaml`. Should pass after redundant `DependsOn` removal.

## Angular unit tests

`backend.service.spec.ts` uses `http://127.0.0.1:8080` to match `environment.ts`.

## Optional repo variable

Set `ORCAST_BACKEND_URL` = `https://pjrftm3bkv.us-west-2.awsapprunner.com` in GitHub repo variables to override manifest injection.
