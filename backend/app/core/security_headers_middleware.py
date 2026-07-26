"""Security Headers Middleware - Add security headers to all responses.

Adds headers to prevent common web vulnerabilities:
- X-Content-Type-Options: nosniff - Prevent MIME type sniffing
- X-Frame-Options: DENY - Prevent clickjacking attacks
- X-XSS-Protection: 1; mode=block - Enable browser XSS protection
- Strict-Transport-Security: HSTS - Enforce HTTPS
- X-Powered-By: Remove to hide framework info

Requirements: 8.12
"""

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.config import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all HTTP responses.
    
    Requirements: 8.12
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and add security headers to response.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response with security headers added
        """
        # Get response from next handler
        response = await call_next(request)
        
        # Add security headers
        # 1. X-Content-Type-Options: nosniff
        # Prevents browser from MIME-type sniffing (e.g., treating .jpg as .html)
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # 2. X-Frame-Options: DENY
        # Prevents embedding in <iframe> (clickjacking protection)
        response.headers["X-Frame-Options"] = "DENY"
        
        # 3. X-XSS-Protection: 1; mode=block
        # Enable browser's XSS filter and block page on detection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # 4. Strict-Transport-Security (HSTS)
        # Force HTTPS for all future requests (1 year + subdomains)
        # Only add if running over HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # 5. Remove X-Powered-By header to hide framework info
        # Don't advertise that we're using FastAPI/Python
        response.headers.pop("X-Powered-By", None)
        
        # 6. Content-Security-Policy (optional, can be strict)
        # For API-only server, we can use a restrictive policy
        # response.headers["Content-Security-Policy"] = "default-src 'none'"
        
        # 7. Referrer-Policy
        # Don't send referrer to third-party sites
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 8. Permissions-Policy (formerly Feature-Policy)
        # Disable APIs that aren't needed
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response
