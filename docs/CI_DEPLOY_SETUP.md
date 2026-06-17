# CI deploy setup

Why GitHub Actions deploy jobs fail and how to fix them.

## Firebase Hosting (orcast.org)

**Symptom:** `Failed to get Firebase project orca-904de` or `401` on deploy

**Root cause:** GitHub secret `FIREBASE_SERVICE_ACCOUNT_ORCA_904DE` must be a service account key from Firebase project **`orca-904de`**, not `orca-466204`.

**Fix:**

1. Open [Firebase console](https://console.firebase.google.com/) → project **orca-904de**
2. Enable [Firebase Management API](https://console.firebase.google.com/project/orca-904de/settings/general) and Firebase Hosting API
3. Use service account `firebase-adminsdk-fbsvc@orca-904de.iam.gserviceaccount.com` (or `github-action-*@orca-904de.iam.gserviceaccount.com`) with roles:
   - Firebase Admin (or Firebase Hosting Admin)
   - Service Usage Consumer
4. Generate key: `gcloud iam service-accounts keys create key.json --iam-account=firebase-adminsdk-fbsvc@orca-904de.iam.gserviceaccount.com --project=orca-904de`
5. Update GitHub secret: `gh secret set FIREBASE_SERVICE_ACCOUNT_ORCA_904DE < key.json`

**Local deploy (fastest for orcast.org tonight):**

```bash
firebase logout   # clear expired user tokens if you see 401
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/orca-904de-sa-key.json
bash tools/deployment/firebase/deploy.sh
```

Or interactive: `firebase login --reauth` then `bash tools/deployment/firebase/deploy.sh`

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
