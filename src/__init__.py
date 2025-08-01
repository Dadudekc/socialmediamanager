"""
Ultimate Follow Builder - Main Package

The most comprehensive social media growth automation system.
"""

__version__ = "2.0.0"
__author__ = "Ultimate Follow Builder Team"
__description__ = "Advanced social media growth automation with AI content generation"

# Import main components for easy access
from .core.ultimate_follow_builder import UltimateFollowBuilder
from .ai.content_generator import AIContentGenerator
from .web.dashboard import start_dashboard

__all__ = [
    "UltimateFollowBuilder",
    "AIContentGenerator", 
    "start_dashboard"
] 