from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.routes import auth, shipments, admin, delivery

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Courier and logistics REST API",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(shipments.router, prefix=settings.api_v1_prefix)
app.include_router(admin.router, prefix=settings.api_v1_prefix)
app.include_router(delivery.router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["System"])
def health():
    return {"success": True, "status": "ok", "service": "courier-api"}


@app.exception_handler(RequestValidationError)
async def validation_error(_, exc):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation error",
            "error": "VALIDATION_ERROR",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def generic_error(_, exc):
    if settings.app_env == "development":
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "error": "INTERNAL_ERROR",
                "details": str(exc),
            },
        )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": "INTERNAL_ERROR",
        },
    )
