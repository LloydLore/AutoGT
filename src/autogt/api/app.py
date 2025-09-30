"""FastAPI application setup for AutoGT TARA Platform.

Reference: contracts/api.yaml - REST API specification
Provides HTTP endpoints matching CLI functionality for automotive cybersecurity analysis.
"""

from contextlib import asynccontextmanager
from typing import Dict, Any
import logging
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
import uvicorn

from .routes import analysis, export as export_routes
from .middleware.logging import setup_api_logging
from .middleware.rate_limiting import RateLimitingMiddleware


# Version information
__version__ = "1.0.0"

# Setup logging
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info(f"AutoGT TARA Platform API v{__version__} starting up...")
    
    # Initialize services (placeholder for future database connections, etc.)
    app.state.initialized = True
    logger.info("API services initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("AutoGT TARA Platform API shutting down...")
    # Cleanup resources if needed
    logger.info("Cleanup completed")


# Create FastAPI application
app = FastAPI(
    title="AutoGT TARA Platform API",
    description="CLI and API interfaces for automotive threat analysis and risk assessment following ISO/SAE 21434",
    version=__version__,
    contact={
        "name": "AutoGT Team",
        "url": "https://github.com/autogt/platform",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add custom middleware (placeholder implementations)
app.add_middleware(RateLimitingMiddleware, calls_per_minute=60)


# Custom exception handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler for consistent error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_error"
            },
            "request_id": getattr(request.state, 'request_id', None)
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions with appropriate HTTP status."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": 400,
                "message": str(exc),
                "type": "validation_error"
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(f"Unexpected error processing request: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "type": "internal_error"
            }
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "version": __version__,
        "service": "autogt-tara-api"
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AutoGT TARA Platform API",
        "version": __version__,
        "description": "Automotive cybersecurity threat analysis and risk assessment platform",
        "documentation": "/docs",
        "health_check": "/health"
    }


# Include routers
app.include_router(
    analysis.router,
    prefix="/api/v1/analysis",
    tags=["Analysis"]
)

app.include_router(
    export_routes.router,
    prefix="/api/v1/export",
    tags=["Export"]
)


# Development server configuration
def create_app(config: Dict[str, Any] = None) -> FastAPI:
    """Create configured FastAPI application.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured FastAPI application instance
    """
    if config:
        # Apply configuration if provided
        pass
    
    setup_api_logging()
    return app


def main():
    """Main entry point for running the API server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AutoGT TARA Platform API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    setup_api_logging()
    
    logger.info(f"Starting AutoGT TARA Platform API on {args.host}:{args.port}")
    
    uvicorn.run(
        "autogt.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        access_log=True
    )


if __name__ == "__main__":
    main()