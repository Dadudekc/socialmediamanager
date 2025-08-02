"""Simple asynchronous API facade for the GrowthEngine.

This module exposes a lightweight object with a ``get`` coroutine that
simulates a few HTTP endpoints used in the tests.  The implementation is
backed by the real :class:`~growth_engine.GrowthEngine` class so the
responses reflect the current state of the engine instance associated
with the application.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from growth_engine import GrowthEngine


class GrowthEngineAPI:
    """Tiny in-memory API used by the tests.

    The class mimics a subset of an HTTP web framework by exposing a
    :py:meth:`get` coroutine.  Each endpoint returns serialisable
    dictionaries so they can easily be consumed by the tests or future
    web layers.
    """

    def __init__(self, engine: GrowthEngine | None = None) -> None:
        self.engine = engine or GrowthEngine()

    async def get(self, path: str) -> Dict[str, Any]:
        """Handle a very small subset of GET endpoints.

        Parameters
        ----------
        path:
            The request path.  Only a handful of endpoints are
            recognised; anything else results in an empty dict which
            mirrors the behaviour of a ``404`` response in a real API.
        """
        if path == "/api/communities":
            communities = [
                {
                    "id": c.id,
                    "name": c.name,
                    "type": c.type.value,
                    "members": len(c.members),
                }
                for c in self.engine.communities.values()
            ]
            return {"communities": communities}

        if path == "/api/users":
            users = [
                {
                    "user_id": u.user_id,
                    "username": u.username,
                    "xp_points": u.xp_points,
                    "badges": [b.value for b in u.badges],
                }
                for u in self.engine.users.values()
            ]
            return {"users": users}

        if path == "/api/leaderboard":
            leaderboard = await self.engine.update_leaderboard()
            return {"leaderboard": leaderboard}

        if path == "/api/health":
            return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

        return {}


# Default application instance used by the tests
app = GrowthEngineAPI()

__all__ = ["app", "GrowthEngineAPI"]
