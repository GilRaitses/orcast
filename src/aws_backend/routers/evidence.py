"""Evidence asset upload, listing, and management for user-owned media."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ..auth import ReviewerIdentity, require_signed_in
from ..config import settings

router = APIRouter()

_MAX_BYTES = 25 * 1024 * 1024  # 25 MB
_EVIDENCE_PREFIX = "evidence"


def _safe_filename(name: str) -> str:
    """Strip directory traversal, null bytes, and non-ASCII."""
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = re.sub(r"[^\w.\-]", "_", name)
    name = re.sub(r"\.{2,}", "_", name)
    return name[:200] or "upload"


def _infer_kind(content_type: str | None) -> str:
    ct = (content_type or "").lower()
    if ct.startswith("image/"):
        return "image"
    if ct.startswith("audio/"):
        return "audio"
    return "other"


def _s3_client():
    return boto3.client("s3", region_name=settings.aws_region)


def _asset_to_dict(asset: dict) -> dict:
    return asset


def _build_asset(
    *,
    owner_user_id: str,
    kind: str,
    filename: str,
    content_type: str,
    size_bytes: int,
    storage_uri: str,
    caption: Optional[str] = None,
) -> dict:
    return {
        "id": f"asset_{uuid4().hex[:16]}",
        "owner_user_id": owner_user_id,
        "kind": kind,
        "filename": filename,
        "content_type": content_type,
        "size_bytes": size_bytes,
        "storage_uri": storage_uri,
        "caption": caption,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "linked_to": {
            "journal_entry_id": None,
            "community_submission_id": None,
        },
    }


@router.post("/api/evidence/assets")
async def upload_evidence_asset(
    file: UploadFile = File(...),
    kind: Optional[str] = Form(default=None),
    caption: Optional[str] = Form(default=None),
    identity: ReviewerIdentity = Depends(require_signed_in),
) -> Dict[str, Any]:
    """Upload a media file (image or audio) as evidence for a sighting report."""
    # Read and validate
    data = await file.read()
    if len(data) > _MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum is {_MAX_BYTES // (1024 * 1024)} MB.",
        )
    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")

    content_type = file.content_type or "application/octet-stream"
    effective_kind = kind if kind in {"image", "audio", "other"} else _infer_kind(content_type)
    safe_name = _safe_filename(file.filename or "upload")
    owner_id = identity.reviewer_id or "anon"
    asset_id = f"asset_{uuid4().hex[:16]}"
    s3_key = f"{_EVIDENCE_PREFIX}/{owner_id}/{asset_id}/{safe_name}"

    storage_uri = f"s3://{settings.raw_payload_bucket}/{s3_key}"

    if settings.storage_backend.lower() == "aws":
        try:
            s3 = _s3_client()
            s3.put_object(
                Bucket=settings.raw_payload_bucket,
                Key=s3_key,
                Body=data,
                ContentType=content_type,
                Metadata={
                    "owner-user-id": owner_id,
                    "asset-id": asset_id,
                    "kind": effective_kind,
                },
            )
        except (BotoCoreError, ClientError) as exc:
            raise HTTPException(status_code=502, detail=f"Storage error: {exc}") from exc
    else:
        # Local / memory mode — skip S3 write; URI is still returned
        storage_uri = f"local://{s3_key}"

    if caption and len(caption) > 500:
        caption = caption[:500]

    asset = _build_asset(
        owner_user_id=owner_id,
        kind=effective_kind,
        filename=safe_name,
        content_type=content_type,
        size_bytes=len(data),
        storage_uri=storage_uri,
        caption=caption,
    )
    # Override id to match what was used for the S3 key
    asset["id"] = asset_id
    return {"status": "success", "asset": asset}


@router.get("/api/evidence/assets")
def list_evidence_assets(
    identity: ReviewerIdentity = Depends(require_signed_in),
) -> Dict[str, Any]:
    """List uploaded evidence assets for the current user.

    In the AWS backend this would query a DynamoDB index; for now we list S3
    objects under the user's evidence prefix.  Returns an empty list in
    local/memory mode.
    """
    owner_id = identity.reviewer_id or "anon"
    assets: List[dict] = []

    if settings.storage_backend.lower() == "aws":
        try:
            s3 = _s3_client()
            prefix = f"{_EVIDENCE_PREFIX}/{owner_id}/"
            paginator = s3.get_paginator("list_objects_v2")
            seen_asset_ids: set = set()
            for page in paginator.paginate(Bucket=settings.raw_payload_bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    key: str = obj["Key"]
                    parts = key.split("/")
                    # evidence/{owner}/{asset_id}/{filename}
                    if len(parts) < 4:
                        continue
                    aid = parts[2]
                    fname = parts[3]
                    if aid in seen_asset_ids:
                        continue
                    seen_asset_ids.add(aid)
                    try:
                        head = s3.head_object(Bucket=settings.raw_payload_bucket, Key=key)
                        meta = head.get("Metadata", {})
                        ct = head.get("ContentType", "application/octet-stream")
                        assets.append(
                            _build_asset(
                                owner_user_id=owner_id,
                                kind=meta.get("kind", _infer_kind(ct)),
                                filename=fname,
                                content_type=ct,
                                size_bytes=obj.get("Size", 0),
                                storage_uri=f"s3://{settings.raw_payload_bucket}/{key}",
                            )
                            | {"id": aid, "created_at": obj["LastModified"].isoformat()}
                        )
                    except (BotoCoreError, ClientError):
                        pass
        except (BotoCoreError, ClientError):
            pass

    return {"status": "success", "total_count": len(assets), "assets": assets}


@router.delete("/api/evidence/assets/{asset_id}")
def delete_evidence_asset(
    asset_id: str,
    identity: ReviewerIdentity = Depends(require_signed_in),
) -> Dict[str, Any]:
    """Unlink an evidence asset.

    In this wave we tombstone the S3 object metadata tag rather than deleting
    the object, so recovery is still possible.  Cross-user deletion is rejected
    by checking the owner prefix.
    """
    owner_id = identity.reviewer_id or "anon"
    if settings.storage_backend.lower() == "aws":
        try:
            s3 = _s3_client()
            prefix = f"{_EVIDENCE_PREFIX}/{owner_id}/{asset_id}/"
            resp = s3.list_objects_v2(Bucket=settings.raw_payload_bucket, Prefix=prefix, MaxKeys=1)
            objects = resp.get("Contents", [])
            if not objects:
                raise HTTPException(status_code=404, detail="Asset not found or not yours.")
            key = objects[0]["Key"]
            s3.put_object_tagging(
                Bucket=settings.raw_payload_bucket,
                Key=key,
                Tagging={"TagSet": [{"Key": "tombstoned", "Value": "true"}]},
            )
        except (BotoCoreError, ClientError) as exc:
            raise HTTPException(status_code=502, detail=f"Storage error: {exc}") from exc

    return {"status": "success", "asset_id": asset_id, "tombstoned": True}
