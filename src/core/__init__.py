"""
Core automation components for the Ultimate Follow Builder.

This package contains the main automation systems:
- Follow automation
- Engagement automation  
- Ultimate follow builder
- Builder configuration
"""

from .follow_automation import FollowAutomation
from .engagement_automation import EngagementAutomation
from .ultimate_follow_builder import UltimateFollowBuilder
from .builder_config import BuilderConfig, BuilderMode

__all__ = [
    "FollowAutomation",
    "EngagementAutomation", 
    "UltimateFollowBuilder",
    "BuilderConfig",
    "BuilderMode"
] 