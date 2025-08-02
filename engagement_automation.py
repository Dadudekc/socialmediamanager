import sys
from pathlib import Path

src_path = Path(__file__).resolve().parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from core.engagement_automation import (
    EngagementAutomation,
    EngagementType,
)

__all__ = [
    "EngagementAutomation",
    "EngagementType",
]
