"""
Common Error Handling for Microservices

Standardizes error responses and handling across all services.
"""

import time
from typing import Dict, Any, Optional, Union
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.requests import Request

from .logger import CustomLogger


class ServiceError(Exception):
    """Base exception for service errors"""

    def __init__(
        self, message: str, error_code: str = None, details: Dict[str, Any] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ValidationError(ServiceError):
    """Validation error"""

    pass


class DatabaseError(ServiceError):
    """Database operation error"""

    pass


class ModelError(ServiceError):
    """Model/ML operation error"""

    pass


class ExternalServiceError(ServiceError):
    """External service error"""

    pass


def create_error_response(
    error: Union[ServiceError, Exception],
    status_code: int = 500,
    request_id: Optional[str] = None,
    include_traceback: bool = False,
) -> Dict[str, Any]:
    """Create standardized error response"""

    error_response = {
        "error": {
            "message": str(error),
            "type": error.__class__.__name__,
            "timestamp": time.time(),
            "request_id": request_id,
        }
    }

    # Add error code if available
    if hasattr(error, "error_code") and error.error_code:
        error_response["error"]["code"] = error.error_code

    # Add details if available
    if hasattr(error, "details") and error.details:
        error_response["error"]["details"] = error.details

    # Add traceback in development
    if include_traceback:
        import traceback

        error_response["error"]["traceback"] = traceback.format_exc()

    return error_response


def handle_service_error(
    error: Exception, logger: CustomLogger, request: Optional[Request] = None
) -> JSONResponse:
    """Handle service errors and return appropriate response"""

    request_id = None
    if request:
        request_id = request.headers.get("X-Request-ID")

    # Log the error
    logger.error(f"Service error: {error}", exc_info=True)

    # Determine status code and response
    if isinstance(error, ValidationError):
        status_code = status.HTTP_400_BAD_REQUEST
        error_response = create_error_response(error, status_code, request_id)

    elif isinstance(error, DatabaseError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        error_response = create_error_response(error, status_code, request_id)

    elif isinstance(error, ModelError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        error_response = create_error_response(error, status_code, request_id)

    elif isinstance(error, ExternalServiceError):
        status_code = status.HTTP_502_BAD_GATEWAY
        error_response = create_error_response(error, status_code, request_id)

    elif isinstance(error, HTTPException):
        # FastAPI HTTP exceptions
        status_code = error.status_code
        error_response = create_error_response(error, status_code, request_id)

    else:
        # Generic errors
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_response = create_error_response(error, status_code, request_id)

    return JSONResponse(status_code=status_code, content=error_response)


def create_http_exception(
    message: str,
    status_code: int = 500,
    error_code: str = None,
    details: Dict[str, Any] = None,
) -> HTTPException:
    """Create a standardized HTTP exception"""

    error_detail = {
        "message": message,
        "error_code": error_code,
        "timestamp": time.time(),
    }

    if details:
        error_detail["details"] = details

    return HTTPException(status_code=status_code, detail=error_detail)


# Common error responses
def not_found_error(resource: str, resource_id: str) -> HTTPException:
    """Create a not found error"""
    return create_http_exception(
        message=f"{resource} with id '{resource_id}' not found",
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="NOT_FOUND",
    )


def validation_error(
    message: str, field: str = None, value: Any = None
) -> HTTPException:
    """Create a validation error"""
    details = {}
    if field:
        details["field"] = field
    if value is not None:
        details["value"] = str(value)

    return create_http_exception(
        message=message,
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code="VALIDATION_ERROR",
        details=details,
    )


def service_unavailable_error(service_name: str, reason: str = None) -> HTTPException:
    """Create a service unavailable error"""
    message = f"{service_name} service is currently unavailable"
    if reason:
        message += f": {reason}"

    return create_http_exception(
        message=message,
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error_code="SERVICE_UNAVAILABLE",
    )


def rate_limit_error(limit: int, window: str = "minute") -> HTTPException:
    """Create a rate limit error"""
    return create_http_exception(
        message=f"Rate limit exceeded: {limit} requests per {window}",
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        error_code="RATE_LIMIT_EXCEEDED",
    )


# Error handling decorator
def handle_errors(func):
    """Decorator to handle errors in service functions"""

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception:
            # This would need to be adapted based on the context
            # For now, just re-raise
            raise

    return wrapper
