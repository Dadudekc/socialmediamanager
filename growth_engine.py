import importlib.util
import sys
from pathlib import Path

src_path = Path(__file__).resolve().parent / "src"
module_path = src_path / "growth_engine" / "growth_engine.py"

# Load the underlying implementation directly to avoid package import issues
spec = importlib.util.spec_from_file_location("growth_engine_impl", module_path)
module = importlib.util.module_from_spec(spec)
if spec and spec.loader:  # pragma: no cover - loader is always provided
    spec.loader.exec_module(module)

GrowthEngine = module.GrowthEngine
CommunityType = module.CommunityType
BadgeType = module.BadgeType

__all__ = ["GrowthEngine", "CommunityType", "BadgeType"]
