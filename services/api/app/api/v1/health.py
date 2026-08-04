from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import PedestrianObservation
from app.schemas import HealthComponent, HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
        db_status = HealthComponent(status="ok")
    except Exception as exc:  # pragma: no cover - defensive, exercised only if DB is down
        db_status = HealthComponent(status="error", detail=str(exc))

    latest = db.execute(
        select(PedestrianObservation.observed_at).order_by(PedestrianObservation.observed_at.desc()).limit(1)
    ).scalar()

    if latest is None:
        freshness = HealthComponent(status="unavailable", detail="No pedestrian observations ingested yet.")
    elif datetime.now(timezone.utc) - latest <= timedelta(minutes=30):
        freshness = HealthComponent(status="ok", detail=f"Latest observation at {latest.isoformat()}")
    else:
        freshness = HealthComponent(status="stale", detail=f"Latest observation at {latest.isoformat()}")

    overall = "ok" if db_status.status == "ok" and freshness.status == "ok" else "degraded"
    return HealthResponse(
        status=overall,
        api=HealthComponent(status="ok"),
        database=db_status,
        data_freshness=freshness,
    )
