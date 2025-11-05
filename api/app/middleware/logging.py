"""
Logging middleware
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import structlog
import time
import uuid

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request/response logging
    """

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())

        # Add request ID to context
        structlog.contextvars.bind_contextvars(request_id=request_id)

        # Log request
        start_time = time.time()
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None,
        )

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time=f"{process_time:.3f}s",
        )

        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"

        # Clear context
        structlog.contextvars.clear_contextvars()

        return response
