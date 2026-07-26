# app/core/login_rate_limiter.py

from fastapi import Request, HTTPException, status
from redis import Redis
from redis.exceptions import RedisError
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Redis connection
redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)


class LoginRateLimitError(HTTPException):
    """Exception raised when login rate limit is exceeded"""
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
        self.retry_after = retry_after


class LoginRateLimiter:
    """Rate limiter specifically for login attempts with IP-based tracking"""
    
    def __init__(
        self,
        max_attempts: int = settings.LOGIN_RATE_LIMIT_PER_MINUTE,
        window_seconds: int = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    ):
        """
        Initialize the login rate limiter
        
        Args:
            max_attempts: Maximum number of failed login attempts allowed
            window_seconds: Time window in seconds for rate limiting
        """
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, handling proxies"""
        # Check for X-Forwarded-For header (common with proxies/load balancers)
        if x_forwarded_for := request.headers.get("X-Forwarded-For"):
            return x_forwarded_for.split(",")[0].strip()
        # Check for X-Real-IP header
        if x_real_ip := request.headers.get("X-Real-IP"):
            return x_real_ip
        # Fall back to client connection IP
        if request.client:
            return request.client.host
        return "unknown"
    
    def _get_rate_limit_key(self, client_ip: str) -> str:
        """Generate the Redis key for rate limiting"""
        return f"login_rate_limit:{client_ip}"
    
    def _get_success_key(self, client_ip: str) -> str:
        """Generate the Redis key for tracking successful login reset"""
        return f"login_success:{client_ip}"
    
    async def check_rate_limit(self, request: Request) -> None:
        """
        Check if the client has exceeded the login rate limit
        
        Args:
            request: FastAPI Request object
            
        Raises:
            LoginRateLimitError: If rate limit is exceeded
        """
        client_ip = self._get_client_ip(request)
        rate_limit_key = self._get_rate_limit_key(client_ip)
        
        try:
            # Get current attempt count
            attempt_count = redis_client.get(rate_limit_key)
            
            if attempt_count is not None:
                attempt_count = int(attempt_count)
                
                # Check if limit exceeded
                if attempt_count >= self.max_attempts:
                    ttl = redis_client.ttl(rate_limit_key)
                    retry_after = ttl if ttl > 0 else self.window_seconds
                    logger.warning(
                        f"Login rate limit exceeded for IP: {client_ip}, "
                        f"attempts: {attempt_count}/{self.max_attempts}"
                    )
                    raise LoginRateLimitError(retry_after=retry_after)
        
        except RedisError as e:
            # Graceful degradation: log warning but allow login if Redis unavailable
            logger.warning(
                f"Redis error during login rate limit check for IP {client_ip}: {str(e)}. "
                f"Allowing login (graceful degradation)"
            )
    
    async def record_failed_attempt(self, request: Request) -> None:
        """
        Record a failed login attempt for the client
        
        Args:
            request: FastAPI Request object
        """
        client_ip = self._get_client_ip(request)
        rate_limit_key = self._get_rate_limit_key(client_ip)
        
        try:
            # Increment attempt counter with TTL
            pipe = redis_client.pipeline()
            pipe.incr(rate_limit_key)
            pipe.expire(rate_limit_key, self.window_seconds)
            pipe.execute()
            
            attempt_count = redis_client.get(rate_limit_key)
            logger.info(
                f"Recorded failed login attempt for IP: {client_ip}, "
                f"attempts: {attempt_count}/{self.max_attempts}"
            )
        
        except RedisError as e:
            logger.warning(
                f"Redis error while recording failed login attempt for IP {client_ip}: {str(e)}"
            )
    
    async def reset_limit(self, request: Request) -> None:
        """
        Reset the rate limit counter after successful login
        
        Args:
            request: FastAPI Request object
        """
        client_ip = self._get_client_ip(request)
        rate_limit_key = self._get_rate_limit_key(client_ip)
        
        try:
            # Delete the rate limit key and set success marker
            pipe = redis_client.pipeline()
            pipe.delete(rate_limit_key)
            # Mark successful login (optional, for audit purposes)
            pipe.setex(self._get_success_key(client_ip), 3600, "success")
            pipe.execute()
            
            logger.info(f"Reset login rate limit for IP: {client_ip}")
        
        except RedisError as e:
            logger.warning(
                f"Redis error while resetting login rate limit for IP {client_ip}: {str(e)}"
            )


# Global instance of login rate limiter
login_rate_limiter = LoginRateLimiter()
