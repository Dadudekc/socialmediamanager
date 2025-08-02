import importlib.util
from pathlib import Path

src_path = Path(__file__).resolve().parent / "src"
module_path = src_path / "growth_engine" / "growth_engine_scheduler.py"

spec = importlib.util.spec_from_file_location("growth_engine_scheduler_impl", module_path)
module = importlib.util.module_from_spec(spec)
if spec and spec.loader:  # pragma: no cover
    spec.loader.exec_module(module)

GrowthEngineScheduler = module.GrowthEngineScheduler

__all__ = ["GrowthEngineScheduler"]
