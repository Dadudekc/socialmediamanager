#!/usr/bin/env python3
"""
Follow Automation System - Core component of the Ultimate Follow Builder.
Handles automated following, unfollowing, and engagement targeting.
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

logger = setup_logging("follow_automation", log_dir="./logs")

class PlatformType(Enum):
    """Supported social media platforms."""
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"

class ActionType(Enum):
    """Types of follow automation actions."""
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"
    LIKE = "like"
    COMMENT = "comment"
    DM = "dm"
    STORY_VIEW = "story_view"

class TargetingType(Enum):
    """Types of targeting strategies."""
    HASHTAG = "hashtag"
    COMPETITOR_FOLLOWERS = "competitor_followers"
    LOCATION = "location"
    INTERESTS = "interests"
    ENGAGEMENT_BASED = "engagement_based"
    NICHE = "niche"

@dataclass
class TargetAccount:
    """Represents a target account for following."""
    username: str
    platform: PlatformType
    follower_count: int
    engagement_rate: float
    niche: str
    last_activity: datetime
    is_verified: bool = False
    is_private: bool = False
    engagement_score: float = 0.0
    follow_status: str = "not_followed"  # not_followed, following, followed_back, unfollowed

@dataclass
class FollowCampaign:
    """Represents a follow automation campaign."""
    id: str
    name: str
    platform: PlatformType
    targeting_type: TargetingType
    target_criteria: Dict[str, Any]
    daily_follow_limit: int
    daily_unfollow_limit: int
    engagement_window_days: int
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    total_follows: int = 0
    total_unfollows: int = 0
    total_engagements: int = 0

@dataclass
class FollowAction:
    """Represents a follow/unfollow action."""
    id: str
    campaign_id: str
    action_type: ActionType
    target_username: str
    platform: PlatformType
    timestamp: datetime
    success: bool = False
    error_message: str = ""
    engagement_metrics: Dict[str, Any] = field(default_factory=dict)

class FollowAutomation:
    """Main follow automation system."""
    
    def __init__(self):
        self.campaigns: Dict[str, FollowCampaign] = {}
        self.target_accounts: Dict[str, TargetAccount] = {}
        self.actions: List[FollowAction] = []
        self.rate_limits: Dict[PlatformType, Dict[str, Any]] = {}
        self.safety_settings: Dict[str, Any] = {}
        
        # Initialize rate limits for each platform
        self._initialize_rate_limits()
        self._initialize_safety_settings()
    
    def _initialize_rate_limits(self):
        """Initialize rate limits for different platforms."""
        self.rate_limits = {
            PlatformType.INSTAGRAM: {
                "follows_per_hour": 20,
                "unfollows_per_hour": 20,
                "likes_per_hour": 50,
                "comments_per_hour": 10,
                "dms_per_hour": 5,
                "story_views_per_hour": 100
            },
            PlatformType.TWITTER: {
                "follows_per_hour": 30,
                "unfollows_per_hour": 30,
                "likes_per_hour": 100,
                "comments_per_hour": 20,
                "dms_per_hour": 10,
                "retweets_per_hour": 20
            },
            PlatformType.TIKTOK: {
                "follows_per_hour": 25,
                "unfollows_per_hour": 25,
                "likes_per_hour": 80,
                "comments_per_hour": 15,
                "dms_per_hour": 8,
                "video_views_per_hour": 200
            }
        }
    
    def _initialize_safety_settings(self):
        """Initialize safety settings for account protection."""
        self.safety_settings = {
            "max_daily_follows": 150,
            "max_daily_unfollows": 150,
            "engagement_window_days": 3,
            "follow_ratio_threshold": 0.8,
            "human_delay_min": 30,
            "human_delay_max": 120,
            "randomization_factor": 0.3
        }
    
    async def create_follow_campaign(self, name: str, platform: PlatformType, 
                                   targeting_type: TargetingType, target_criteria: Dict[str, Any],
                                   daily_follow_limit: int = 50, daily_unfollow_limit: int = 50,
                                   engagement_window_days: int = 3) -> str:
        """Create a new follow automation campaign."""
        campaign_id = f"campaign-{platform.value}-{int(time.time())}"
        
        campaign = FollowCampaign(
            id=campaign_id,
            name=name,
            platform=platform,
            targeting_type=targeting_type,
            target_criteria=target_criteria,
            daily_follow_limit=daily_follow_limit,
            daily_unfollow_limit=daily_unfollow_limit,
            engagement_window_days=engagement_window_days
        )
        
        self.campaigns[campaign_id] = campaign
        logger.info(f"Created follow campaign: {name} ({campaign_id})")
        return campaign_id
    
    async def find_target_accounts(self, campaign_id: str) -> List[TargetAccount]:
        """Find target accounts based on campaign criteria."""
        if campaign_id not in self.campaigns:
            logger.error(f"Campaign {campaign_id} not found")
            return []
        
        campaign = self.campaigns[campaign_id]
        targets = []
        
        if campaign.targeting_type == TargetingType.HASHTAG:
            targets = await self._find_accounts_by_hashtag(campaign.target_criteria)
        elif campaign.targeting_type == TargetingType.COMPETITOR_FOLLOWERS:
            targets = await self._find_competitor_followers(campaign.target_criteria)
        elif campaign.targeting_type == TargetingType.LOCATION:
            targets = await self._find_accounts_by_location(campaign.target_criteria)
        elif campaign.targeting_type == TargetingType.INTERESTS:
            targets = await self._find_accounts_by_interests(campaign.target_criteria)
        elif campaign.targeting_type == TargetingType.ENGAGEMENT_BASED:
            targets = await self._find_high_engagement_accounts(campaign.target_criteria)
        elif campaign.targeting_type == TargetingType.NICHE:
            targets = await self._find_niche_accounts(campaign.target_criteria)
        
        # Filter and score targets
        filtered_targets = await self._filter_and_score_targets(targets, campaign)
        
        logger.info(f"Found {len(filtered_targets)} target accounts for campaign {campaign_id}")
        return filtered_targets
    
    async def _find_accounts_by_hashtag(self, criteria: Dict[str, Any]) -> List[TargetAccount]:
        """Find accounts using specific hashtags."""
        hashtags = criteria.get("hashtags", [])
        min_followers = criteria.get("min_followers", 1000)
        max_followers = criteria.get("max_followers", 100000)
        
        # Simulate finding accounts by hashtag
        accounts = []
        for hashtag in hashtags:
            # This would integrate with platform APIs
            for i in range(random.randint(10, 30)):
                account = TargetAccount(
                    username=f"user_{hashtag}_{i}",
                    platform=PlatformType.INSTAGRAM,
                    follower_count=random.randint(min_followers, max_followers),
                    engagement_rate=random.uniform(0.01, 0.05),
                    niche=hashtag,
                    last_activity=datetime.now() - timedelta(hours=random.randint(1, 24))
                )
                accounts.append(account)
        
        return accounts
    
    async def _find_competitor_followers(self, criteria: Dict[str, Any]) -> List[TargetAccount]:
        """Find followers of competitor accounts."""
        competitor_usernames = criteria.get("competitor_usernames", [])
        
        accounts = []
        for competitor in competitor_usernames:
            # Simulate finding competitor followers
            for i in range(random.randint(20, 50)):
                account = TargetAccount(
                    username=f"follower_{competitor}_{i}",
                    platform=PlatformType.INSTAGRAM,
                    follower_count=random.randint(500, 50000),
                    engagement_rate=random.uniform(0.02, 0.08),
                    niche=criteria.get("niche", "general"),
                    last_activity=datetime.now() - timedelta(hours=random.randint(1, 48))
                )
                accounts.append(account)
        
        return accounts
    
    async def _find_accounts_by_location(self, criteria: Dict[str, Any]) -> List[TargetAccount]:
        """Find accounts by location."""
        location = criteria.get("location", "")
        radius_km = criteria.get("radius_km", 50)
        
        # Simulate location-based targeting
        accounts = []
        for i in range(random.randint(15, 40)):
            account = TargetAccount(
                username=f"local_user_{location}_{i}",
                platform=PlatformType.INSTAGRAM,
                follower_count=random.randint(1000, 100000),
                engagement_rate=random.uniform(0.015, 0.06),
                niche=criteria.get("niche", "local"),
                last_activity=datetime.now() - timedelta(hours=random.randint(1, 72))
            )
            accounts.append(account)
        
        return accounts
    
    async def _find_accounts_by_interests(self, criteria: Dict[str, Any]) -> List[TargetAccount]:
        """Find accounts by interests."""
        interests = criteria.get("interests", [])
        
        accounts = []
        for interest in interests:
            for i in range(random.randint(10, 25)):
                account = TargetAccount(
                    username=f"interest_user_{interest}_{i}",
                    platform=PlatformType.INSTAGRAM,
                    follower_count=random.randint(2000, 80000),
                    engagement_rate=random.uniform(0.02, 0.07),
                    niche=interest,
                    last_activity=datetime.now() - timedelta(hours=random.randint(1, 36))
                )
                accounts.append(account)
        
        return accounts
    
    async def _find_high_engagement_accounts(self, criteria: Dict[str, Any]) -> List[TargetAccount]:
        """Find accounts with high engagement rates."""
        min_engagement_rate = criteria.get("min_engagement_rate", 0.03)
        
        accounts = []
        for i in range(random.randint(20, 60)):
            account = TargetAccount(
                username=f"high_engagement_user_{i}",
                platform=PlatformType.INSTAGRAM,
                follower_count=random.randint(5000, 100000),
                engagement_rate=random.uniform(min_engagement_rate, 0.12),
                niche=criteria.get("niche", "high_engagement"),
                last_activity=datetime.now() - timedelta(hours=random.randint(1, 24))
            )
            accounts.append(account)
        
        return accounts
    
    async def _find_niche_accounts(self, criteria: Dict[str, Any]) -> List[TargetAccount]:
        """Find accounts in specific niches."""
        niche = criteria.get("niche", "")
        min_followers = criteria.get("min_followers", 1000)
        max_followers = criteria.get("max_followers", 100000)
        
        accounts = []
        for i in range(random.randint(15, 45)):
            account = TargetAccount(
                username=f"niche_user_{niche}_{i}",
                platform=PlatformType.INSTAGRAM,
                follower_count=random.randint(min_followers, max_followers),
                engagement_rate=random.uniform(0.02, 0.08),
                niche=niche,
                last_activity=datetime.now() - timedelta(hours=random.randint(1, 48))
            )
            accounts.append(account)
        
        return accounts
    
    async def _filter_and_score_targets(self, targets: List[TargetAccount], 
                                      campaign: FollowCampaign) -> List[TargetAccount]:
        """Filter and score target accounts."""
        filtered_targets = []
        
        for target in targets:
            # Apply filters
            if self._should_target_account(target, campaign):
                # Calculate engagement score
                target.engagement_score = self._calculate_engagement_score(target)
                filtered_targets.append(target)
        
        # Sort by engagement score
        filtered_targets.sort(key=lambda x: x.engagement_score, reverse=True)
        
        return filtered_targets
    
    def _should_target_account(self, target: TargetAccount, campaign: FollowCampaign) -> bool:
        """Determine if an account should be targeted."""
        # Skip private accounts
        if target.is_private:
            return False
        
        # Check follower count range
        min_followers = campaign.target_criteria.get("min_followers", 1000)
        max_followers = campaign.target_criteria.get("max_followers", 100000)
        
        if not (min_followers <= target.follower_count <= max_followers):
            return False
        
        # Check engagement rate
        min_engagement = campaign.target_criteria.get("min_engagement_rate", 0.01)
        if target.engagement_rate < min_engagement:
            return False
        
        # Check activity (skip inactive accounts)
        days_inactive = (datetime.now() - target.last_activity).days
        max_inactive_days = campaign.target_criteria.get("max_inactive_days", 7)
        if days_inactive > max_inactive_days:
            return False
        
        return True
    
    def _calculate_engagement_score(self, target: TargetAccount) -> float:
        """Calculate engagement score for target account."""
        base_score = target.engagement_rate * 100
        
        # Bonus for verified accounts
        if target.is_verified:
            base_score *= 1.2
        
        # Bonus for recent activity
        hours_since_activity = (datetime.now() - target.last_activity).total_seconds() / 3600
        if hours_since_activity < 24:
            base_score *= 1.1
        
        # Penalty for very large accounts (less likely to follow back)
        if target.follower_count > 50000:
            base_score *= 0.8
        
        return base_score
    
    async def execute_follow_action(self, campaign_id: str, target_username: str, 
                                  action_type: ActionType) -> FollowAction:
        """Execute a follow/unfollow action."""
        if campaign_id not in self.campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        campaign = self.campaigns[campaign_id]
        
        # Check rate limits
        if not await self._check_rate_limit(campaign.platform, action_type):
            raise Exception(f"Rate limit exceeded for {action_type.value}")
        
        # Create action
        action = FollowAction(
            id=f"action-{int(time.time())}",
            campaign_id=campaign_id,
            action_type=action_type,
            target_username=target_username,
            platform=campaign.platform,
            timestamp=datetime.now()
        )
        
        # Simulate action execution
        try:
            # Add human-like delay
            await self._human_delay()
            
            # Execute action (this would integrate with platform APIs)
            success = await self._execute_platform_action(action)
            
            action.success = success
            if success:
                logger.info(f"Successfully executed {action_type.value} on {target_username}")
                
                # Update campaign stats
                if action_type == ActionType.FOLLOW:
                    campaign.total_follows += 1
                elif action_type == ActionType.UNFOLLOW:
                    campaign.total_unfollows += 1
                elif action_type in [ActionType.LIKE, ActionType.COMMENT, ActionType.DM]:
                    campaign.total_engagements += 1
            else:
                action.error_message = "Action failed"
                logger.warning(f"Failed to execute {action_type.value} on {target_username}")
        
        except Exception as e:
            action.success = False
            action.error_message = str(e)
            logger.error(f"Error executing {action_type.value} on {target_username}: {e}")
        
        # Store action
        self.actions.append(action)
        
        return action
    
    async def _check_rate_limit(self, platform: PlatformType, action_type: ActionType) -> bool:
        """Check if rate limit allows the action."""
        limits = self.rate_limits.get(platform, {})
        action_key = f"{action_type.value}s_per_hour"
        
        if action_key not in limits:
            return True
        
        # Count recent actions
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_actions = [
            action for action in self.actions
            if action.platform == platform and 
               action.action_type == action_type and
               action.timestamp > one_hour_ago
        ]
        
        return len(recent_actions) < limits[action_key]
    
    async def _human_delay(self):
        """Add human-like delay between actions."""
        min_delay = self.safety_settings["human_delay_min"]
        max_delay = self.safety_settings["human_delay_max"]
        
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    async def _execute_platform_action(self, action: FollowAction) -> bool:
        """Execute action on the specific platform."""
        # This would integrate with actual platform APIs
        # For now, simulate success with 90% probability
        return random.random() > 0.1
    
    async def run_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Run a follow automation campaign."""
        if campaign_id not in self.campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        campaign = self.campaigns[campaign_id]
        
        logger.info(f"Starting campaign: {campaign.name}")
        
        # Find target accounts
        targets = await self.find_target_accounts(campaign_id)
        
        # Execute actions
        actions_executed = 0
        successful_actions = 0
        
        for target in targets[:campaign.daily_follow_limit]:
            try:
                action = await self.execute_follow_action(
                    campaign_id, target.username, ActionType.FOLLOW
                )
                actions_executed += 1
                if action.success:
                    successful_actions += 1
                
                # Store target account
                self.target_accounts[target.username] = target
                
            except Exception as e:
                logger.error(f"Error in campaign {campaign_id}: {e}")
                break
        
        # Schedule unfollow actions for later
        await self._schedule_unfollow_actions(campaign_id, targets)
        
        result = {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "targets_found": len(targets),
            "actions_executed": actions_executed,
            "successful_actions": successful_actions,
            "success_rate": successful_actions / max(actions_executed, 1)
        }
        
        logger.info(f"Campaign {campaign.name} completed: {result}")
        return result
    
    async def _schedule_unfollow_actions(self, campaign_id: str, targets: List[TargetAccount]):
        """Schedule unfollow actions for the future."""
        campaign = self.campaigns[campaign_id]
        unfollow_delay = timedelta(days=campaign.engagement_window_days)
        
        for target in targets:
            # Schedule unfollow for later
            unfollow_time = datetime.now() + unfollow_delay
            # This would be stored in a job queue for later execution
            logger.info(f"Scheduled unfollow for {target.username} at {unfollow_time}")
    
    async def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """Get statistics for a campaign."""
        if campaign_id not in self.campaigns:
            return {}
        
        campaign = self.campaigns[campaign_id]
        campaign_actions = [a for a in self.actions if a.campaign_id == campaign_id]
        
        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "platform": campaign.platform.value,
            "targeting_type": campaign.targeting_type.value,
            "is_active": campaign.is_active,
            "total_follows": campaign.total_follows,
            "total_unfollows": campaign.total_unfollows,
            "total_engagements": campaign.total_engagements,
            "success_rate": len([a for a in campaign_actions if a.success]) / max(len(campaign_actions), 1),
            "created_at": campaign.created_at.isoformat()
        }
    
    async def get_all_campaign_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all campaigns."""
        stats = []
        for campaign_id in self.campaigns:
            stats.append(await self.get_campaign_stats(campaign_id))
        return stats

# Example usage
async def test_follow_automation():
    """Test the follow automation system."""
    automation = FollowAutomation()
    
    # Create a hashtag-based campaign
    campaign_id = await automation.create_follow_campaign(
        name="Fitness Hashtag Campaign",
        platform=PlatformType.INSTAGRAM,
        targeting_type=TargetingType.HASHTAG,
        target_criteria={
            "hashtags": ["fitness", "workout", "gym"],
            "min_followers": 2000,
            "max_followers": 50000,
            "min_engagement_rate": 0.02
        },
        daily_follow_limit=30,
        daily_unfollow_limit=30
    )
    
    # Run the campaign
    result = await automation.run_campaign(campaign_id)
    print(f"Campaign result: {result}")
    
    # Get campaign stats
    stats = await automation.get_campaign_stats(campaign_id)
    print(f"Campaign stats: {stats}")

if __name__ == "__main__":
    asyncio.run(test_follow_automation()) 