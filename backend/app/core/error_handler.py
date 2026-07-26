"""Global Error Handler - Intercept and normalize all exceptions.

This handler provides:
- Consistent error response format
- Secure error message handling (no sensitive data leaks)
- Request ID tracking for support
- Comprehensive logging of errors
- Differentiated handling for different error types

Requirements: 8.3, 8.4
"""

import logging
import uuid
from typing import Any, Callable
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException, RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response model."""
    
    @staticmethod
    def create(
        success: bool = False,
        message: str = "An error occurred",
        request_id: str = None,
        details: dict = None,
        status_code: int = 500
    ) -> dict[str, Any]:
        """
        Create standardized error response.
        
        Args:
            success: Whether operation succeeded
            message: Human-readable error message
            request_id: Request tracking ID
            details: Additional error details (if appropriate to share)
            status_code: HTTP status code
            
        Returns:
            Dictionary with standardized error response
        """
        response = {
            "success": success,
            "message": message,
        }
        
        if request_id:
            response["request_id"] = request_id
        
        if details and status_code < 500:  # Only include details for client errors
            response["details"] = details
        
        return response


async def exception_handler_500(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle unhandled exceptions (500 errors).
    
    Requirements: 8.3, 8.4
    
    Logs full error details but returns generic message to client.
    This prevents information disclosure of internal implementation details.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    logger.error(
        "Unhandled exception",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        exception_type=type(exc).__name__,
        exception_msg=str(exc),
        exc_info=True  # Include full stack trace
    )
    
    response = ErrorResponse.create(
        success=False,
        message="Internal server error",
        request_id=request_id,
        status_code=500
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response
    )


async def exception_handler_validation(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle validation errors (422 Unprocessable Entity).
    
    Requirements: 8.3, 8.4
    
    Returns validation errors to client (safe to expose schema violations).
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    # Extract validation error details
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error.get("loc", [])[1:]),
            "message": error.get("msg", "Validation error")
        })
    
    logger.warning(
        "Validation error",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        error_count=len(errors)
    )
    
    response = ErrorResponse.create(
        success=False,
        message="Request validation failed",
        request_id=request_id,
        details={"validation_errors": errors},
        status_code=422
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response
    )


async def exception_handler_http(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """
    Handle HTTP exceptions (401, 403, 404, etc.).
    
    Requirements: 8.3, 8.4
    
    Provides generic error messages for auth/authz errors.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    # Generic messages for sensitive errors
    sensitive_status_codes = {
        status.HTTP_401_UNAUTHORIZED: "Authorization credentials are missing or invalid",
        status.HTTP_403_FORBIDDEN: "User does not have permission to access this resource",
    }
    
    # Use generic message for sensitive errors, otherwise use provided detail
    if exc.status_code in sensitive_status_codes:
        message = sensitive_status_codes[exc.status_code]
    else:
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    
    log_level = "warning" if exc.status_code >= 400 else "info"
    
    if log_level == "warning":
        logger.warning(
            "HTTP exception",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=exc.status_code,
            message=message
        )
    
    response = ErrorResponse.create(
        success=False,
        message=message,
        request_id=request_id,
        status_code=exc.status_code
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response
    )


async def exception_handler_database(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle database errors.
    
    Requirements: 8.3, 8.4
    
    Logs full SQL error but returns generic message to client.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    logger.error(
        "Database error",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        exception_type=type(exc).__name__,
        exception_msg=str(exc)[:200],  # Truncate long error messages
        exc_info=True
    )
    
    response = ErrorResponse.create(
        success=False,
        message="Database operation failed",
        request_id=request_id,
        status_code=500
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response
    )


def setup_error_handlers(app: FastAPI) -> None:
    """
    Register all error handlers with FastAPI app.
    
    Must be called after app creation but before running.
    
    Args:
        app: FastAPI application instance
    """
    # Register exception handlers in order of specificity
    # More specific handlers should be registered after generic ones
    
    app.add_exception_handler(
        HTTPException,
        exception_handler_http
    )
    
    app.add_exception_handler(
        StarletteHTTPException,
        exception_handler_http
    )
    
    app.add_exception_handler(
        RequestValidationError,
        exception_handler_validation
    )
    
    app.add_exception_handler(
        SQLAlchemyError,
        exception_handler_database
    )
    
    app.add_exception_handler(
        Exception,
        exception_handler_500
    )
    
    logger.info("Error handlers registered")
