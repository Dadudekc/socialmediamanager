#!/usr/bin/env python3
"""
Engagement Automation System - Handles automated likes, comments, DMs, and story views.
Part of the Ultimate Follow Builder for intelligent engagement.
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

logger = setup_logging("engagement_automation", log_dir="./logs")

class EngagementType(Enum):
    """Types of engagement actions."""
    LIKE = "like"
    COMMENT = "comment"
    DM = "dm"
    STORY_VIEW = "story_view"
    REPLY = "reply"
    RETWEET = "retweet"
    SHARE = "share"

class ContentType(Enum):
    """Types of content for engagement."""
    POST = "post"
    STORY = "story"
    REEL = "reel"
    VIDEO = "video"
    CAROUSEL = "carousel"

@dataclass
class EngagementTemplate:
    """Template for engagement messages."""
    id: str
    type: EngagementType
    platform: str
    message: str
    emoji: str = ""
    use_count: int = 0
    success_rate: float = 0.0
    is_active: bool = True

@dataclass
class EngagementAction:
    """Represents an engagement action."""
    id: str
    target_username: str
    content_id: str
    engagement_type: EngagementType
    content_type: ContentType
    platform: str
    message: str
    timestamp: datetime
    success: bool = False
    response_received: bool = False
    engagement_metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EngagementCampaign:
    """Represents an engagement automation campaign."""
    id: str
    name: str
    platform: str
    engagement_types: List[EngagementType]
    target_criteria: Dict[str, Any]
    daily_engagement_limit: int
    engagement_timing: Dict[str, Any]
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    total_engagements: int = 0
    successful_engagements: int = 0

class EngagementAutomation:
    """Main engagement automation system."""
    
    def __init__(self):
        self.campaigns: Dict[str, EngagementCampaign] = {}
        self.templates: Dict[str, EngagementTemplate] = {}
        self.actions: List[EngagementAction] = []
        self.engagement_timing: Dict[str, Any] = {}
        
        # Initialize default templates and timing
        self._initialize_default_templates()
        self._initialize_engagement_timing()
    
    def _initialize_default_templates(self):
        """Initialize default engagement templates."""
        default_templates = [
            # Like templates (no message needed)
            {
                "id": "like_generic",
                "type": EngagementType.LIKE,
                "platform": "instagram",
                "message": "",
                "emoji": "❤️"
            },
            # Comment templates
            {
                "id": "comment_generic",
                "type": EngagementType.COMMENT,
                "platform": "instagram",
                "message": "Great content! 🔥",
                "emoji": "🔥"
            },
            {
                "id": "comment_question",
                "type": EngagementType.COMMENT,
                "platform": "instagram",
                "message": "What do you think about this? 🤔",
                "emoji": "🤔"
            },
            {
                "id": "comment_compliment",
                "type": EngagementType.COMMENT,
                "platform": "instagram",
                "message": "Amazing work! 👏",
                "emoji": "👏"
            },
            # DM templates
            {
                "id": "dm_greeting",
                "type": EngagementType.DM,
                "platform": "instagram",
                "message": "Hey! I love your content. Would love to connect! 😊",
                "emoji": "😊"
            },
            {
                "id": "dm_collaboration",
                "type": EngagementType.DM,
                "platform": "instagram",
                "message": "Hi! I think we could create some amazing content together. Interested? 🤝",
                "emoji": "🤝"
            },
            # Story view templates (no message needed)
            {
                "id": "story_view",
                "type": EngagementType.STORY_VIEW,
                "platform": "instagram",
                "message": "",
                "emoji": "👀"
            }
        ]
        
        for template_data in default_templates:
            template = EngagementTemplate(**template_data)
            self.templates[template.id] = template
    
    def _initialize_engagement_timing(self):
        """Initialize optimal engagement timing."""
        self.engagement_timing = {
            "instagram": {
                "best_hours": [9, 12, 18, 21],  # Best hours to engage
                "engagement_delay_min": 30,  # Minimum delay between engagements
                "engagement_delay_max": 120,  # Maximum delay between engagements
                "daily_limits": {
                    "likes": 100,
                    "comments": 20,
                    "dms": 10,
                    "story_views": 200
                }
            },
            "twitter": {
                "best_hours": [8, 12, 17, 20],
                "engagement_delay_min": 20,
                "engagement_delay_max": 90,
                "daily_limits": {
                    "likes": 150,
                    "comments": 30,
                    "dms": 15,
                    "retweets": 25
                }
            },
            "tiktok": {
                "best_hours": [10, 14, 19, 22],
                "engagement_delay_min": 25,
                "engagement_delay_max": 100,
                "daily_limits": {
                    "likes": 120,
                    "comments": 25,
                    "dms": 12,
                    "video_views": 300
                }
            }
        }
    
    async def create_engagement_campaign(self, name: str, platform: str,
                                       engagement_types: List[EngagementType],
                                       target_criteria: Dict[str, Any],
                                       daily_engagement_limit: int = 50) -> str:
        """Create a new engagement automation campaign."""
        campaign_id = f"engagement-{platform}-{int(time.time())}"
        
        campaign = EngagementCampaign(
            id=campaign_id,
            name=name,
            platform=platform,
            engagement_types=engagement_types,
            target_criteria=target_criteria,
            daily_engagement_limit=daily_engagement_limit,
            engagement_timing=self.engagement_timing.get(platform, {})
        )
        
        self.campaigns[campaign_id] = campaign
        logger.info(f"Created engagement campaign: {name} ({campaign_id})")
        return campaign_id
    
    async def create_engagement_template(self, template_type: EngagementType, platform: str,
                                       message: str, emoji: str = "") -> str:
        """Create a new engagement template."""
        template_id = f"template-{template_type.value}-{platform}-{int(time.time())}"
        
        template = EngagementTemplate(
            id=template_id,
            type=template_type,
            platform=platform,
            message=message,
            emoji=emoji
        )
        
        self.templates[template_id] = template
        logger.info(f"Created engagement template: {template_id}")
        return template_id
    
    async def find_engagement_targets(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Find targets for engagement based on campaign criteria."""
        if campaign_id not in self.campaigns:
            logger.error(f"Campaign {campaign_id} not found")
            return []
        
        campaign = self.campaigns[campaign_id]
        targets = []
        
        # Simulate finding engagement targets
        # This would integrate with platform APIs to find posts, stories, etc.
        for i in range(random.randint(20, 50)):
            target = {
                "username": f"target_user_{i}",
                "content_id": f"content_{i}",
                "content_type": random.choice(list(ContentType)),
                "engagement_score": random.uniform(0.5, 1.0),
                "post_time": datetime.now() - timedelta(hours=random.randint(1, 24)),
                "has_story": random.choice([True, False]),
                "follower_count": random.randint(1000, 100000),
                "engagement_rate": random.uniform(0.02, 0.08)
            }
            targets.append(target)
        
        # Filter targets based on criteria
        filtered_targets = self._filter_engagement_targets(targets, campaign)
        
        logger.info(f"Found {len(filtered_targets)} engagement targets for campaign {campaign_id}")
        return filtered_targets
    
    def _filter_engagement_targets(self, targets: List[Dict[str, Any]], 
                                 campaign: EngagementCampaign) -> List[Dict[str, Any]]:
        """Filter engagement targets based on campaign criteria."""
        filtered_targets = []
        
        for target in targets:
            # Apply filters based on campaign criteria
            if self._should_engage_with_target(target, campaign):
                filtered_targets.append(target)
        
        # Sort by engagement score
        filtered_targets.sort(key=lambda x: x["engagement_score"], reverse=True)
        
        return filtered_targets
    
    def _should_engage_with_target(self, target: Dict[str, Any], 
                                 campaign: EngagementCampaign) -> bool:
        """Determine if we should engage with a target."""
        # Check follower count
        min_followers = campaign.target_criteria.get("min_followers", 1000)
        max_followers = campaign.target_criteria.get("max_followers", 100000)
        
        if not (min_followers <= target["follower_count"] <= max_followers):
            return False
        
        # Check engagement rate
        min_engagement = campaign.target_criteria.get("min_engagement_rate", 0.01)
        if target["engagement_rate"] < min_engagement:
            return False
        
        # Check post age (don't engage with very old posts)
        max_post_age_hours = campaign.target_criteria.get("max_post_age_hours", 48)
        post_age_hours = (datetime.now() - target["post_time"]).total_seconds() / 3600
        if post_age_hours > max_post_age_hours:
            return False
        
        return True
    
    async def execute_engagement_action(self, campaign_id: str, target: Dict[str, Any],
                                      engagement_type: EngagementType, 
                                      template_id: Optional[str] = None) -> EngagementAction:
        """Execute an engagement action."""
        if campaign_id not in self.campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        campaign = self.campaigns[campaign_id]
        
        # Get template
        if template_id and template_id in self.templates:
            template = self.templates[template_id]
            message = template.message
        else:
            # Use default template for this engagement type
            message = self._get_default_message(engagement_type, campaign.platform)
        
        # Create action
        action = EngagementAction(
            id=f"engagement-{int(time.time())}",
            target_username=target["username"],
            content_id=target["content_id"],
            engagement_type=engagement_type,
            content_type=target["content_type"],
            platform=campaign.platform,
            message=message,
            timestamp=datetime.now()
        )
        
        # Execute action
        try:
            # Add human-like delay
            await self._engagement_delay(campaign.platform)
            
            # Execute engagement (this would integrate with platform APIs)
            success = await self._execute_platform_engagement(action)
            
            action.success = success
            if success:
                logger.info(f"Successfully engaged with {target['username']} via {engagement_type.value}")
                campaign.total_engagements += 1
                campaign.successful_engagements += 1
                
                # Update template success rate if template was used
                if template_id and template_id in self.templates:
                    template = self.templates[template_id]
                    template.use_count += 1
                    # Update success rate (simplified calculation)
                    template.success_rate = (template.success_rate * (template.use_count - 1) + 1) / template.use_count
            else:
                logger.warning(f"Failed to engage with {target['username']} via {engagement_type.value}")
        
        except Exception as e:
            action.success = False
            logger.error(f"Error executing engagement on {target['username']}: {e}")
        
        # Store action
        self.actions.append(action)
        
        return action
    
    def _get_default_message(self, engagement_type: EngagementType, platform: str) -> str:
        """Get default message for engagement type."""
        default_messages = {
            EngagementType.LIKE: "",
            EngagementType.COMMENT: "Great content! 🔥",
            EngagementType.DM: "Hey! Love your content! 😊",
            EngagementType.STORY_VIEW: "",
            EngagementType.REPLY: "Thanks for sharing! 🙏",
            EngagementType.RETWEET: "",
            EngagementType.SHARE: ""
        }
        
        return default_messages.get(engagement_type, "")
    
    async def _engagement_delay(self, platform: str):
        """Add delay between engagements."""
        timing = self.engagement_timing.get(platform, {})
        min_delay = timing.get("engagement_delay_min", 30)
        max_delay = timing.get("engagement_delay_max", 120)
        
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    async def _execute_platform_engagement(self, action: EngagementAction) -> bool:
        """Execute engagement on the specific platform."""
        # This would integrate with actual platform APIs
        # For now, simulate success with 85% probability
        return random.random() > 0.15
    
    async def run_engagement_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Run an engagement automation campaign."""
        if campaign_id not in self.campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        campaign = self.campaigns[campaign_id]
        
        logger.info(f"Starting engagement campaign: {campaign.name}")
        
        # Find engagement targets
        targets = await self.find_engagement_targets(campaign_id)
        
        # Execute engagements
        engagements_executed = 0
        successful_engagements = 0
        
        for target in targets[:campaign.daily_engagement_limit]:
            # Choose engagement type
            engagement_type = random.choice(campaign.engagement_types)
            
            # Choose template
            template_id = self._select_template(engagement_type, campaign.platform)
            
            try:
                action = await self.execute_engagement_action(
                    campaign_id, target, engagement_type, template_id
                )
                engagements_executed += 1
                if action.success:
                    successful_engagements += 1
                
            except Exception as e:
                logger.error(f"Error in engagement campaign {campaign_id}: {e}")
                break
        
        result = {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "targets_found": len(targets),
            "engagements_executed": engagements_executed,
            "successful_engagements": successful_engagements,
            "success_rate": successful_engagements / max(engagements_executed, 1)
        }
        
        logger.info(f"Engagement campaign {campaign.name} completed: {result}")
        return result
    
    def _select_template(self, engagement_type: EngagementType, platform: str) -> Optional[str]:
        """Select the best template for an engagement type."""
        available_templates = [
            template_id for template_id, template in self.templates.items()
            if template.type == engagement_type and 
               template.platform == platform and 
               template.is_active
        ]
        
        if not available_templates:
            return None
        
        # Select template based on success rate and use count
        best_template = None
        best_score = 0
        
        for template_id in available_templates:
            template = self.templates[template_id]
            # Score based on success rate and freshness (less used templates get bonus)
            score = template.success_rate + (1 / max(template.use_count, 1)) * 0.1
            if score > best_score:
                best_score = score
                best_template = template_id
        
        return best_template
    
    async def get_engagement_stats(self, campaign_id: str) -> Dict[str, Any]:
        """Get statistics for an engagement campaign."""
        if campaign_id not in self.campaigns:
            return {}
        
        campaign = self.campaigns[campaign_id]
        campaign_actions = [a for a in self.actions if a.campaign_id == campaign_id]
        
        # Group by engagement type
        engagement_by_type = {}
        for action in campaign_actions:
            engagement_type = action.engagement_type.value
            if engagement_type not in engagement_by_type:
                engagement_by_type[engagement_type] = {"total": 0, "successful": 0}
            engagement_by_type[engagement_type]["total"] += 1
            if action.success:
                engagement_by_type[engagement_type]["successful"] += 1
        
        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "platform": campaign.platform,
            "is_active": campaign.is_active,
            "total_engagements": campaign.total_engagements,
            "successful_engagements": campaign.successful_engagements,
            "overall_success_rate": campaign.successful_engagements / max(campaign.total_engagements, 1),
            "engagement_by_type": engagement_by_type,
            "created_at": campaign.created_at.isoformat()
        }
    
    async def get_template_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all templates."""
        stats = []
        for template_id, template in self.templates.items():
            stats.append({
                "template_id": template_id,
                "type": template.type.value,
                "platform": template.platform,
                "message": template.message,
                "use_count": template.use_count,
                "success_rate": template.success_rate,
                "is_active": template.is_active
            })
        return stats
    
    async def optimize_engagement_timing(self, platform: str) -> Dict[str, Any]:
        """Optimize engagement timing based on historical data."""
        # Analyze when engagements are most successful
        platform_actions = [a for a in self.actions if a.platform == platform]
        
        if not platform_actions:
            return {"message": "No data available for optimization"}
        
        # Group by hour and calculate success rates
        hourly_success = {}
        for action in platform_actions:
            hour = action.timestamp.hour
            if hour not in hourly_success:
                hourly_success[hour] = {"total": 0, "successful": 0}
            hourly_success[hour]["total"] += 1
            if action.success:
                hourly_success[hour]["successful"] += 1
        
        # Calculate success rates
        best_hours = []
        for hour, data in hourly_success.items():
            if data["total"] >= 5:  # Minimum sample size
                success_rate = data["successful"] / data["total"]
                if success_rate > 0.7:  # High success rate
                    best_hours.append(hour)
        
        # Update timing for the platform
        if platform in self.engagement_timing:
            self.engagement_timing[platform]["best_hours"] = sorted(best_hours)
        
        return {
            "platform": platform,
            "best_hours": sorted(best_hours),
            "hourly_success_rates": {
                hour: data["successful"] / data["total"] 
                for hour, data in hourly_success.items() 
                if data["total"] >= 5
            }
        }

# Example usage
async def test_engagement_automation():
    """Test the engagement automation system."""
    automation = EngagementAutomation()
    
    # Create an engagement campaign
    campaign_id = await automation.create_engagement_campaign(
        name="Fitness Engagement Campaign",
        platform="instagram",
        engagement_types=[EngagementType.LIKE, EngagementType.COMMENT, EngagementType.STORY_VIEW],
        target_criteria={
            "min_followers": 2000,
            "max_followers": 50000,
            "min_engagement_rate": 0.02,
            "max_post_age_hours": 24
        },
        daily_engagement_limit=30
    )
    
    # Run the campaign
    result = await automation.run_engagement_campaign(campaign_id)
    print(f"Engagement campaign result: {result}")
    
    # Get campaign stats
    stats = await automation.get_engagement_stats(campaign_id)
    print(f"Engagement campaign stats: {stats}")
    
    # Get template stats
    template_stats = await automation.get_template_stats()
    print(f"Template stats: {template_stats}")

if __name__ == "__main__":
    asyncio.run(test_engagement_automation()) 