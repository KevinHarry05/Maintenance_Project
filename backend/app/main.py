import json
import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler
from sqlalchemy import select, func

from app.core.api_gateway import gateway
from app.core.logger import get_logger
from app.core.rate_limit import limiter
from app.core.error_handler import setup_error_handlers
from app.core.security_headers_middleware import SecurityHeadersMiddleware
from app.config import settings
from app.database import Base, engine, AsyncSessionLocal
from app.routes import auth
from app.routes import users
from app.routes import admin
from app.routes import complaints
from app.routes import building
from app.routes import health
from app.routes import websocket_route
from app.routes import notifications
from app.routes import ai
from app.models import User, Building, Complaint, TicketLog, Notification, TokenBlacklist, EmailVerificationToken

app = FastAPI(
    title="SBMS Backend",
    description="Smart Building Management System Backend API",
    version="1.0.0",
)

# Ensure uploads directory exists and serve static files
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

logger = get_logger("sbms.api")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Phase 5.4: Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS (Phase 5.5: Update CORS Configuration)
cors_origins = settings.cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=bool(cors_origins),
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(complaints.router, tags=["Complaints"])
app.include_router(building.router, prefix="/buildings", tags=["Buildings"])
app.include_router(health.router)
app.include_router(websocket_route.router)
app.include_router(notifications.router)
app.include_router(ai.router)

# Phase 5.1: Setup Global Error Handlers
setup_error_handlers(app)


@app.on_event("startup")
async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("startup")
async def seed_default_buildings() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count()).select_from(Building))
        building_count = result.scalar_one()

        if building_count:
            return

        session.add_all([
            Building(name="Main Academic Block", block="A", floor_count=4),
            Building(name="Science Block", block="B", floor_count=3),
            Building(name="Administration Block", block="C", floor_count=2),
        ])
        await session.commit()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = gateway._request_id()
    request.state.request_id = request_id
    start_time = time.perf_counter()

    logger.info(
        "request.start request_id=%s method=%s path=%s",
        request_id,
        request.method,
        request.url.path,
    )

    try:
        if not gateway._is_public_path(request.url.path, request.method):
            gateway._check_rate_limit(request)
            gateway._validate_token(request)

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "request.end request_id=%s method=%s path=%s status=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            response.headers["X-Request-ID"] = request_id
            return response

        # Preserve CORS and other headers set by inner middlewares (e.g. CORSMiddleware).
        # Creating a new JSONResponse would otherwise silently drop Access-Control-Allow-Origin,
        # causing every cross-origin response to be rejected by the browser.
        _passthrough_headers = {
            "X-Request-ID": request_id,
        }
        _cors_names = (
            "access-control-allow-origin",
            "access-control-allow-credentials",
            "access-control-expose-headers",
            "access-control-allow-methods",
            "access-control-allow-headers",
            "vary",
        )
        for _h in _cors_names:
            _v = response.headers.get(_h)
            if _v:
                _passthrough_headers[_h] = _v

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            return Response(
                content=body,
                status_code=response.status_code,
                media_type=content_type,
                headers={**response.headers, "X-Request-ID": request_id},
            )

        if response.status_code >= 400:
            if isinstance(payload, dict) and "success" in payload and "request_id" in payload:
                return JSONResponse(
                    status_code=response.status_code,
                    content=payload,
                    headers=_passthrough_headers,
                )

            message = "Request failed"
            if isinstance(payload, dict):
                detail = payload.get("detail")
                if isinstance(detail, str):
                    message = detail
                elif detail is not None:
                    message = str(detail)

            return JSONResponse(
                status_code=response.status_code,
                content={
                    "success": False,
                    "data": payload,
                    "message": message,
                    "request_id": request_id,
                },
                headers=_passthrough_headers,
            )

        wrapped = gateway.normalize_success(request_id=request_id, data=payload)
        return JSONResponse(
            status_code=response.status_code,
            content=wrapped,
            headers=_passthrough_headers,
        )
    except Exception as exc:
        if hasattr(exc, "status_code") and hasattr(exc, "detail"):
            logger.warning(
                "request.fail request_id=%s method=%s path=%s status=%s detail=%s",
                request_id,
                request.method,
                request.url.path,
                exc.status_code,
                exc.detail,
            )
            return gateway.normalize_error(request_id, exc.status_code, str(exc.detail))

        logger.exception(
            "request.error request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )
        return gateway.normalize_error(request_id, 500, "Internal server error")


@app.get("/")
async def root():
    return {"message": "Smart Building Management API"}