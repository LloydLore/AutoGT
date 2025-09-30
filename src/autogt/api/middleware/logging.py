"""Logging middleware for FastAPI application."""

import logging
import time
from typing import Callable
from fastapi import Request, Response
from fastapi.routing import Match


logger = logging.getLogger(__name__)


def setup_api_logging():
    """Setup logging configuration for API."""
    # Configure logging format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configure loggers
    api_logger = logging.getLogger('autogt.api')
    api_logger.setLevel(logging.INFO)
    api_logger.addHandler(console_handler)


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """Log request and response information."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    
    return response