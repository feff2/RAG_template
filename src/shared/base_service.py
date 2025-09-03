"""
Lightweight Base Service for Microservices

Extracts common patterns while keeping services completely atomic.
No shared dependencies or complex inheritance.
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .logger import CustomLogger


class BaseService(ABC):
    """Lightweight base class for microservices - no shared state"""

    def __init__(self, service_name: str, app: FastAPI):
        self.service_name = service_name
        self.app = app
        self.logger = CustomLogger(service_name)
        self.start_time: Optional[float] = None

        # Add common middleware
        self._add_common_middleware()
        self._add_common_routes()

    def _add_common_middleware(self):
        """Add common middleware to all services"""
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Request timing
        @self.app.middleware("http")
        async def add_timing_header(request, call_next):
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Service-Name"] = self.service_name
            return response

    def _add_common_routes(self):
        """Add common routes to all services"""

        @self.app.get("/health")
        async def health_check():
            """Standard health check"""
            try:
                health_info = await self._get_health_info()
                return health_info
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content={"status": "unhealthy", "error": str(e)},
                )

        @self.app.get("/status")
        async def get_status():
            """Get service status"""
            try:
                return {
                    "service": self.service_name,
                    "status": "running",
                    "uptime": self._get_uptime(),
                    "health": await self._get_health_info(),
                    "timestamp": time.time(),
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    @abstractmethod
    async def _get_health_info(self) -> Dict[str, Any]:
        """Service-specific health check - must implement"""
        pass

    def _get_uptime(self) -> float:
        """Get service uptime"""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    async def start(self):
        """Start the service"""
        self.start_time = time.time()
        self.logger.info(f"{self.service_name} service started")

    async def stop(self):
        """Stop the service"""
        self.logger.info(f"{self.service_name} service stopped")


def create_service_app(
    service_name: str, title: str = None, description: str = None
) -> FastAPI:
    """Create a FastAPI app with common configuration"""
    return FastAPI(
        title=title or f"{service_name.title()} Service",
        description=description or f"Microservice for {service_name}",
        version="1.0.0",
    )
