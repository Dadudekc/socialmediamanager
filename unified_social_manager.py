"""
Unified Social Media Manager
===========================

A comprehensive system that manages all social media platforms:
- LinkedIn: Professional networking and content
- Twitter: Micro-blogging and engagement
- Facebook: Community building and page management
- Instagram: Visual content and stories
- Reddit: Community engagement and moderation
- Discord: Server management and communication
- Stocktwits: Stock-related content and analysis

Provides unified interface for:
- Multi-platform posting and scheduling
- Content management and optimization
- Analytics and performance tracking
- Automated engagement and networking
- Campaign management
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import json
import time

from project_config import config
from platform_login_manager import run_all_logins
from social_media_automation import SocialMediaAutomation, PostContent, PlatformType, AutomationConfig
from content_manager import ContentManager, ContentCategory, ContentCampaign
from setup_logging import setup_logging

logger = setup_logging("unified_manager", log_dir=config.LOG_DIR)

class UnifiedSocialManager:
    """Unified manager for all social media platforms."""
    
    def __init__(self):
        self.automation = SocialMediaAutomation()
        self.content_manager = ContentManager()
        self.active_campaigns = {}
        self.scheduled_tasks = []
        
        # Platform status tracking
        self.platform_status = {
            platform: {"connected": False, "last_check": None}
            for platform in PlatformType
        }
        
        logger.info("✅ Unified Social Media Manager initialized")
    
    def initialize_all_platforms(self):
        """Initialize connections to all platforms."""
        logger.info("🔗 Initializing all platform connections...")
        
        try:
            # Run login process for all platforms
            run_all_logins()
            
            # Initialize automation driver
            self.automation.initialize_driver()
            
            # Update platform status
            for platform in PlatformType:
                self.platform_status[platform]["connected"] = True
                self.platform_status[platform]["last_check"] = datetime.now()
            
            logger.info("✅ All platforms initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing platforms: {e}")
            return False
    
    def post_to_all_platforms(self, text: str, hashtags: List[str] = None,
                             mentions: List[str] = None, scheduled_time: datetime = None) -> Dict:
        """Post content to all platforms simultaneously."""
        try:
            # Create post content
            content = PostContent(
                text=text,
                content_type=self.automation.platform_handlers[PlatformType.LINKEDIN].__class__.__name__.replace("Automation", "").lower(),
                hashtags=hashtags or [],
                mentions=mentions or [],
                scheduled_time=scheduled_time
            )
            
            # Post to all platforms
            results = self.automation.post_to_all_platforms(content)
            
            logger.info(f"✅ Posted to {len([r for r in results.values() if r.get('success')])} platforms")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error posting to all platforms: {e}")
            return {"error": str(e)}
    
    def post_to_specific_platforms(self, text: str, platforms: List[PlatformType],
                                 hashtags: List[str] = None, mentions: List[str] = None) -> Dict:
        """Post content to specific platforms."""
        try:
            content = PostContent(
                text=text,
                content_type=self.automation.platform_handlers[PlatformType.LINKEDIN].__class__.__name__.replace("Automation", "").lower(),
                hashtags=hashtags or [],
                mentions=mentions or []
            )
            
            results = {}
            for platform in platforms:
                result = self.automation.post_to_platform(platform, content)
                results[platform.value] = result
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error posting to specific platforms: {e}")
            return {"error": str(e)}
    
    def create_and_schedule_campaign(self, name: str, description: str,
                                   start_date: datetime, end_date: datetime,
                                   platforms: List[PlatformType], posts: List[str]) -> Dict:
        """Create and schedule a content campaign."""
        try:
            # Create campaign
            campaign = self.content_manager.create_campaign(
                name=name,
                description=description,
                start_date=start_date,
                end_date=end_date,
                platforms=platforms
            )
            
            # Add posts to campaign
            for post_text in posts:
                content = PostContent(
                    text=post_text,
                    content_type=self.automation.platform_handlers[PlatformType.LINKEDIN].__class__.__name__.replace("Automation", "").lower()
                )
                self.content_manager.add_post_to_campaign(name, content)
            
            # Schedule campaign
            schedule_result = self.content_manager.schedule_campaign(name, self.automation)
            
            self.active_campaigns[name] = campaign
            
            logger.info(f"✅ Created and scheduled campaign: {name}")
            return {
                "campaign_name": name,
                "total_posts": len(posts),
                "platforms": [p.value for p in platforms],
                "schedule_result": schedule_result
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating campaign: {e}")
            return {"error": str(e)}
    
    def engage_with_content(self, platforms: List[PlatformType] = None,
                          engagement_types: List[str] = None) -> Dict:
        """Engage with content on specified platforms."""
        if platforms is None:
            platforms = list(PlatformType)
        
        if engagement_types is None:
            engagement_types = ["like", "follow"]
        
        results = {}
        
        for platform in platforms:
            platform_results = {}
            for engagement_type in engagement_types:
                try:
                    result = self.automation.engage_with_content(platform, engagement_type)
                    platform_results[engagement_type] = result
                except Exception as e:
                    logger.error(f"❌ Error engaging on {platform.value}: {e}")
                    platform_results[engagement_type] = {"success": False, "error": str(e)}
            
            results[platform.value] = platform_results
        
        return results
    
    def follow_users(self, usernames: List[str], platforms: List[PlatformType] = None) -> Dict:
        """Follow users on specified platforms."""
        if platforms is None:
            platforms = list(PlatformType)
        
        results = {}
        
        for platform in platforms:
            try:
                result = self.automation.follow_users(platform, usernames)
                results[platform.value] = result
            except Exception as e:
                logger.error(f"❌ Error following users on {platform.value}: {e}")
                results[platform.value] = {"success": False, "error": str(e)}
        
        return results
    
    def get_analytics_for_all_platforms(self) -> Dict:
        """Get analytics from all platforms."""
        analytics = {}
        
        for platform in PlatformType:
            try:
                platform_analytics = self.automation.get_analytics(platform)
                analytics[platform.value] = platform_analytics
            except Exception as e:
                logger.error(f"❌ Error getting analytics for {platform.value}: {e}")
                analytics[platform.value] = {"success": False, "error": str(e)}
        
        return analytics
    
    def generate_content_ideas(self, category: ContentCategory,
                             platforms: List[PlatformType] = None) -> List[str]:
        """Generate content ideas for specified category and platforms."""
        if platforms is None:
            platforms = list(PlatformType)
        
        return self.content_manager.generate_content_ideas(category, platforms)
    
    def create_content_template(self, name: str, category: ContentCategory,
                              base_text: str, hashtags: List[str],
                              platforms: List[PlatformType],
                              mentions: List[str] = None) -> Dict:
        """Create a content template."""
        try:
            template = self.content_manager.create_template(
                name=name,
                category=category,
                base_text=base_text,
                hashtags=hashtags,
                platforms=platforms,
                mentions=mentions
            )
            
            return {
                "success": True,
                "template_name": template.name,
                "category": template.category.value,
                "platforms": [p.value for p in template.platforms]
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating template: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_content_from_template(self, template_name: str,
                                    variables: Dict[str, str] = None) -> Dict:
        """Generate content from a template."""
        try:
            content = self.content_manager.generate_content_from_template(
                template_name, variables
            )
            
            return {
                "success": True,
                "content": content.text,
                "hashtags": content.hashtags,
                "mentions": content.mentions
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating content from template: {e}")
            return {"success": False, "error": str(e)}
    
    def optimize_content_for_platforms(self, text: str, platforms: List[PlatformType]) -> Dict:
        """Optimize content for specific platforms."""
        try:
            content = PostContent(
                text=text,
                content_type=self.automation.platform_handlers[PlatformType.LINKEDIN].__class__.__name__.replace("Automation", "").lower()
            )
            
            optimized_content = {}
            for platform in platforms:
                optimized = self.content_manager.optimize_content_for_platform(content, platform)
                optimized_content[platform.value] = optimized.text
            
            return {
                "success": True,
                "original_text": text,
                "optimized_content": optimized_content
            }
            
        except Exception as e:
            logger.error(f"❌ Error optimizing content: {e}")
            return {"success": False, "error": str(e)}
    
    def get_content_analytics(self) -> Dict:
        """Get content management analytics."""
        return self.content_manager.get_content_analytics()
    
    def get_platform_status(self) -> Dict:
        """Get status of all platforms."""
        return self.platform_status
    
    def export_campaign(self, campaign_name: str, format: str = "json") -> Dict:
        """Export a campaign."""
        try:
            export_data = self.content_manager.export_campaign(campaign_name, format)
            
            return {
                "success": True,
                "campaign_name": campaign_name,
                "format": format,
                "data": export_data
            }
            
        except Exception as e:
            logger.error(f"❌ Error exporting campaign: {e}")
            return {"success": False, "error": str(e)}
    
    def import_campaign(self, campaign_data: Dict) -> Dict:
        """Import a campaign."""
        try:
            campaign = self.content_manager.import_campaign(campaign_data)
            
            return {
                "success": True,
                "campaign_name": campaign.name,
                "total_posts": len(campaign.posts),
                "platforms": [p.value for p in campaign.platforms]
            }
            
        except Exception as e:
            logger.error(f"❌ Error importing campaign: {e}")
            return {"success": False, "error": str(e)}
    
    def run_automated_engagement(self, duration_minutes: int = 30) -> Dict:
        """Run automated engagement for a specified duration."""
        try:
            logger.info(f"🤖 Starting automated engagement for {duration_minutes} minutes")
            
            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            engagement_results = []
            
            while datetime.now() < end_time:
                # Engage with content on random platforms
                platforms = random.sample(list(PlatformType), min(3, len(PlatformType)))
                engagement_types = random.sample(["like", "follow", "comment"], 2)
                
                for platform in platforms:
                    for engagement_type in engagement_types:
                        try:
                            result = self.automation.engage_with_content(platform, engagement_type)
                            engagement_results.append({
                                "platform": platform.value,
                                "engagement_type": engagement_type,
                                "timestamp": datetime.now().isoformat(),
                                "result": result
                            })
                            
                            # Add delay between engagements
                            time.sleep(random.randint(30, 120))
                            
                        except Exception as e:
                            logger.error(f"❌ Error in automated engagement: {e}")
                
                # Wait before next round
                time.sleep(random.randint(300, 600))  # 5-10 minutes
            
            logger.info(f"✅ Automated engagement completed. {len(engagement_results)} actions performed")
            
            return {
                "success": True,
                "duration_minutes": duration_minutes,
                "total_actions": len(engagement_results),
                "results": engagement_results
            }
            
        except Exception as e:
            logger.error(f"❌ Error in automated engagement: {e}")
            return {"success": False, "error": str(e)}
    
    def schedule_recurring_posts(self, text: str, platforms: List[PlatformType],
                               interval_hours: int = 24, duration_days: int = 7) -> Dict:
        """Schedule recurring posts."""
        try:
            start_time = datetime.now()
            end_time = start_time + timedelta(days=duration_days)
            
            scheduled_posts = []
            current_time = start_time
            
            while current_time < end_time:
                content = PostContent(
                    text=text,
                    content_type=self.automation.platform_handlers[PlatformType.LINKEDIN].__class__.__name__.replace("Automation", "").lower(),
                    scheduled_time=current_time
                )
                
                # Schedule post
                result = self.automation.schedule_posts([content])
                scheduled_posts.append({
                    "scheduled_time": current_time.isoformat(),
                    "result": result
                })
                
                # Move to next interval
                current_time += timedelta(hours=interval_hours)
            
            return {
                "success": True,
                "total_posts_scheduled": len(scheduled_posts),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "interval_hours": interval_hours,
                "scheduled_posts": scheduled_posts
            }
            
        except Exception as e:
            logger.error(f"❌ Error scheduling recurring posts: {e}")
            return {"success": False, "error": str(e)}
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary."""
        try:
            # Get analytics from all platforms
            platform_analytics = self.get_analytics_for_all_platforms()
            
            # Get content analytics
            content_analytics = self.get_content_analytics()
            
            # Get platform status
            platform_status = self.get_platform_status()
            
            # Get post history
            post_history = self.automation.get_post_history()
            
            return {
                "platform_analytics": platform_analytics,
                "content_analytics": content_analytics,
                "platform_status": platform_status,
                "post_history": post_history,
                "active_campaigns": len(self.active_campaigns),
                "total_templates": len(self.content_manager.templates),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting performance summary: {e}")
            return {"error": str(e)}
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if self.automation.driver:
                self.automation.close_driver()
            
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")

def main():
    """Main function for testing the unified manager."""
    manager = UnifiedSocialManager()
    
    try:
        # Initialize all platforms
        if not manager.initialize_all_platforms():
            logger.error("❌ Failed to initialize platforms")
            return
        
        # Example: Post to all platforms
        post_result = manager.post_to_all_platforms(
            text="Excited to share our latest project! 🚀 #innovation #tech",
            hashtags=["innovation", "tech", "automation"]
        )
        print(f"Post result: {post_result}")
        
        # Example: Create a campaign
        campaign_result = manager.create_and_schedule_campaign(
            name="Test_Campaign",
            description="Test campaign for demonstration",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            platforms=[PlatformType.LINKEDIN, PlatformType.TWITTER],
            posts=[
                "Day 1: Introduction to our new project",
                "Day 2: Key features and benefits",
                "Day 3: Customer testimonials",
                "Day 4: Technical deep dive",
                "Day 5: Future roadmap"
            ]
        )
        print(f"Campaign result: {campaign_result}")
        
        # Example: Get performance summary
        summary = manager.get_performance_summary()
        print(f"Performance summary: {summary}")
        
        # Example: Generate content ideas
        ideas = manager.generate_content_ideas(
            ContentCategory.EDUCATIONAL,
            [PlatformType.LINKEDIN, PlatformType.TWITTER]
        )
        print(f"Content ideas: {ideas}")
        
    except Exception as e:
        logger.error(f"❌ Error in main: {e}")
    
    finally:
        manager.cleanup()

if __name__ == "__main__":
    main() 