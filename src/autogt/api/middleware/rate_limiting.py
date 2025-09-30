"""Rate limiting middleware for FastAPI application."""

import time
from collections import defaultdict
from typing import Dict, DefaultDict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.client_calls: DefaultDict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        now = time.time()
        minute_ago = now - 60
        
        # Clean old entries
        self.client_calls[client_ip] = [
            call_time for call_time in self.client_calls[client_ip]
            if call_time > minute_ago
        ]
        
        # Check if limit exceeded
        if len(self.client_calls[client_ip]) >= self.calls_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Add current call
        self.client_calls[client_ip].append(now)
        
        response = await call_next(request)
        return response