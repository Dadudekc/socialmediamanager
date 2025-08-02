"""Dashboard helpers for displaying GrowthEngine information.

The real project would expose these values through a web framework.  For
our tests we only need a light-weight asynchronous facade that can be
queried for dashboard data.
"""
from __future__ import annotations

from typing import Any, Dict, List

from growth_engine import GrowthEngine


class GrowthEngineDashboard:
    """In-memory dashboard data provider."""

    def __init__(self, engine: GrowthEngine | None = None) -> None:
        self.engine = engine or GrowthEngine()

    async def get(self, path: str) -> Dict[str, Any]:
        """Return dashboard related information for supported paths."""
        if path == "/api/dashboard-data":
            stats = {
                "total_users": len(self.engine.users),
                "total_communities": len(self.engine.communities),
                "total_collaborations": len(self.engine.collaborations),
                "total_templates": len(self.engine.templates),
            }

            charts: List[Dict[str, Any]] = [
                {"name": "users", "data": [len(self.engine.users)]},
                {"name": "communities", "data": [len(self.engine.communities)]},
            ]

            lists: List[Dict[str, Any]] = [
                {
                    "title": "Top Users",
                    "items": [
                        u.username
                        for u in sorted(
                            self.engine.users.values(),
                            key=lambda u: u.xp_points,
                            reverse=True,
                        )[:5]
                    ],
                },
                {
                    "title": "Communities",
                    "items": [c.name for c in self.engine.communities.values()],
                },
            ]

            return {"stats": stats, "charts": charts, "lists": lists}

        return {}


# Default application instance
app = GrowthEngineDashboard()

__all__ = ["app", "GrowthEngineDashboard"]
