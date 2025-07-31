"""
Content Management System
========================

Manages content creation, scheduling, and optimization for all social media platforms.
Provides tools for:
- Content creation and editing
- Multi-platform content adaptation
- Scheduling and automation
- Performance tracking
- Content templates and libraries
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import random
import re

from project_config import config
from social_media_automation import PostContent, ContentType, PlatformType
from setup_logging import setup_logging

logger = setup_logging("content_manager", log_dir=config.LOG_DIR)

class ContentCategory(Enum):
    PROMOTIONAL = "promotional"
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    NEWS = "news"
    PERSONAL = "personal"
    INTERACTIVE = "interactive"

class ContentStatus(Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    ARCHIVED = "archived"

@dataclass
class ContentTemplate:
    """Template for creating consistent content."""
    name: str
    category: ContentCategory
    base_text: str
    hashtags: List[str]
    mentions: List[str]
    platforms: List[PlatformType]
    media_requirements: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, str]] = None

@dataclass
class ContentCampaign:
    """Represents a content campaign across multiple platforms."""
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    posts: List[PostContent]
    platforms: List[PlatformType]
    status: ContentStatus = ContentStatus.DRAFT

class ContentManager:
    """Manages content creation, scheduling, and optimization."""
    
    def __init__(self):
        self.content_dir = Path("content")
        self.content_dir.mkdir(exist_ok=True)
        
        self.templates_dir = self.content_dir / "templates"
        self.templates_dir.mkdir(exist_ok=True)
        
        self.campaigns_dir = self.content_dir / "campaigns"
        self.campaigns_dir.mkdir(exist_ok=True)
        
        self.scheduled_dir = self.content_dir / "scheduled"
        self.scheduled_dir.mkdir(exist_ok=True)
        
        self.templates = self.load_templates()
        self.campaigns = self.load_campaigns()
        
        logger.info("✅ Content Manager initialized")
    
    def load_templates(self) -> Dict[str, ContentTemplate]:
        """Load content templates from files."""
        templates = {}
        
        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    template = ContentTemplate(**data)
                    templates[template.name] = template
            except Exception as e:
                logger.error(f"❌ Error loading template {template_file}: {e}")
        
        logger.info(f"✅ Loaded {len(templates)} content templates")
        return templates
    
    def save_template(self, template: ContentTemplate):
        """Save a content template to file."""
        try:
            template_file = self.templates_dir / f"{template.name}.json"
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(template), f, indent=2, default=str)
            
            self.templates[template.name] = template
            logger.info(f"✅ Saved template: {template.name}")
            
        except Exception as e:
            logger.error(f"❌ Error saving template {template.name}: {e}")
    
    def create_template(self, name: str, category: ContentCategory, base_text: str,
                       hashtags: List[str], platforms: List[PlatformType],
                       mentions: List[str] = None, variables: Dict[str, str] = None) -> ContentTemplate:
        """Create a new content template."""
        template = ContentTemplate(
            name=name,
            category=category,
            base_text=base_text,
            hashtags=hashtags,
            mentions=mentions or [],
            platforms=platforms,
            variables=variables or {}
        )
        
        self.save_template(template)
        return template
    
    def generate_content_from_template(self, template_name: str, variables: Dict[str, str] = None) -> PostContent:
        """Generate content from a template with variable substitution."""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.templates[template_name]
        variables = variables or {}
        
        # Substitute variables in base text
        text = template.base_text
        for var_name, var_value in variables.items():
            text = text.replace(f"{{{var_name}}}", var_value)
        
        # Add hashtags and mentions
        if template.hashtags:
            text += "\n\n" + " ".join([f"#{tag}" for tag in template.hashtags])
        
        if template.mentions:
            text += "\n\n" + " ".join([f"@{mention}" for mention in template.mentions])
        
        return PostContent(
            text=text,
            content_type=ContentType.TEXT,
            hashtags=template.hashtags,
            mentions=template.mentions,
            platform_specific={
                "template": template_name,
                "category": template.category.value,
                "platforms": [p.value for p in template.platforms]
            }
        )
    
    def create_campaign(self, name: str, description: str, start_date: datetime,
                       end_date: datetime, platforms: List[PlatformType]) -> ContentCampaign:
        """Create a new content campaign."""
        campaign = ContentCampaign(
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            posts=[],
            platforms=platforms
        )
        
        self.campaigns[name] = campaign
        self.save_campaign(campaign)
        
        logger.info(f"✅ Created campaign: {name}")
        return campaign
    
    def add_post_to_campaign(self, campaign_name: str, post: PostContent):
        """Add a post to a campaign."""
        if campaign_name not in self.campaigns:
            raise ValueError(f"Campaign '{campaign_name}' not found")
        
        campaign = self.campaigns[campaign_name]
        campaign.posts.append(post)
        
        self.save_campaign(campaign)
        logger.info(f"✅ Added post to campaign: {campaign_name}")
    
    def save_campaign(self, campaign: ContentCampaign):
        """Save a campaign to file."""
        try:
            campaign_file = self.campaigns_dir / f"{campaign.name}.json"
            
            # Convert campaign to dict for JSON serialization
            campaign_dict = {
                "name": campaign.name,
                "description": campaign.description,
                "start_date": campaign.start_date.isoformat(),
                "end_date": campaign.end_date.isoformat(),
                "platforms": [p.value for p in campaign.platforms],
                "status": campaign.status.value,
                "posts": []
            }
            
            # Convert posts to dict
            for post in campaign.posts:
                post_dict = {
                    "text": post.text,
                    "content_type": post.content_type.value,
                    "hashtags": post.hashtags,
                    "mentions": post.mentions,
                    "scheduled_time": post.scheduled_time.isoformat() if post.scheduled_time else None,
                    "platform_specific": post.platform_specific
                }
                campaign_dict["posts"].append(post_dict)
            
            with open(campaign_file, 'w', encoding='utf-8') as f:
                json.dump(campaign_dict, f, indent=2)
            
        except Exception as e:
            logger.error(f"❌ Error saving campaign {campaign.name}: {e}")
    
    def load_campaigns(self) -> Dict[str, ContentCampaign]:
        """Load campaigns from files."""
        campaigns = {}
        
        for campaign_file in self.campaigns_dir.glob("*.json"):
            try:
                with open(campaign_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Convert back to proper types
                    campaign = ContentCampaign(
                        name=data["name"],
                        description=data["description"],
                        start_date=datetime.fromisoformat(data["start_date"]),
                        end_date=datetime.fromisoformat(data["end_date"]),
                        platforms=[PlatformType(p) for p in data["platforms"]],
                        status=ContentStatus(data["status"]),
                        posts=[]
                    )
                    
                    # Convert posts back to PostContent objects
                    for post_data in data["posts"]:
                        post = PostContent(
                            text=post_data["text"],
                            content_type=ContentType(post_data["content_type"]),
                            hashtags=post_data.get("hashtags"),
                            mentions=post_data.get("mentions"),
                            scheduled_time=datetime.fromisoformat(post_data["scheduled_time"]) if post_data.get("scheduled_time") else None,
                            platform_specific=post_data.get("platform_specific")
                        )
                        campaign.posts.append(post)
                    
                    campaigns[campaign.name] = campaign
                    
            except Exception as e:
                logger.error(f"❌ Error loading campaign {campaign_file}: {e}")
        
        logger.info(f"✅ Loaded {len(campaigns)} campaigns")
        return campaigns
    
    def schedule_campaign(self, campaign_name: str, automation_system) -> Dict:
        """Schedule all posts in a campaign."""
        if campaign_name not in self.campaigns:
            raise ValueError(f"Campaign '{campaign_name}' not found")
        
        campaign = self.campaigns[campaign_name]
        results = []
        
        # Calculate posting schedule
        total_posts = len(campaign.posts)
        campaign_duration = (campaign.end_date - campaign.start_date).total_seconds()
        interval = campaign_duration / total_posts if total_posts > 0 else 0
        
        for i, post in enumerate(campaign.posts):
            # Calculate scheduled time
            scheduled_time = campaign.start_date + timedelta(seconds=i * interval)
            post.scheduled_time = scheduled_time
            
            # Schedule the post
            try:
                result = automation_system.schedule_posts([post])
                results.append({
                    "post_index": i,
                    "scheduled_time": scheduled_time.isoformat(),
                    "result": result
                })
                
            except Exception as e:
                logger.error(f"❌ Error scheduling post {i} in campaign {campaign_name}: {e}")
                results.append({
                    "post_index": i,
                    "scheduled_time": scheduled_time.isoformat(),
                    "result": {"success": False, "error": str(e)}
                })
        
        campaign.status = ContentStatus.SCHEDULED
        self.save_campaign(campaign)
        
        return {
            "campaign_name": campaign_name,
            "total_posts": total_posts,
            "scheduled_posts": results
        }
    
    def optimize_content_for_platform(self, content: PostContent, platform: PlatformType) -> PostContent:
        """Optimize content for a specific platform."""
        optimized_content = PostContent(
            text=content.text,
            content_type=content.content_type,
            media_paths=content.media_paths,
            hashtags=content.hashtags,
            mentions=content.mentions,
            scheduled_time=content.scheduled_time,
            platform_specific=content.platform_specific or {}
        )
        
        # Platform-specific optimizations
        if platform == PlatformType.TWITTER:
            # Twitter character limit
            if len(optimized_content.text) > 280:
                optimized_content.text = optimized_content.text[:277] + "..."
        
        elif platform == PlatformType.INSTAGRAM:
            # Instagram prefers hashtags
            if optimized_content.hashtags:
                optimized_content.text += "\n\n" + " ".join([f"#{tag}" for tag in optimized_content.hashtags[:30]])
        
        elif platform == PlatformType.LINKEDIN:
            # LinkedIn prefers professional tone
            optimized_content.text = self.make_professional(optimized_content.text)
        
        elif platform == PlatformType.REDDIT:
            # Reddit prefers community-focused content
            optimized_content.text = self.make_community_focused(optimized_content.text)
        
        return optimized_content
    
    def make_professional(self, text: str) -> str:
        """Make text more professional for LinkedIn."""
        # Remove excessive emojis
        text = re.sub(r'[^\w\s@#]', '', text)
        
        # Add professional hashtags if none exist
        if not re.search(r'#\w+', text):
            text += "\n\n#professional #networking #business"
        
        return text
    
    def make_community_focused(self, text: str) -> str:
        """Make text more community-focused for Reddit."""
        # Add community-focused elements
        if not re.search(r'community|discussion|thoughts', text.lower()):
            text += "\n\nWhat are your thoughts on this?"
        
        return text
    
    def generate_content_ideas(self, category: ContentCategory, platforms: List[PlatformType]) -> List[str]:
        """Generate content ideas based on category and platforms."""
        ideas = []
        
        if category == ContentCategory.PROMOTIONAL:
            ideas = [
                "Excited to announce our latest product launch! 🚀",
                "Join us for an exclusive webinar this week",
                "Limited time offer - don't miss out!",
                "We're hiring! Join our amazing team",
                "Customer success story: How we helped [company] achieve their goals"
            ]
        
        elif category == ContentCategory.EDUCATIONAL:
            ideas = [
                "5 tips for improving your productivity",
                "The future of [industry] in 2024",
                "How to master [skill] in 30 days",
                "Common mistakes to avoid in [field]",
                "Behind the scenes: How we built [feature]"
            ]
        
        elif category == ContentCategory.ENTERTAINMENT:
            ideas = [
                "Fun fact Friday: Did you know...",
                "Team building activities that actually work",
                "Office humor: The struggle is real 😂",
                "Throwback Thursday: Remember when...",
                "Weekend vibes: What we're up to"
            ]
        
        elif category == ContentCategory.NEWS:
            ideas = [
                "Breaking: [industry] news you need to know",
                "Market update: What's happening in [sector]",
                "Industry insights: Trends to watch",
                "Company update: What's new with us",
                "Partner announcement: Excited to work with [company]"
            ]
        
        elif category == ContentCategory.PERSONAL:
            ideas = [
                "Personal reflection: What I learned this week",
                "Grateful for our amazing community",
                "Life update: What's new with me",
                "Behind the scenes of my daily routine",
                "Sharing my journey: From [start] to [current]"
            ]
        
        elif category == ContentCategory.INTERACTIVE:
            ideas = [
                "Poll: What's your favorite [topic]?",
                "Question of the day: [thought-provoking question]",
                "Share your experience: [topic]",
                "Vote: Which [option] do you prefer?",
                "Tell us: What would you like to see from us?"
            ]
        
        # Filter ideas based on platform capabilities
        filtered_ideas = []
        for idea in ideas:
            if self.is_idea_suitable_for_platforms(idea, platforms):
                filtered_ideas.append(idea)
        
        return filtered_ideas
    
    def is_idea_suitable_for_platforms(self, idea: str, platforms: List[PlatformType]) -> bool:
        """Check if a content idea is suitable for the given platforms."""
        # Simple heuristic - can be enhanced
        if PlatformType.TWITTER in platforms and len(idea) > 280:
            return False
        
        if PlatformType.INSTAGRAM in platforms and len(idea) > 2200:
            return False
        
        return True
    
    def get_content_analytics(self) -> Dict:
        """Get analytics about content performance."""
        analytics = {
            "total_templates": len(self.templates),
            "total_campaigns": len(self.campaigns),
            "campaigns_by_status": {},
            "templates_by_category": {},
            "platform_distribution": {}
        }
        
        # Count campaigns by status
        for campaign in self.campaigns.values():
            status = campaign.status.value
            analytics["campaigns_by_status"][status] = analytics["campaigns_by_status"].get(status, 0) + 1
        
        # Count templates by category
        for template in self.templates.values():
            category = template.category.value
            analytics["templates_by_category"][category] = analytics["templates_by_category"].get(category, 0) + 1
        
        # Count platform distribution
        for template in self.templates.values():
            for platform in template.platforms:
                platform_name = platform.value
                analytics["platform_distribution"][platform_name] = analytics["platform_distribution"].get(platform_name, 0) + 1
        
        return analytics
    
    def export_campaign(self, campaign_name: str, format: str = "json") -> str:
        """Export a campaign to various formats."""
        if campaign_name not in self.campaigns:
            raise ValueError(f"Campaign '{campaign_name}' not found")
        
        campaign = self.campaigns[campaign_name]
        
        if format == "json":
            return json.dumps(asdict(campaign), indent=2, default=str)
        
        elif format == "csv":
            # Create CSV format
            csv_lines = ["Post,Text,Platforms,Scheduled Time"]
            for i, post in enumerate(campaign.posts):
                platforms = ",".join([p.value for p in campaign.platforms])
                scheduled_time = post.scheduled_time.isoformat() if post.scheduled_time else "Not scheduled"
                csv_lines.append(f"Post {i+1},\"{post.text}\",{platforms},{scheduled_time}")
            
            return "\n".join(csv_lines)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_campaign(self, campaign_data: Dict) -> ContentCampaign:
        """Import a campaign from data."""
        try:
            campaign = ContentCampaign(
                name=campaign_data["name"],
                description=campaign_data["description"],
                start_date=datetime.fromisoformat(campaign_data["start_date"]),
                end_date=datetime.fromisoformat(campaign_data["end_date"]),
                platforms=[PlatformType(p) for p in campaign_data["platforms"]],
                status=ContentStatus(campaign_data["status"]),
                posts=[]
            )
            
            # Convert posts
            for post_data in campaign_data["posts"]:
                post = PostContent(
                    text=post_data["text"],
                    content_type=ContentType(post_data["content_type"]),
                    hashtags=post_data.get("hashtags"),
                    mentions=post_data.get("mentions"),
                    scheduled_time=datetime.fromisoformat(post_data["scheduled_time"]) if post_data.get("scheduled_time") else None,
                    platform_specific=post_data.get("platform_specific")
                )
                campaign.posts.append(post)
            
            self.campaigns[campaign.name] = campaign
            self.save_campaign(campaign)
            
            logger.info(f"✅ Imported campaign: {campaign.name}")
            return campaign
            
        except Exception as e:
            logger.error(f"❌ Error importing campaign: {e}")
            raise

if __name__ == "__main__":
    # Example usage
    content_manager = ContentManager()
    
    # Create a template
    template = content_manager.create_template(
        name="product_launch",
        category=ContentCategory.PROMOTIONAL,
        base_text="Excited to announce our latest product: {product_name}! 🚀",
        hashtags=["launch", "innovation", "product"],
        platforms=[PlatformType.LINKEDIN, PlatformType.TWITTER, PlatformType.FACEBOOK],
        variables={"product_name": "AI Assistant"}
    )
    
    # Generate content from template
    content = content_manager.generate_content_from_template(
        "product_launch",
        variables={"product_name": "Smart Analytics"}
    )
    
    # Create a campaign
    campaign = content_manager.create_campaign(
        name="Q1_Launch_Campaign",
        description="Product launch campaign for Q1",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=30),
        platforms=[PlatformType.LINKEDIN, PlatformType.TWITTER]
    )
    
    # Add posts to campaign
    content_manager.add_post_to_campaign("Q1_Launch_Campaign", content)
    
    # Get analytics
    analytics = content_manager.get_content_analytics()
    print(f"Content Analytics: {analytics}")
    
    # Generate content ideas
    ideas = content_manager.generate_content_ideas(
        ContentCategory.EDUCATIONAL,
        [PlatformType.LINKEDIN, PlatformType.TWITTER]
    )
    print(f"Content Ideas: {ideas}") 