"""
LugyFlutter - واجهات الويب
"""

from .dashboard import WebDashboard
from .api import FastAPIWrapper, app
from .models import (
    TaskRequest,
    TaskResponse,
    StatusResponse,
    HealthResponse
)

__all__ = [
    "WebDashboard",
    "FastAPIWrapper",
    "app",
    "TaskRequest",
    "TaskResponse",
    "StatusResponse",
    "HealthResponse",
]