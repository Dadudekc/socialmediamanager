import sys
from pathlib import Path

src_path = Path(__file__).resolve().parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from core.ultimate_follow_builder import (
    UltimateFollowBuilder,
    BuilderConfig,
    BuilderMode,
)

__all__ = [
    "UltimateFollowBuilder",
    "BuilderConfig",
    "BuilderMode",
]
