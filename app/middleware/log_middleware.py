from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import logging
import time
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        path = re.sub(
            r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}',
            '<id>',
            request.url.path
        )
        
        logger.info(
            f"{request.method} {path} - {response.status_code} - {process_time:.4f}s"
        )
        return response
