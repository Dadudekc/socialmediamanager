#!/usr/bin/env python3
"""
Ultimate Follow Builder - The most comprehensive social media growth automation system.
Integrates follow automation, engagement automation, content optimization, and AI features.
"""

import os
import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
from pathlib import Path

from setup_logging import setup_logging
from follow_automation import FollowAutomation, PlatformType, TargetingType, ActionType
from engagement_automation import EngagementAutomation, EngagementType
from growth_engine import GrowthEngine, CommunityType, BadgeType

logger = setup_logging("ultimate_follow_builder", log_dir="./logs")

class BuilderMode(Enum):
    """Modes of operation for the Ultimate Follow Builder."""
    AGGRESSIVE = "aggressive"  # Fast growth, higher risk
    MODERATE = "moderate"      # Balanced growth, medium risk
    CONSERVATIVE = "conservative"  # Slow growth, low risk
    SAFE = "safe"             # Very slow growth, minimal risk

@dataclass
class BuilderConfig:
    """Configuration for the Ultimate Follow Builder."""
    mode: BuilderMode
    platforms: List[str]
    daily_follow_limit: int
    daily_unfollow_limit: int
    daily_engagement_limit: int
    engagement_window_days: int
    safety_settings: Dict[str, Any]
    ai_features_enabled: bool = True
    analytics_enabled: bool = True

@dataclass
class BuilderStats:
    """Statistics for the Ultimate Follow Builder."""
    total_follows: int = 0
    total_unfollows: int = 0
    total_engagements: int = 0
    total_followers_gained: int = 0
    engagement_rate: float = 0.0
    growth_rate: float = 0.0
    account_health_score: float = 100.0
    last_updated: datetime = field(default_factory=datetime.now)

class UltimateFollowBuilder:
    """The Ultimate Follow Builder - Complete social media growth automation."""
    
    def __init__(self, config: BuilderConfig):
        self.config = config
        self.follow_automation = FollowAutomation()
        self.engagement_automation = EngagementAutomation()
        self.growth_engine = GrowthEngine()
        self.stats = BuilderStats()
        self.active_campaigns: Dict[str, Any] = {}
        self.account_health: Dict[str, Any] = {}
        
        # Initialize based on mode
        self._initialize_mode_settings()
        self._initialize_account_health()
    
    def _initialize_mode_settings(self):
        """Initialize settings based on the selected mode."""
        mode_settings = {
            BuilderMode.AGGRESSIVE: {
                "daily_follow_limit": 100,
                "daily_unfollow_limit": 80,
                "daily_engagement_limit": 200,
                "engagement_window_days": 2,
                "human_delay_min": 20,
                "human_delay_max": 60,
                "safety_threshold": 0.7
            },
            BuilderMode.MODERATE: {
                "daily_follow_limit": 50,
                "daily_unfollow_limit": 40,
                "daily_engagement_limit": 100,
                "engagement_window_days": 3,
                "human_delay_min": 30,
                "human_delay_max": 90,
                "safety_threshold": 0.8
            },
            BuilderMode.CONSERVATIVE: {
                "daily_follow_limit": 25,
                "daily_unfollow_limit": 20,
                "daily_engagement_limit": 50,
                "engagement_window_days": 5,
                "human_delay_min": 45,
                "human_delay_max": 120,
                "safety_threshold": 0.9
            },
            BuilderMode.SAFE: {
                "daily_follow_limit": 10,
                "daily_unfollow_limit": 8,
                "daily_engagement_limit": 25,
                "engagement_window_days": 7,
                "human_delay_min": 60,
                "human_delay_max": 180,
                "safety_threshold": 0.95
            }
        }
        
        settings = mode_settings.get(self.config.mode, mode_settings[BuilderMode.MODERATE])
        
        # Update config with mode-specific settings
        self.config.daily_follow_limit = settings["daily_follow_limit"]
        self.config.daily_unfollow_limit = settings["daily_unfollow_limit"]
        self.config.daily_engagement_limit = settings["daily_engagement_limit"]
        self.config.engagement_window_days = settings["engagement_window_days"]
        self.config.safety_settings.update(settings)
    
    def _initialize_account_health(self):
        """Initialize account health monitoring."""
        for platform in self.config.platforms:
            self.account_health[platform] = {
                "health_score": 100.0,
                "last_action": None,
                "daily_actions": 0,
                "warnings": [],
                "suspensions": 0,
                "rate_limit_hits": 0
            }
    
    async def create_growth_strategy(self, niche: str, target_audience: Dict[str, Any]) -> str:
        """Create a comprehensive growth strategy."""
        strategy_id = f"strategy-{niche}-{int(time.time())}"
        
        # Create follow campaigns for each platform
        follow_campaigns = []
        for platform in self.config.platforms:
            campaign_id = await self.follow_automation.create_follow_campaign(
                name=f"{niche.title()} Follow Campaign - {platform.title()}",
                platform=PlatformType(platform),
                targeting_type=TargetingType.NICHE,
                target_criteria={
                    "niche": niche,
                    "min_followers": target_audience.get("min_followers", 1000),
                    "max_followers": target_audience.get("max_followers", 100000),
                    "min_engagement_rate": target_audience.get("min_engagement_rate", 0.02),
                    "interests": target_audience.get("interests", []),
                    "locations": target_audience.get("locations", [])
                },
                daily_follow_limit=self.config.daily_follow_limit,
                daily_unfollow_limit=self.config.daily_unfollow_limit,
                engagement_window_days=self.config.engagement_window_days
            )
            follow_campaigns.append(campaign_id)
        
        # Create engagement campaigns for each platform
        engagement_campaigns = []
        for platform in self.config.platforms:
            campaign_id = await self.engagement_automation.create_engagement_campaign(
                name=f"{niche.title()} Engagement Campaign - {platform.title()}",
                platform=platform,
                engagement_types=[EngagementType.LIKE, EngagementType.COMMENT, EngagementType.STORY_VIEW],
                target_criteria={
                    "min_followers": target_audience.get("min_followers", 1000),
                    "max_followers": target_audience.get("max_followers", 100000),
                    "min_engagement_rate": target_audience.get("min_engagement_rate", 0.02),
                    "max_post_age_hours": 24
                },
                daily_engagement_limit=self.config.daily_engagement_limit
            )
            engagement_campaigns.append(campaign_id)
        
        # Create growth engine community
        community_id = await self.growth_engine.create_micro_community(
            name=f"{niche.title()} Growth Community",
            community_type=CommunityType.NICHE_FINDER,
            description=f"Automated growth community for {niche} niche",
            templates=[
                {
                    "name": f"{niche.title()} Growth Template",
                    "steps": [
                        f"Identify {niche} target audience",
                        "Analyze competitor strategies",
                        "Optimize content for {niche}",
                        "Track growth metrics"
                    ]
                }
            ]
        )
        
        strategy = {
            "id": strategy_id,
            "niche": niche,
            "target_audience": target_audience,
            "follow_campaigns": follow_campaigns,
            "engagement_campaigns": engagement_campaigns,
            "community_id": community_id,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        self.active_campaigns[strategy_id] = strategy
        logger.info(f"Created growth strategy: {strategy_id} for {niche} niche")
        
        return strategy_id
    
    async def execute_growth_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Execute a complete growth strategy."""
        if strategy_id not in self.active_campaigns:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        strategy = self.active_campaigns[strategy_id]
        
        logger.info(f"Executing growth strategy: {strategy_id}")
        
        results = {
            "strategy_id": strategy_id,
            "niche": strategy["niche"],
            "follow_results": [],
            "engagement_results": [],
            "growth_metrics": {},
            "account_health": {}
        }
        
        # Execute follow campaigns
        for campaign_id in strategy["follow_campaigns"]:
            try:
                result = await self.follow_automation.run_campaign(campaign_id)
                results["follow_results"].append(result)
                
                # Update stats
                self.stats.total_follows += result.get("successful_actions", 0)
                
            except Exception as e:
                logger.error(f"Error in follow campaign {campaign_id}: {e}")
                results["follow_results"].append({"error": str(e)})
        
        # Execute engagement campaigns
        for campaign_id in strategy["engagement_campaigns"]:
            try:
                result = await self.engagement_automation.run_engagement_campaign(campaign_id)
                results["engagement_results"].append(result)
                
                # Update stats
                self.stats.total_engagements += result.get("successful_engagements", 0)
                
            except Exception as e:
                logger.error(f"Error in engagement campaign {campaign_id}: {e}")
                results["engagement_results"].append({"error": str(e)})
        
        # Calculate growth metrics
        results["growth_metrics"] = await self._calculate_growth_metrics(strategy_id)
        
        # Update account health
        results["account_health"] = self._update_account_health()
        
        # Update builder stats
        self._update_builder_stats()
        
        logger.info(f"Growth strategy {strategy_id} completed: {results}")
        return results
    
    async def _calculate_growth_metrics(self, strategy_id: str) -> Dict[str, Any]:
        """Calculate growth metrics for a strategy."""
        strategy = self.active_campaigns[strategy_id]
        
        # Simulate follower growth based on actions
        total_follows = sum(
            result.get("successful_actions", 0) 
            for result in strategy.get("follow_results", [])
        )
        
        # Estimate follower gain (typically 10-30% follow back rate)
        follow_back_rate = random.uniform(0.1, 0.3)
        estimated_followers_gained = int(total_follows * follow_back_rate)
        
        # Calculate engagement rate
        total_engagements = sum(
            result.get("successful_engagements", 0)
            for result in strategy.get("engagement_results", [])
        )
        
        engagement_rate = total_engagements / max(total_follows, 1)
        
        return {
            "total_follows": total_follows,
            "estimated_followers_gained": estimated_followers_gained,
            "total_engagements": total_engagements,
            "engagement_rate": engagement_rate,
            "growth_rate": estimated_followers_gained / max(total_follows, 1),
            "strategy_efficiency": engagement_rate * follow_back_rate
        }
    
    def _update_account_health(self) -> Dict[str, Any]:
        """Update and return account health status."""
        for platform in self.config.platforms:
            health = self.account_health[platform]
            
            # Simulate health changes based on actions
            if health["daily_actions"] > self.config.daily_follow_limit * 0.8:
                health["health_score"] = max(health["health_score"] - 5, 0)
                health["warnings"].append("High daily action count")
            
            if health["rate_limit_hits"] > 0:
                health["health_score"] = max(health["health_score"] - 10, 0)
                health["warnings"].append("Rate limit exceeded")
            
            # Reset daily actions
            health["daily_actions"] = 0
        
        return self.account_health
    
    def _update_builder_stats(self):
        """Update builder statistics."""
        self.stats.last_updated = datetime.now()
        
        # Calculate overall engagement rate
        total_actions = self.stats.total_follows + self.stats.total_engagements
        self.stats.engagement_rate = self.stats.total_engagements / max(total_actions, 1)
        
        # Calculate growth rate
        self.stats.growth_rate = self.stats.total_followers_gained / max(self.stats.total_follows, 1)
        
        # Calculate account health score (average across platforms)
        health_scores = [health["health_score"] for health in self.account_health.values()]
        self.stats.account_health_score = sum(health_scores) / len(health_scores) if health_scores else 100.0
    
    async def get_builder_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data for the Ultimate Follow Builder."""
        dashboard = {
            "builder_stats": {
                "total_follows": self.stats.total_follows,
                "total_unfollows": self.stats.total_unfollows,
                "total_engagements": self.stats.total_engagements,
                "total_followers_gained": self.stats.total_followers_gained,
                "engagement_rate": self.stats.engagement_rate,
                "growth_rate": self.stats.growth_rate,
                "account_health_score": self.stats.account_health_score,
                "last_updated": self.stats.last_updated.isoformat()
            },
            "active_campaigns": len(self.active_campaigns),
            "account_health": self.account_health,
            "config": {
                "mode": self.config.mode.value,
                "platforms": self.config.platforms,
                "daily_limits": {
                    "follows": self.config.daily_follow_limit,
                    "unfollows": self.config.daily_unfollow_limit,
                    "engagements": self.config.daily_engagement_limit
                }
            },
            "campaign_summary": await self._get_campaign_summary()
        }
        
        return dashboard
    
    async def _get_campaign_summary(self) -> Dict[str, Any]:
        """Get summary of all campaigns."""
        follow_stats = await self.follow_automation.get_all_campaign_stats()
        engagement_stats = []
        
        for campaign_id in self.engagement_automation.campaigns:
            stats = await self.engagement_automation.get_engagement_stats(campaign_id)
            engagement_stats.append(stats)
        
        return {
            "follow_campaigns": len(follow_stats),
            "engagement_campaigns": len(engagement_stats),
            "total_campaigns": len(follow_stats) + len(engagement_stats),
            "active_follow_campaigns": len([s for s in follow_stats if s.get("is_active", False)]),
            "active_engagement_campaigns": len([s for s in engagement_stats if s.get("is_active", False)])
        }
    
    async def optimize_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Optimize a growth strategy based on performance data."""
        if strategy_id not in self.active_campaigns:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        strategy = self.active_campaigns[strategy_id]
        
        optimizations = {
            "strategy_id": strategy_id,
            "optimizations": [],
            "recommendations": []
        }
        
        # Analyze follow campaign performance
        for campaign_id in strategy["follow_campaigns"]:
            stats = await self.follow_automation.get_campaign_stats(campaign_id)
            
            if stats.get("success_rate", 0) < 0.7:
                optimizations["optimizations"].append({
                    "campaign_id": campaign_id,
                    "type": "follow",
                    "issue": "Low success rate",
                    "recommendation": "Adjust targeting criteria or reduce daily limits"
                })
        
        # Analyze engagement campaign performance
        for campaign_id in strategy["engagement_campaigns"]:
            stats = await self.engagement_automation.get_engagement_stats(campaign_id)
            
            if stats.get("overall_success_rate", 0) < 0.8:
                optimizations["optimizations"].append({
                    "campaign_id": campaign_id,
                    "type": "engagement",
                    "issue": "Low engagement success rate",
                    "recommendation": "Update engagement templates or timing"
                })
        
        # Account health recommendations
        for platform, health in self.account_health.items():
            if health["health_score"] < 80:
                optimizations["recommendations"].append({
                    "platform": platform,
                    "issue": "Low account health",
                    "recommendation": "Reduce daily limits or increase delays"
                })
        
        # Mode optimization
        if self.stats.account_health_score < 70:
            optimizations["recommendations"].append({
                "type": "mode_change",
                "issue": "Account health declining",
                "recommendation": f"Consider switching to {BuilderMode.CONSERVATIVE.value} mode"
            })
        
        logger.info(f"Strategy optimization completed for {strategy_id}")
        return optimizations
    
    async def run_ultimate_builder(self, niche: str, target_audience: Dict[str, Any]) -> Dict[str, Any]:
        """Run the complete Ultimate Follow Builder for a niche."""
        logger.info(f"🚀 Starting Ultimate Follow Builder for {niche} niche")
        
        # Create growth strategy
        strategy_id = await self.create_growth_strategy(niche, target_audience)
        
        # Execute strategy
        results = await self.execute_growth_strategy(strategy_id)
        
        # Optimize strategy
        optimizations = await self.optimize_strategy(strategy_id)
        
        # Get dashboard
        dashboard = await self.get_builder_dashboard()
        
        complete_results = {
            "strategy_id": strategy_id,
            "niche": niche,
            "execution_results": results,
            "optimizations": optimizations,
            "dashboard": dashboard,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Ultimate Follow Builder completed for {niche}")
        return complete_results

# Example usage
async def test_ultimate_follow_builder():
    """Test the Ultimate Follow Builder."""
    # Create configuration
    config = BuilderConfig(
        mode=BuilderMode.MODERATE,
        platforms=["instagram", "twitter"],
        daily_follow_limit=50,
        daily_unfollow_limit=40,
        daily_engagement_limit=100,
        engagement_window_days=3,
        safety_settings={},
        ai_features_enabled=True,
        analytics_enabled=True
    )
    
    # Initialize Ultimate Follow Builder
    builder = UltimateFollowBuilder(config)
    
    # Define target audience
    target_audience = {
        "min_followers": 2000,
        "max_followers": 50000,
        "min_engagement_rate": 0.02,
        "interests": ["fitness", "health", "workout"],
        "locations": ["United States", "Canada"]
    }
    
    # Run the Ultimate Follow Builder
    results = await builder.run_ultimate_builder("fitness", target_audience)
    
    print("🎯 Ultimate Follow Builder Results:")
    print(f"Strategy ID: {results['strategy_id']}")
    print(f"Growth Metrics: {results['execution_results']['growth_metrics']}")
    print(f"Account Health: {results['execution_results']['account_health']}")
    print(f"Optimizations: {len(results['optimizations']['optimizations'])}")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_ultimate_follow_builder()) 