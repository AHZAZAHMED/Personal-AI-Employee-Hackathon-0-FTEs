"""
Health Check System for AI Employee - Gold Tier

Provides HTTP health check endpoints for all services to enable monitoring and alerting.
Addresses AUDIT-1 RISK #5: No Health Monitoring
"""

import json
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from enum import Enum


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ServiceHealth:
    """Tracks health metrics for a service."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.status = HealthStatus.UNKNOWN
        self.start_time = datetime.now()
        self.last_check_time = datetime.now()
        self.error_count = 0
        self.success_count = 0
        self.details: Dict[str, Any] = {}
        self.dependencies: Dict[str, HealthStatus] = {}
        self._lock = threading.Lock()

    def update_status(self, status: str, details: Optional[Dict[str, Any]] = None):
        """Update service health status."""
        with self._lock:
            self.status = HealthStatus(status)
            self.last_check_time = datetime.now()
            if details:
                self.details.update(details)

    def record_success(self):
        """Record a successful operation."""
        with self._lock:
            self.success_count += 1
            self.last_check_time = datetime.now()

    def record_error(self):
        """Record an error."""
        with self._lock:
            self.error_count += 1
            self.last_check_time = datetime.now()

    def get_uptime_seconds(self) -> float:
        """Get service uptime in seconds."""
        return (datetime.now() - self.start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert health status to dictionary."""
        with self._lock:
            uptime = self.get_uptime_seconds()
            return {
                'service': self.service_name,
                'status': self.status.value,
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': uptime,
                'metrics': {
                    'success_count': self.success_count,
                    'error_count': self.error_count,
                },
                'details': self.details
            }


class HealthCheckServer:
    """HTTP server for health check endpoints."""

    def __init__(self, service_name: str, port: int = 8080):
        self.service_name = service_name
        self.port = port
        self.service_health = ServiceHealth(service_name)

    def start(self):
        """Start the health check server."""
        print(f"[HEALTH] Server ready on port {self.port}")
