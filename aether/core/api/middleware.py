"""
Middleware for Aether AI Companion API.
"""

import time
import logging
from typing import Callable
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from shared.config.settings import get_settings
from shared.utils.logging import get_logger

logger = get_logger(__name__)


# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)


class RequestLoggingMiddleware:
    """Middleware for logging API requests."""
    
    def __init__(self, app: FastAPI):
        self.app = app
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request with logging."""
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {response.status_code} - {process_time:.3f}s",
                extra={
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "method": request.method,
                    "path": request.url.path
                }
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {str(e)} - {process_time:.3f}s",
                extra={
                    "error": str(e),
                    "process_time": process_time,
                    "method": request.method,
                    "path": request.url.path
                },
                exc_info=True
            )
            raise


class SecurityHeadersMiddleware:
    """Middleware for adding security headers."""
    
    def __init__(self, app: FastAPI):
        self.app = app
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss:;"
        )
        
        return response


class ErrorHandlingMiddleware:
    """Middleware for centralized error handling."""
    
    def __init__(self, app: FastAPI):
        self.app = app
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Handle errors consistently."""
        try:
            return await call_next(request)
        except HTTPException:
            # Re-raise HTTP exceptions (handled by FastAPI)
            raise
        except Exception as e:
            logger.error(
                f"Unhandled error in {request.method} {request.url.path}: {str(e)}",
                exc_info=True
            )
            
            # Return generic error response
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )


def setup_middleware(app: FastAPI) -> None:
    """
    Set up all middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    settings = get_settings()
    
    # Rate limiting middleware
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time"]
    )
    
    # Trusted host middleware
    if settings.allowed_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts
        )
    
    # Custom middleware (order matters - last added runs first)
    app.middleware("http")(ErrorHandlingMiddleware(app))
    app.middleware("http")(SecurityHeadersMiddleware(app))
    app.middleware("http")(RequestLoggingMiddleware(app))
    
    logger.info("Middleware setup completed")


# Rate limiting decorators for common use cases
def rate_limit_strict(requests: str = "10/minute"):
    """Strict rate limiting for sensitive endpoints."""
    return limiter.limit(requests)


def rate_limit_moderate(requests: str = "100/minute"):
    """Moderate rate limiting for regular endpoints."""
    return limiter.limit(requests)


def rate_limit_lenient(requests: str = "1000/minute"):
    """Lenient rate limiting for high-frequency endpoints."""
    return limiter.limit(requests)