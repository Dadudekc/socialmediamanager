#!/usr/bin/env python3
"""
Growth Engine - Social Media Growth Automation System
Implements micro-communities, partner growth loops, gamification, content building, and API hooks.
"""

import os
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
import random
from pathlib import Path

from setup_logging import setup_logging

logger = setup_logging("growth_engine", log_dir="./logs")

class CommunityType(Enum):
    """Types of micro-communities."""
    NICHE_FINDER = "niche_finder"
    PROBLEM_SOLVER = "problem_solver"
    COLLABORATION = "collaboration"
    ENGAGEMENT = "engagement"

class BadgeType(Enum):
    """Types of engagement badges."""
    FIRST_COMMENT = "first_comment"
    WEEKLY_TOP = "weekly_top"
    COLLAB_MASTER = "collab_master"
    ENGAGEMENT_KING = "engagement_king"
    CONTENT_CREATOR = "content_creator"

@dataclass
class MicroCommunity:
    """Represents a micro-community."""
    id: str
    name: str
    type: CommunityType
    description: str
    members: List[str] = field(default_factory=list)
    templates: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    engagement_score: float = 0.0

@dataclass
class UserProfile:
    """User profile with gamification elements."""
    user_id: str
    username: str
    xp_points: int = 0
    level: int = 1
    badges: List[BadgeType] = field(default_factory=list)
    communities: List[str] = field(default_factory=list)
    weekly_engagement: int = 0
    total_posts: int = 0
    collaboration_count: int = 0

@dataclass
class ContentTemplate:
    """Content template for different formats."""
    id: str
    name: str
    type: str  # carousel, thread, short, post
    template_data: Dict[str, Any]
    engagement_score: float = 0.0
    usage_count: int = 0

@dataclass
class Collaboration:
    """Collaboration between users."""
    id: str
    user1_id: str
    user2_id: str
    platform: str
    content_type: str
    status: str  # pending, active, completed
    engagement_metrics: Dict[str, Any] = field(default_factory=dict)

class GrowthEngine:
    """Main growth engine class implementing all growth features."""
    
    def __init__(self):
        self.communities: Dict[str, MicroCommunity] = {}
        self.users: Dict[str, UserProfile] = {}
        self.templates: Dict[str, ContentTemplate] = {}
        self.collaborations: Dict[str, Collaboration] = {}
        self.leaderboard_data: Dict[str, List[Dict]] = {}
        self.background_jobs: List[Dict] = []
        
        # Initialize default communities and templates
        self._initialize_default_communities()
        self._initialize_default_templates()
    
    def _initialize_default_communities(self):
        """Initialize default micro-communities."""
        communities_data = [
            {
                "id": "niche-finder-001",
                "name": "Niche Finder Community",
                "type": CommunityType.NICHE_FINDER,
                "description": "Find and validate your niche with data-driven insights",
                "templates": [
                    {
                        "name": "Niche Research Template",
                        "steps": [
                            "Identify target audience demographics",
                            "Analyze competitor content",
                            "Find content gaps",
                            "Validate with engagement metrics"
                        ]
                    }
                ]
            },
            {
                "id": "problem-solver-001", 
                "name": "Problem Solver Community",
                "type": CommunityType.PROBLEM_SOLVER,
                "description": "Solve real problems with collaborative solutions",
                "templates": [
                    {
                        "name": "Problem-Solution Template",
                        "steps": [
                            "Define the problem clearly",
                            "Research existing solutions",
                            "Propose innovative approach",
                            "Test and validate solution"
                        ]
                    }
                ]
            }
        ]
        
        for comm_data in communities_data:
            community = MicroCommunity(**comm_data)
            self.communities[community.id] = community
    
    def _initialize_default_templates(self):
        """Initialize default content templates."""
        templates_data = [
            {
                "id": "carousel-template-001",
                "name": "Educational Carousel",
                "type": "carousel",
                "template_data": {
                    "slides": 5,
                    "format": "educational",
                    "elements": ["title", "problem", "solution", "benefits", "cta"]
                }
            },
            {
                "id": "thread-template-001", 
                "name": "Story Thread",
                "type": "thread",
                "template_data": {
                    "tweets": 5,
                    "format": "story",
                    "elements": ["hook", "setup", "conflict", "resolution", "lesson"]
                }
            },
            {
                "id": "short-template-001",
                "name": "Quick Tip Short",
                "type": "short",
                "template_data": {
                    "duration": "15-30s",
                    "format": "tip",
                    "elements": ["hook", "tip", "demonstration", "cta"]
                }
            }
        ]
        
        for template_data in templates_data:
            template = ContentTemplate(**template_data)
            self.templates[template.id] = template
    
    async def create_micro_community(self, name: str, community_type: CommunityType, 
                                   description: str, templates: List[Dict] = None) -> str:
        """Create a new micro-community."""
        community_id = f"{community_type.value}-{uuid.uuid4().hex[:8]}"
        
        community = MicroCommunity(
            id=community_id,
            name=name,
            type=community_type,
            description=description,
            templates=templates or []
        )
        
        self.communities[community_id] = community
        logger.info(f"Created micro-community: {name} ({community_id})")
        return community_id
    
    async def join_community(self, user_id: str, community_id: str) -> bool:
        """Add user to a micro-community."""
        if community_id not in self.communities:
            logger.error(f"Community {community_id} not found")
            return False
        
        if user_id not in self.communities[community_id].members:
            self.communities[community_id].members.append(user_id)
            
            # Add XP for joining community
            if user_id in self.users:
                self.users[user_id].xp_points += 10
                self.users[user_id].communities.append(community_id)
            
            logger.info(f"User {user_id} joined community {community_id}")
            return True
        
        return False
    
    async def create_user_profile(self, user_id: str, username: str) -> UserProfile:
        """Create a new user profile."""
        profile = UserProfile(user_id=user_id, username=username)
        self.users[user_id] = profile
        logger.info(f"Created user profile for {username}")
        return profile
    
    async def award_badge(self, user_id: str, badge_type: BadgeType) -> bool:
        """Award a badge to a user."""
        if user_id not in self.users:
            logger.error(f"User {user_id} not found")
            return False
        
        if badge_type not in self.users[user_id].badges:
            self.users[user_id].badges.append(badge_type)
            
            # Add XP for badge
            xp_rewards = {
                BadgeType.FIRST_COMMENT: 5,
                BadgeType.WEEKLY_TOP: 50,
                BadgeType.COLLAB_MASTER: 25,
                BadgeType.ENGAGEMENT_KING: 30,
                BadgeType.CONTENT_CREATOR: 20
            }
            
            self.users[user_id].xp_points += xp_rewards.get(badge_type, 10)
            logger.info(f"Awarded {badge_type.value} badge to user {user_id}")
            return True
        
        return False
    
    async def create_collaboration(self, user1_id: str, user2_id: str, 
                                 platform: str, content_type: str) -> str:
        """Create a collaboration between two users."""
        collab_id = f"collab-{uuid.uuid4().hex[:8]}"
        
        collaboration = Collaboration(
            id=collab_id,
            user1_id=user1_id,
            user2_id=user2_id,
            platform=platform,
            content_type=content_type,
            status="pending"
        )
        
        self.collaborations[collab_id] = collaboration
        logger.info(f"Created collaboration {collab_id} between {user1_id} and {user2_id}")
        return collab_id
    
    async def create_content_template(self, name: str, content_type: str, 
                                   template_data: Dict[str, Any]) -> str:
        """Create a new content template."""
        template_id = f"template-{uuid.uuid4().hex[:8]}"
        
        template = ContentTemplate(
            id=template_id,
            name=name,
            type=content_type,
            template_data=template_data
        )
        
        self.templates[template_id] = template
        logger.info(f"Created content template: {name} ({template_id})")
        return template_id
    
    async def generate_content_with_template(self, template_id: str, 
                                          custom_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate content using a template."""
        if template_id not in self.templates:
            logger.error(f"Template {template_id} not found")
            return {}
        
        template = self.templates[template_id]
        template.usage_count += 1
        
        # Merge template data with custom data
        content_data = template.template_data.copy()
        if custom_data:
            content_data.update(custom_data)
        
        return {
            "template_id": template_id,
            "template_name": template.name,
            "content_type": template.type,
            "generated_content": content_data,
            "usage_count": template.usage_count
        }
    
    async def update_leaderboard(self, platform: str = "all"):
        """Update weekly leaderboard."""
        # Calculate user scores
        user_scores = []
        for user_id, user in self.users.items():
            score = user.xp_points + (user.weekly_engagement * 2) + (user.collaboration_count * 10)
            user_scores.append({
                "user_id": user_id,
                "username": user.username,
                "score": score,
                "xp_points": user.xp_points,
                "weekly_engagement": user.weekly_engagement,
                "collaboration_count": user.collaboration_count
            })
        
        # Sort by score
        user_scores.sort(key=lambda x: x["score"], reverse=True)
        
        self.leaderboard_data[platform] = user_scores[:10]  # Top 10
        logger.info(f"Updated leaderboard for {platform}")
        return user_scores[:10]
    
    async def schedule_background_jobs(self):
        """Schedule background jobs for automation."""
        jobs = [
            {
                "id": "weekly-leaderboard",
                "type": "leaderboard_update",
                "schedule": "weekly",
                "function": self.update_leaderboard
            },
            {
                "id": "collab-suggestions",
                "type": "collaboration_suggestions",
                "schedule": "daily",
                "function": self._generate_collab_suggestions
            },
            {
                "id": "engagement-metrics",
                "type": "metrics_logging",
                "schedule": "hourly",
                "function": self._log_engagement_metrics
            }
        ]
        
        self.background_jobs = jobs
        logger.info(f"Scheduled {len(jobs)} background jobs")
        return jobs
    
    async def _generate_collab_suggestions(self) -> List[Dict]:
        """Generate collaboration suggestions based on user activity."""
        suggestions = []
        
        # Find users with similar engagement patterns
        active_users = [user for user in self.users.values() if user.weekly_engagement > 0]
        
        for i, user1 in enumerate(active_users):
            for user2 in active_users[i+1:]:
                if (user1.user_id != user2.user_id and 
                    len(set(user1.communities) & set(user2.communities)) > 0):
                    
                    suggestion = {
                        "user1_id": user1.user_id,
                        "user2_id": user2.user_id,
                        "reason": "Similar community interests",
                        "score": len(set(user1.communities) & set(user2.communities))
                    }
                    suggestions.append(suggestion)
        
        logger.info(f"Generated {len(suggestions)} collaboration suggestions")
        return suggestions
    
    async def _log_engagement_metrics(self):
        """Log engagement metrics for analysis."""
        metrics = {
            "total_users": len(self.users),
            "total_communities": len(self.communities),
            "total_collaborations": len(self.collaborations),
            "total_templates": len(self.templates),
            "avg_xp_per_user": sum(user.xp_points for user in self.users.values()) / max(len(self.users), 1),
            "timestamp": datetime.now().isoformat()
        }
        
        # Save metrics to file
        metrics_file = Path("./data/engagement_metrics.json")
        metrics_file.parent.mkdir(exist_ok=True)
        
        with open(metrics_file, "a") as f:
            f.write(json.dumps(metrics) + "\n")
        
        logger.info("Logged engagement metrics")
        return metrics
    
    async def get_api_hooks(self) -> Dict[str, Any]:
        """Get API hooks for external integrations."""
        hooks = {
            "communities": {
                "list": "/api/communities",
                "create": "/api/communities",
                "join": "/api/communities/{id}/join"
            },
            "users": {
                "profile": "/api/users/{id}",
                "leaderboard": "/api/users/leaderboard"
            },
            "content": {
                "templates": "/api/content/templates",
                "generate": "/api/content/generate",
                "share": "/api/content/share"
            },
            "collaborations": {
                "create": "/api/collaborations",
                "list": "/api/collaborations"
            }
        }
        
        return hooks
    
    async def export_data_for_external_network(self, network_name: str) -> Dict[str, Any]:
        """Export data for external network integration."""
        export_data = {
            "network": network_name,
            "timestamp": datetime.now().isoformat(),
            "communities": [
                {
                    "id": comm.id,
                    "name": comm.name,
                    "type": comm.type.value,
                    "member_count": len(comm.members)
                }
                for comm in self.communities.values()
            ],
            "top_users": [
                {
                    "user_id": user.user_id,
                    "username": user.username,
                    "xp_points": user.xp_points,
                    "level": user.level
                }
                for user in sorted(self.users.values(), key=lambda u: u.xp_points, reverse=True)[:10]
            ],
            "popular_templates": [
                {
                    "id": template.id,
                    "name": template.name,
                    "type": template.type,
                    "usage_count": template.usage_count
                }
                for template in sorted(self.templates.values(), key=lambda t: t.usage_count, reverse=True)[:5]
            ]
        }
        
        logger.info(f"Exported data for network: {network_name}")
        return export_data

# Example usage and testing
async def test_growth_engine():
    """Test the growth engine functionality."""
    engine = GrowthEngine()
    
    # Create test users
    user1 = await engine.create_user_profile("user1", "alice_social")
    user2 = await engine.create_user_profile("user2", "bob_creator")
    
    # Join communities
    await engine.join_community("user1", "niche-finder-001")
    await engine.join_community("user2", "problem-solver-001")
    
    # Award badges
    await engine.award_badge("user1", BadgeType.FIRST_COMMENT)
    await engine.award_badge("user2", BadgeType.CONTENT_CREATOR)
    
    # Create collaboration
    collab_id = await engine.create_collaboration("user1", "user2", "instagram", "carousel")
    
    # Generate content
    content = await engine.generate_content_with_template("carousel-template-001", {
        "title": "Social Media Growth Tips",
        "problem": "Low engagement rates",
        "solution": "Optimize posting times"
    })
    
    # Update leaderboard
    leaderboard = await engine.update_leaderboard()
    
    # Schedule jobs
    jobs = await engine.schedule_background_jobs()
    
    # Get API hooks
    hooks = await engine.get_api_hooks()
    
    logger.info("Growth engine test completed successfully")
    return {
        "users_created": len(engine.users),
        "communities": len(engine.communities),
        "collaborations": len(engine.collaborations),
        "leaderboard": leaderboard[:3],
        "jobs_scheduled": len(jobs)
    }

if __name__ == "__main__":
    asyncio.run(test_growth_engine()) 