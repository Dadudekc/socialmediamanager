"""
Configuration settings for the Ultimate Follow Builder.

Centralized configuration management for all system components.
"""

import os
from typing import Dict, Any

# Environment settings
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/ultimate_follow_builder.db")

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8004"))
API_DEBUG = DEBUG

# Dashboard settings
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8004"))

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "data/logs/ultimate_follow_builder.log"

# Platform settings
PLATFORM_SETTINGS = {
    "instagram": {
        "rate_limits": {
            "follows_per_hour": 20,
            "likes_per_hour": 50,
            "comments_per_hour": 10
        },
        "safety_delays": {
            "min_delay": 30,
            "max_delay": 120
        }
    },
    "twitter": {
        "rate_limits": {
            "follows_per_hour": 30,
            "likes_per_hour": 100,
            "tweets_per_hour": 25
        },
        "safety_delays": {
            "min_delay": 20,
            "max_delay": 90
        }
    },
    "tiktok": {
        "rate_limits": {
            "follows_per_hour": 25,
            "likes_per_hour": 80,
            "comments_per_hour": 15
        },
        "safety_delays": {
            "min_delay": 25,
            "max_delay": 100
        }
    }
}

# AI settings
AI_SETTINGS = {
    "content_generation": {
        "max_length": 280,
        "include_hashtags": True,
        "include_emoji": True
    },
    "viral_prediction": {
        "min_score": 0.6,
        "confidence_threshold": 0.8
    }
}

# Growth engine settings
GROWTH_ENGINE_SETTINGS = {
    "micro_communities": {
        "max_members": 1000,
        "engagement_threshold": 0.05
    },
    "gamification": {
        "xp_per_action": 10,
        "level_thresholds": [100, 250, 500, 1000, 2000]
    }
}

# Safety settings
SAFETY_SETTINGS = {
    "max_daily_actions": 200,
    "account_health_threshold": 70,
    "suspension_check_interval": 3600
}

def get_setting(key: str, default: Any = None) -> Any:
    """Get a setting value with fallback to default."""
    return globals().get(key, default)

def get_platform_setting(platform: str, setting: str) -> Any:
    """Get platform-specific setting."""
    return PLATFORM_SETTINGS.get(platform, {}).get(setting)

def get_ai_setting(setting: str) -> Any:
    """Get AI-specific setting."""
    return AI_SETTINGS.get(setting, {})

def get_growth_setting(setting: str) -> Any:
    """Get growth engine setting."""
    return GROWTH_ENGINE_SETTINGS.get(setting, {}) 