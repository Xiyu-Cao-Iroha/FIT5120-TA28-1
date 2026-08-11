import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1 import health, places, refuges, routes
from app.config import get_settings
from app.db import SessionLocal
from app.errors import ApiError
from app.schemas import ErrorDetail, ErrorResponse
from app.seed import refresh_demo_scenario_freshness

logger = logging.getLogger(__name__)
settings = get_settings()

# Comfortably under settings.default_max_observation_age_minutes (30 by
# default) so the periodic refresh always lands well before seeded demo
# data would otherwise age out - see refresh_demo_scenario_freshness.
DEMO_FRESHNESS_REFRESH_INTERVAL_SECONDS = 600


def _refresh_demo_freshness_once() -> None:
    db = SessionLocal()
    try:
        refresh_demo_scenario_freshness(db)
    except SQLAlchemyError:
        # Runs before migrations on a brand-new database (pedestrian_sensors
        # doesn't exist yet) - this is a best-effort freshness nicety, not a
        # critical path, so it must never block app startup or crash the
        # whole process. It'll succeed once the schema exists.
        logger.warning("Demo scenario freshness refresh skipped (schema not ready yet?)", exc_info=True)
    finally:
        db.close()


async def _demo_freshness_loop() -> None:
    while True:
        await asyncio.sleep(DEMO_FRESHNESS_REFRESH_INTERVAL_SECONDS)
        await asyncio.to_thread(_refresh_demo_freshness_once)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(_refresh_demo_freshness_once)
    task = asyncio.create_task(_demo_freshness_loop())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="CalmPath API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=ErrorDetail(code=exc.code, message=exc.message)).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Never leak stack traces, SQL, or credentials (section 9.1 / 14.1).
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(code="INTERNAL_ERROR", message="An unexpected error occurred.")
        ).model_dump(),
    )


app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(routes.router, prefix="/api/v1", tags=["routes"])
app.include_router(refuges.router, prefix="/api/v1", tags=["refuges"])
app.include_router(places.router, prefix="/api/v1", tags=["places"])
