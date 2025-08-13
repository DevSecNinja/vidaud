"""Health check server for monitoring application status."""

import logging
from datetime import UTC, datetime

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse


class HealthServer:
    """Simple health check server (NF12)."""

    def __init__(self, port: int = 8080):
        self.port = port
        self.logger = logging.getLogger(__name__)
        self.app = FastAPI(title="vidaud Health Check")
        self.start_time = datetime.now(UTC)

        # Setup routes
        self.app.get("/health")(self.health_check)
        self.app.get("/metrics")(self.metrics)

    async def health_check(self) -> JSONResponse:
        """Basic health check endpoint."""
        return JSONResponse(
            {
                "status": "healthy",
                "timestamp": datetime.now(UTC).isoformat(),
                "uptime_seconds": (datetime.now(UTC) - self.start_time).total_seconds(),
            }
        )

    async def metrics(self) -> JSONResponse:
        """Basic metrics endpoint (NF12)."""
        uptime = datetime.now(UTC) - self.start_time

        metrics_data = {
            "uptime_seconds": uptime.total_seconds(),
            "start_time": self.start_time.isoformat(),
            "current_time": datetime.now(UTC).isoformat(),
            "status": "running",
        }

        return JSONResponse(metrics_data)

    async def start(self):
        """Start the health server."""
        self.logger.info(f"Starting health server on port {self.port}")

        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="warning",  # Reduce uvicorn noise
            access_log=False,
        )

        server = uvicorn.Server(config)
        await server.serve()
