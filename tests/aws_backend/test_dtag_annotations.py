"""Tests for the DTAG annotation write API (studio-live-persistence, STU-B).

Offline and deterministic: the default memory storage backend is used, so no
boto3 or AWS is touched. A fresh store is installed per test for isolation.
"""

import os
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.aws_backend.annotations.store import (
    AwsAnnotationStore,
    MemoryAnnotationStore,
    StoredAnnotation,
)
from src.aws_backend.main import app
from src.aws_backend.routers import annotations as ann
from tests.aws_backend.conftest_governance import governance_headers

client = TestClient(app)

EXAMPLE_ID = "cascadia_2010_k33_test"


@pytest.fixture(autouse=True)
def fresh_store():
    """Isolate each test: a clean memory store and empty rate buckets."""
    ann._store = ann.build_annotation_store()
    ann._write_buckets.clear()
    yield


def _valid_body(start=0, end=100, behavior="foraging_dive", **over):
    body = {
        "deployment_id": EXAMPLE_ID,
        "target": {"kind": "dive", "dive_id": 1, "start_sample": start, "end_sample": end},
        "behavior": behavior,
        "state": "active",
        "confidence": 0.8,
        "notes": "deep foraging dive",
        "provenance": {
            "source": "community",
            "annotator_id": "client-claimed-id",
            "annotator_role": "community",
            "method": "manual",
            "dataset": "client-claimed-dataset",
            "h5_refs": ["depth/values"],
            "license_status": "client-claimed-license",
            "tool": "client-claimed-tool",
        },
    }
    body.update(over)
    return body


# --- round-trip create -> list -> get ---------------------------------------


def test_create_list_get_round_trip():
    created = client.post(
        "/api/dtag/annotations", json=_valid_body(), headers=governance_headers()
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["status"] == "created"
    assert body["simulated"] is True
    ann_id = body["id"]
    assert ann_id

    listed = client.get(
        f"/api/dtag/annotations?deployment_id={EXAMPLE_ID}", headers=governance_headers()
    )
    assert listed.status_code == 200
    rows = listed.json()
    # The client parses a bare array of full Annotation objects, not an envelope.
    assert isinstance(rows, list)
    assert len(rows) == 1
    assert rows[0]["id"] == ann_id

    got = client.get(f"/api/dtag/annotations/{ann_id}", headers=governance_headers())
    assert got.status_code == 200
    one = got.json()
    assert one["id"] == ann_id
    assert one["behavior"] == "foraging_dive"
    assert one["target"]["kind"] == "dive"
    assert one["target"]["start_sample"] == 0
    assert one["target"]["end_sample"] == 100
    # Full 10-field provenance, with deployment_id moved in and a server created_at.
    prov = one["provenance"]
    for field in (
        "dataset",
        "deployment_id",
        "source",
        "annotator_id",
        "annotator_role",
        "method",
        "h5_refs",
        "license_status",
        "tool",
        "created_at",
    ):
        assert field in prov
    assert prov["deployment_id"] == EXAMPLE_ID
    assert prov["created_at"]
    assert one["simulated"] is True


def test_get_missing_annotation_is_404():
    resp = client.get("/api/dtag/annotations/does_not_exist", headers=governance_headers())
    assert resp.status_code == 404


# --- auth (P0 auth bypass) ---------------------------------------------------


def test_post_without_reviewer_is_rejected():
    resp = client.post("/api/dtag/annotations", json=_valid_body())
    assert resp.status_code == 401


def test_list_without_reviewer_is_rejected():
    resp = client.get(f"/api/dtag/annotations?deployment_id={EXAMPLE_ID}")
    assert resp.status_code == 401


def test_direct_keyless_call_rejected_when_api_key_configured(monkeypatch):
    """Router-level require_api_key closes the direct-backend bypass: a forged
    reviewer header without the server key is rejected."""
    monkeypatch.setenv("ORCAST_API_KEY", "studio-key")
    local = TestClient(app)
    # Reviewer headers but no X-ORCAST-Key and no trusted proxy marker.
    resp = local.post(
        "/api/dtag/annotations",
        json=_valid_body(),
        headers={
            "X-ORCAST-Reviewer-Id": "attacker_forged",
            "X-ORCAST-Reviewer-Email": "attacker@example.com",
            "X-ORCAST-Reviewer-Role": "reviewer",
        },
    )
    assert resp.status_code == 401
    # With the server key plus the trusted-proxy marker, the same call is accepted.
    ok = local.post(
        "/api/dtag/annotations",
        json=_valid_body(),
        headers=governance_headers(),
    )
    assert ok.status_code == 200, ok.text


# --- provenance tamper (P0 identity stamping, P1 authority pinning) ----------


def test_provenance_is_server_stamped_not_from_body():
    resp = client.post(
        "/api/dtag/annotations",
        json=_valid_body(
            provenance={
                "source": "expert",
                "annotator_id": "spoofed-expert-id",
                "annotator_role": "lead-scientist",
                "method": "manual",
                "dataset": "spoofed-dataset",
                "h5_refs": ["evil/ref", "another"],
                "license_status": "public-domain",
                "tool": "spoofed-tool",
            }
        ),
        headers=governance_headers(reviewer_id="user_real", reviewer_email="real@example.com"),
    )
    assert resp.status_code == 200, resp.text
    ann_id = resp.json()["id"]
    one = client.get(f"/api/dtag/annotations/{ann_id}", headers=governance_headers()).json()
    prov = one["provenance"]
    # Identity is the verified reviewer id, not the spoofed body, never the email.
    assert prov["annotator_id"] == "user_real"
    assert prov["annotator_id"] != "spoofed-expert-id"
    # source pinned to community; the body's "expert" claim is dropped.
    assert prov["source"] == "community"
    # dataset, license, tool pinned server-side.
    assert prov["dataset"] == EXAMPLE_ID
    assert prov["license_status"] == "simulated-example"
    assert prov["tool"] == "bss-annotation-studio-v1"
    # h5_refs pinned to the server dive set, not the client-injected values.
    assert "evil/ref" not in prov["h5_refs"]
    assert prov["h5_refs"] == [
        "depth/values",
        "dives/dive_indices",
        "analysis/animal_frame_metrics/odba",
    ]


def test_source_defaults_to_community():
    resp = client.post(
        "/api/dtag/annotations",
        json=_valid_body(provenance={"source": "expert", "method": "manual"}),
        headers=governance_headers(reviewer_role="reviewer"),
    )
    assert resp.status_code == 200, resp.text
    ann_id = resp.json()["id"]
    one = client.get(f"/api/dtag/annotations/{ann_id}", headers=governance_headers()).json()
    # No recognized expert role and a body claim of "expert" are both ignored.
    assert one["provenance"]["source"] == "community"


def test_source_elevates_to_expert_on_recognized_role():
    resp = client.post(
        "/api/dtag/annotations",
        json=_valid_body(provenance={"source": "community", "method": "manual"}),
        headers=governance_headers(reviewer_role="researcher"),
    )
    assert resp.status_code == 200, resp.text
    ann_id = resp.json()["id"]
    one = client.get(f"/api/dtag/annotations/{ann_id}", headers=governance_headers()).json()
    # A recognized expert/researcher role tier elevates source server-side.
    assert one["provenance"]["source"] == "expert"


def test_reviewer_email_never_returned():
    resp = client.post(
        "/api/dtag/annotations",
        json=_valid_body(),
        headers=governance_headers(reviewer_id="user_pii", reviewer_email="secret@example.com"),
    )
    ann_id = resp.json()["id"]
    raw = client.get(f"/api/dtag/annotations/{ann_id}", headers=governance_headers()).text
    assert "secret@example.com" not in raw
    assert "reviewer_email" not in raw
    listed = client.get(
        f"/api/dtag/annotations?deployment_id={EXAMPLE_ID}", headers=governance_headers()
    ).text
    assert "secret@example.com" not in listed


# --- honesty label (P1 simulated stamping) -----------------------------------


def test_unknown_deployment_is_rejected():
    resp = client.post(
        "/api/dtag/annotations",
        json=_valid_body(deployment_id="not_a_real_deployment"),
        headers=governance_headers(),
    )
    assert resp.status_code == 404


def test_simulated_label_stamped_from_record():
    resp = client.post("/api/dtag/annotations", json=_valid_body(), headers=governance_headers())
    assert resp.json()["simulated"] is True
    ann_id = resp.json()["id"]
    one = client.get(f"/api/dtag/annotations/{ann_id}", headers=governance_headers()).json()
    assert one["simulated"] is True
    assert one["provenance"]["license_status"] == "simulated-example"


# --- input validation (P1 injection caps / enum allow-lists) -----------------


def test_end_before_start_is_422():
    resp = client.post(
        "/api/dtag/annotations",
        json=_valid_body(start=500, end=100),
        headers=governance_headers(),
    )
    assert resp.status_code == 422


def test_invalid_behavior_is_422():
    resp = client.post(
        "/api/dtag/annotations",
        json=_valid_body(behavior="<script>alert(1)</script>"),
        headers=governance_headers(),
    )
    assert resp.status_code == 422


def test_invalid_target_kind_is_422():
    body = _valid_body()
    body["target"]["kind"] = "galaxy"
    resp = client.post("/api/dtag/annotations", json=body, headers=governance_headers())
    assert resp.status_code == 422


def test_confidence_out_of_range_is_422():
    resp = client.post(
        "/api/dtag/annotations",
        json=_valid_body(confidence=5.0),
        headers=governance_headers(),
    )
    assert resp.status_code == 422


def test_notes_over_cap_is_422():
    resp = client.post(
        "/api/dtag/annotations",
        json=_valid_body(notes="x" * 5000),
        headers=governance_headers(),
    )
    assert resp.status_code == 422


# --- idempotency (content-key dedup) -----------------------------------------


def test_duplicate_post_is_idempotent():
    first = client.post("/api/dtag/annotations", json=_valid_body(), headers=governance_headers())
    second = client.post("/api/dtag/annotations", json=_valid_body(), headers=governance_headers())
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["status"] == "duplicate"
    rows = client.get(
        f"/api/dtag/annotations?deployment_id={EXAMPLE_ID}", headers=governance_headers()
    ).json()
    assert len(rows) == 1


def test_distinct_reviewers_are_not_deduped():
    a = client.post(
        "/api/dtag/annotations",
        json=_valid_body(),
        headers=governance_headers(reviewer_id="user_a"),
    )
    b = client.post(
        "/api/dtag/annotations",
        json=_valid_body(),
        headers=governance_headers(reviewer_id="user_b"),
    )
    assert a.json()["id"] != b.json()["id"]
    rows = client.get(
        f"/api/dtag/annotations?deployment_id={EXAMPLE_ID}", headers=governance_headers()
    ).json()
    assert len(rows) == 2


# --- write rate limit keyed on reviewer id -----------------------------------


def test_write_rate_limit_per_reviewer():
    # Distinct content each call so dedup does not absorb them; same reviewer.
    statuses = []
    for i in range(ann._WRITE_RATE_LIMIT + 2):
        resp = client.post(
            "/api/dtag/annotations",
            json=_valid_body(start=i * 10, end=i * 10 + 5, behavior=f"dive{i}"),
            headers=governance_headers(reviewer_id="busy_user"),
        )
        statuses.append(resp.status_code)
    assert 429 in statuses


# --- store unit tests --------------------------------------------------------


def _record(ann_id="a1", dedup="k1", deployment=EXAMPLE_ID):
    return StoredAnnotation(
        id=ann_id,
        deployment_id=deployment,
        dedup_key=dedup,
        simulated=True,
        target={"kind": "dive", "dive_id": 1, "start_sample": 0, "end_sample": 10},
        behavior="foraging_dive",
        provenance={"deployment_id": deployment, "created_at": "2026-01-01T00:00:00+00:00"},
        created_at="2026-01-01T00:00:00+00:00",
    )


def test_memory_store_dedups_on_key():
    store = MemoryAnnotationStore()
    first, created_first = store.create(_record(ann_id="a1", dedup="same"))
    second, created_second = store.create(_record(ann_id="a2", dedup="same"))
    assert created_first is True
    assert created_second is False
    assert second.id == "a1"
    assert store.get("a1") is not None
    assert store.get("a2") is None
    assert len(store.list_for_deployment(EXAMPLE_ID)) == 1


def test_aws_store_create_is_content_key_write_once():
    """The AWS impl must guard the put with attribute_not_exists(sk)."""
    store = AwsAnnotationStore.__new__(AwsAnnotationStore)  # bypass boto3 __init__
    from src.aws_backend.storage import _decimalize, model_to_dict

    store._decimalize = _decimalize
    store._model_to_dict = model_to_dict
    store.table = MagicMock()
    store.create(_record())
    _, kwargs = store.table.put_item.call_args
    assert kwargs["ConditionExpression"] == "attribute_not_exists(sk)"
    item = kwargs["Item"]
    assert item["pk"] == EXAMPLE_ID
    assert item["sk"] == "annotation#k1"
