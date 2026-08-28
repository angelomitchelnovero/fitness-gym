"""Admin reports endpoint — Phase 9."""

from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.reports import ReportsResponse
from app.services import reports_service

router = APIRouter()


@router.get(
    "",
    response_model=ReportsResponse,
    summary="[admin] Operational reports (revenue, retention, popular plans)",
)
def reports(
    period: Literal["day", "week", "month"] = Query(
        "week", description="Time range to summarize"
    ),
    bucket: Literal["day", "week"] = Query(
        "day", description="Bucket granularity (ignored for period=day)"
    ),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> ReportsResponse:
    payload = reports_service.build_reports(
        db, period=period, bucket_size=bucket
    )
    # Pydantic will coerce everything; round-trip via JSON for clean ISO.
    return ReportsResponse.model_validate(json.loads(json.dumps(payload)))
