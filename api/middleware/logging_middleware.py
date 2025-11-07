"""Middleware for adding structured logging and trace ID to requests."""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from domain.services.observability_service import ObservabilityService
from domain.services.alert_service import AlertService


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to add trace ID and structured logging to each request."""

    def __init__(self, app, observability_service: ObservabilityService = None, alert_service: AlertService = None):
        """
        Initialize the middleware.

        Args:
            app: FastAPI application instance
            observability_service: ObservabilityService instance for logging
            alert_service: AlertService instance for sending alerts
        """
        super().__init__(app)
        self.observability_service = observability_service or ObservabilityService(alert_service)
        self.alert_service = alert_service or AlertService()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Process the request and add structured logging.

        Args:
            request: FastAPI request object
            call_next: Next middleware or endpoint in the chain

        Returns:
            Response object
        """
        # Generate trace ID
        trace_id = self.observability_service.generate_trace_id()
        
        # Log request start
        self.observability_service.log_info(
            f"Request started: {request.method} {request.url.path}",
            context={
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "user_agent": request.headers.get("user-agent"),
            },
            trace_id=trace_id
        )
        
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
        except Exception as e:
            # Log the exception and send alert
            self.observability_service.log_error(
                f"Request failed with exception: {str(e)}",
                exception=e,
                context={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": getattr(response, 'status_code', 500) if 'response' in locals() else 500
                },
                trace_id=trace_id,
                alert=True
            )
            # Re-raise the exception
            raise
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Log request completion
        status_code = response.status_code
        self.observability_service.log_info(
            f"Request completed: {request.method} {request.url.path}",
            context={
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "execution_time_ms": execution_time * 1000
            },
            trace_id=trace_id
        )
        
        # Add trace ID to response headers
        response.headers["X-Trace-ID"] = trace_id
        
        # Log metrics
        self.observability_service.log_metric(
            "request_duration_ms",
            execution_time * 1000,
            tags={
                "method": request.method,
                "path": request.url.path,
                "status_code": str(status_code)
            },
            trace_id=trace_id
        )
        
        return response
