from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import health, places, refuges, routes
from app.config import get_settings
from app.errors import ApiError
from app.schemas import ErrorDetail, ErrorResponse

settings = get_settings()

app = FastAPI(title="CalmPath API", version="1.0.0")

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
