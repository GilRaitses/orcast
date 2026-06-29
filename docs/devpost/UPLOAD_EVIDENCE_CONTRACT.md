# EvidenceAsset contract

## Schema

```json
{
  "id": "asset_<16 hex chars>",
  "owner_user_id": "<workos_user_id or agent_orcast_automation>",
  "kind": "image | audio | other",
  "filename": "dorsal-fin.jpg",
  "content_type": "image/jpeg",
  "size_bytes": 12345,
  "storage_uri": "s3://<raw_payload_bucket>/evidence/<owner>/<asset_id>/dorsal-fin.jpg",
  "created_at": "<ISO8601>",
  "linked_to": {
    "journal_entry_id": null,
    "community_submission_id": null
  }
}
```

## Endpoint

`POST /api/evidence/assets`  
Auth: `X-ORCAST-Reviewer-Id` header (WorkOS proxy) or `X-ORCAST-Agent-Key` header.  
Content-Type: `multipart/form-data`

Fields:
- `file` — the binary file (required)
- `kind` — `image | audio | other` (optional, inferred from content-type if absent)
- `caption` — short description (optional, max 500 chars)

Response: `EvidenceAsset` JSON with 200.

`GET /api/evidence/assets` — list caller's assets.
`DELETE /api/evidence/assets/{asset_id}` — unlink (tombstone metadata; S3 object not deleted in this wave).

## Validation

- Max size: 25 MB
- Allowed content types: `image/*`, `audio/*`, `application/octet-stream`, any other MIME type
- Filename sanitised: strip directory separators, control chars
- Caller must be signed in (reviewer_id present in headers)

## S3 key structure

`evidence/<owner_user_id>/<asset_id>/<safe_filename>`

Under `ORCAST_RAW_PAYLOAD_BUCKET` (same bucket as model artifacts).
