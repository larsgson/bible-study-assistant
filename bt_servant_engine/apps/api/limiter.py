"""Rate limiter configuration for API endpoints."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiter: 10 requests per hour per IP address
limiter = Limiter(key_func=get_remote_address, default_limits=["10/hour"])

__all__ = ["limiter"]
