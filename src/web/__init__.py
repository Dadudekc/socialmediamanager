"""
Web interface components for the Ultimate Follow Builder.

This package contains web systems:
- Dashboard
- API endpoints
- WebSocket management
"""

from .dashboard import start_dashboard, get_dashboard_app
from .api import create_api_app

__all__ = [
    "start_dashboard",
    "get_dashboard_app", 
    "create_api_app"
] 