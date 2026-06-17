from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import Response

from ..models import ProbabilityReportRequest
from ..reports import build_probability_report
from ..state import ensure_hotspots, get_latest_ingestion_run, storage
from ..storage import model_to_dict

router = APIRouter()


def _csv_escape(value: str) -> str:
    if any(char in value for char in [",", '"', "\n"]):
        return '"' + value.replace('"', '""') + '"'
    return value


@router.post("/api/reports/probability")
def probability_report(request: ProbabilityReportRequest) -> Dict[str, Any]:
    sightings = storage.list_sightings(limit=10_000)
    hotspots = ensure_hotspots()
    report = build_probability_report(request, sightings, hotspots, get_latest_ingestion_run())
    storage.put_report(report)
    return {"status": "success", "report": model_to_dict(report)}


@router.get("/api/reports/{report_id}.csv")
def get_report_csv(report_id: str) -> Response:
    report = storage.get_report(report_id)
    if not report:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Report not found")
    rows = [
        "hotspot_id,name,center_latitude,center_longitude,radius_km,probability,confidence,detection_count,validated_detection_count,source_count"
    ]
    for hotspot in report.hotspots:
        rows.append(
            ",".join(
                [
                    hotspot.hotspot_id,
                    _csv_escape(hotspot.name),
                    str(hotspot.center_latitude),
                    str(hotspot.center_longitude),
                    str(hotspot.radius_km),
                    str(hotspot.probability),
                    str(hotspot.confidence),
                    str(hotspot.detection_count),
                    str(hotspot.validated_detection_count),
                    str(hotspot.source_count),
                ]
            )
        )
    return Response(
        "\n".join(rows) + "\n",
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={report_id}.csv"},
    )


@router.get("/api/reports/{report_id}")
def get_report(report_id: str) -> Dict[str, Any]:
    report = storage.get_report(report_id)
    if not report:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Report not found")
    return {"status": "success", "report": model_to_dict(report)}
