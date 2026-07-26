import time
import uuid
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from redis.exceptions import RedisError

from app.config import settings
from app.core.logger import get_logger
from app.utils.cache import redis_cache


class APIGateway:
    def __init__(self):
        self.global_limit_per_minute = settings.GLOBAL_RATE_LIMIT_PER_MINUTE
        self.logger = get_logger("sbms.gateway")

    def _request_id(self) -> str:
        return str(uuid.uuid4())

    def _is_public_path(self, path: str, method: str = "") -> bool:
        # Always pass OPTIONS through — these are CORS preflight requests handled by CORSMiddleware
        if method.upper() == "OPTIONS":
            return True
        return path in {"/", "/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc", "/health"} or path.startswith("/auth") or path.startswith("/ws")

    def _validate_token(self, request: Request) -> None:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing bearer token")

        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") != "access":
                raise HTTPException(status_code=401, detail="Invalid token type")
        except JWTError as exc:
            raise HTTPException(status_code=401, detail="Invalid token") from exc

    def _check_rate_limit(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        bucket = int(time.time() // 60)
        cache_key = f"gateway:ratelimit:{client_ip}:{bucket}"

        try:
            current = redis_cache.incr(cache_key)
            if current == 1:
                redis_cache.expire(cache_key, 70)
        except RedisError:
            self.logger.warning("rate_limit.redis_unavailable path=%s ip=%s", request.url.path, client_ip)
            return

        if current > self.global_limit_per_minute:
            raise HTTPException(status_code=429, detail="Too many requests")

    def normalize_error(self, request_id: str, status_code: int, message: str) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "data": None,
                "message": message,
                "request_id": request_id,
            },
        )

    def normalize_success(self, request_id: str, data: Any, message: str = "Request successful") -> dict:
        return {
            "success": True,
            "data": data,
            "message": message,
            "request_id": request_id,
        }


gateway = APIGateway()
