"""
Social Media Automation System
=============================

Provides comprehensive automation capabilities for all supported social media platforms:
- LinkedIn: Posting, networking, content management
- Twitter: Tweeting, following, engagement
- Facebook: Posting, group management, page management
- Instagram: Posting, stories, engagement
- Reddit: Posting, commenting, moderation
- Discord: Message sending, server management
- Stocktwits: Stock-related posting and analysis

Each platform has specific automation features tailored to its capabilities and use cases.
"""

import os
import time
import random
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

from project_config import config
from platform_login_manager import get_driver, load_cookies
from setup_logging import setup_logging

logger = setup_logging("social_automation", log_dir=config.LOG_DIR)

class PlatformType(Enum):
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    REDDIT = "reddit"
    DISCORD = "discord"
    STOCKTWITS = "stocktwits"

class ContentType(Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    LINK = "link"
    POLL = "poll"

@dataclass
class PostContent:
    """Represents content to be posted on social media."""
    text: str
    content_type: ContentType
    media_paths: Optional[List[str]] = None
    hashtags: Optional[List[str]] = None
    mentions: Optional[List[str]] = None
    scheduled_time: Optional[datetime] = None
    platform_specific: Optional[Dict[str, Any]] = None

@dataclass
class AutomationConfig:
    """Configuration for automation behavior."""
    max_posts_per_day: int = 10
    min_delay_between_posts: int = 300  # 5 minutes
    max_delay_between_posts: int = 1800  # 30 minutes
    enable_engagement: bool = True
    enable_following: bool = True
    enable_networking: bool = True
    safe_mode: bool = True  # Adds random delays and human-like behavior

class SocialMediaAutomation:
    """Main automation class for all social media platforms."""
    
    def __init__(self, config: AutomationConfig = None):
        self.config = config or AutomationConfig()
        self.driver = None
        self.platform_handlers = {
            PlatformType.LINKEDIN: LinkedInAutomation(),
            PlatformType.TWITTER: TwitterAutomation(),
            PlatformType.FACEBOOK: FacebookAutomation(),
            PlatformType.INSTAGRAM: InstagramAutomation(),
            PlatformType.REDDIT: RedditAutomation(),
            PlatformType.DISCORD: DiscordAutomation(),
            PlatformType.STOCKTWITS: StocktwitsAutomation()
        }
        self.post_history = []
        
        logger.info("✅ Social Media Automation initialized")
    
    def initialize_driver(self):
        """Initialize the web driver."""
        self.driver = get_driver()
        logger.info("✅ Web driver initialized")
    
    def close_driver(self):
        """Close the web driver."""
        if self.driver:
            self.driver.quit()
            logger.info("✅ Web driver closed")
    
    def post_to_platform(self, platform: PlatformType, content: PostContent) -> Dict:
        """Post content to a specific platform."""
        try:
            if not self.driver:
                self.initialize_driver()
            
            handler = self.platform_handlers[platform]
            result = handler.post_content(self.driver, content, self.config)
            
            # Log the post
            self.post_history.append({
                "platform": platform.value,
                "content": content.text[:100] + "..." if len(content.text) > 100 else content.text,
                "timestamp": datetime.now().isoformat(),
                "success": result.get("success", False)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error posting to {platform.value}: {e}")
            return {"success": False, "error": str(e)}
    
    def post_to_all_platforms(self, content: PostContent) -> Dict:
        """Post content to all platforms."""
        results = {}
        
        for platform in PlatformType:
            try:
                logger.info(f"📝 Posting to {platform.value}...")
                result = self.post_to_platform(platform, content)
                results[platform.value] = result
                
                # Add delay between platforms
                if self.config.safe_mode:
                    delay = random.randint(30, 120)
                    logger.info(f"⏳ Waiting {delay} seconds before next platform...")
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"❌ Error posting to {platform.value}: {e}")
                results[platform.value] = {"success": False, "error": str(e)}
        
        return results
    
    def engage_with_content(self, platform: PlatformType, engagement_type: str = "like") -> Dict:
        """Engage with content on a platform (like, comment, share, etc.)."""
        try:
            if not self.driver:
                self.initialize_driver()
            
            handler = self.platform_handlers[platform]
            return handler.engage_with_content(self.driver, engagement_type, self.config)
            
        except Exception as e:
            logger.error(f"❌ Error engaging on {platform.value}: {e}")
            return {"success": False, "error": str(e)}
    
    def follow_users(self, platform: PlatformType, usernames: List[str]) -> Dict:
        """Follow users on a platform."""
        try:
            if not self.driver:
                self.initialize_driver()
            
            handler = self.platform_handlers[platform]
            return handler.follow_users(self.driver, usernames, self.config)
            
        except Exception as e:
            logger.error(f"❌ Error following users on {platform.value}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_analytics(self, platform: PlatformType) -> Dict:
        """Get analytics for a platform."""
        try:
            if not self.driver:
                self.initialize_driver()
            
            handler = self.platform_handlers[platform]
            return handler.get_analytics(self.driver)
            
        except Exception as e:
            logger.error(f"❌ Error getting analytics for {platform.value}: {e}")
            return {"success": False, "error": str(e)}
    
    def schedule_posts(self, posts: List[PostContent]) -> Dict:
        """Schedule multiple posts across platforms."""
        results = []
        
        for post in posts:
            if post.scheduled_time:
                # Calculate delay until scheduled time
                now = datetime.now()
                delay = (post.scheduled_time - now).total_seconds()
                
                if delay > 0:
                    logger.info(f"⏰ Scheduling post for {post.scheduled_time}")
                    time.sleep(delay)
                
                result = self.post_to_all_platforms(post)
                results.append(result)
                
                # Add delay between posts
                if self.config.safe_mode:
                    delay = random.randint(
                        self.config.min_delay_between_posts,
                        self.config.max_delay_between_posts
                    )
                    time.sleep(delay)
        
        return {"scheduled_posts": results}
    
    def get_post_history(self) -> List[Dict]:
        """Get history of posts made."""
        return self.post_history

class BasePlatformAutomation:
    """Base class for platform-specific automation."""
    
    def __init__(self):
        self.wait_timeout = 10
    
    def wait_for_element(self, driver, by, value, timeout=None):
        """Wait for an element to be present."""
        timeout = timeout or self.wait_timeout
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.presence_of_element_located((by, value)))
    
    def wait_for_clickable(self, driver, by, value, timeout=None):
        """Wait for an element to be clickable."""
        timeout = timeout or self.wait_timeout
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.element_to_be_clickable((by, value)))
    
    def safe_click(self, driver, element):
        """Safely click an element with scrolling."""
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(1)
        element.click()
    
    def human_like_delay(self, min_delay=1, max_delay=3):
        """Add human-like delay."""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def post_content(self, driver, content: PostContent, config: AutomationConfig) -> Dict:
        """Post content to the platform. Override in subclasses."""
        raise NotImplementedError
    
    def engage_with_content(self, driver, engagement_type: str, config: AutomationConfig) -> Dict:
        """Engage with content. Override in subclasses."""
        raise NotImplementedError
    
    def follow_users(self, driver, usernames: List[str], config: AutomationConfig) -> Dict:
        """Follow users. Override in subclasses."""
        raise NotImplementedError
    
    def get_analytics(self, driver) -> Dict:
        """Get analytics. Override in subclasses."""
        raise NotImplementedError

class LinkedInAutomation(BasePlatformAutomation):
    """LinkedIn-specific automation."""
    
    def post_content(self, driver, content: PostContent, config: AutomationConfig) -> Dict:
        try:
            # Navigate to LinkedIn
            driver.get("https://www.linkedin.com/feed/")
            self.human_like_delay()
            
            # Find the post creation button
            post_button = self.wait_for_clickable(
                driver, By.XPATH, "//button[contains(@aria-label, 'Start a post')]"
            )
            self.safe_click(driver, post_button)
            self.human_like_delay()
            
            # Find the post text area
            post_area = self.wait_for_element(
                driver, By.XPATH, "//div[@role='textbox' or @contenteditable='true']"
            )
            
            # Type the content
            post_area.clear()
            post_text = content.text
            
            # Add hashtags if provided
            if content.hashtags:
                post_text += "\n\n" + " ".join([f"#{tag}" for tag in content.hashtags])
            
            # Add mentions if provided
            if content.mentions:
                post_text += "\n\n" + " ".join([f"@{mention}" for mention in content.mentions])
            
            # Type the content character by character for human-like behavior
            for char in post_text:
                post_area.send_keys(char)
                if config.safe_mode:
                    time.sleep(random.uniform(0.01, 0.05))
            
            self.human_like_delay()
            
            # Click post button
            post_submit = self.wait_for_clickable(
                driver, By.XPATH, "//button[contains(text(), 'Post')]"
            )
            self.safe_click(driver, post_submit)
            
            logger.info("✅ LinkedIn post successful")
            return {"success": True, "platform": "linkedin"}
            
        except Exception as e:
            logger.error(f"❌ LinkedIn post failed: {e}")
            return {"success": False, "error": str(e)}
    
    def engage_with_content(self, driver, engagement_type: str, config: AutomationConfig) -> Dict:
        try:
            # Navigate to feed
            driver.get("https://www.linkedin.com/feed/")
            self.human_like_delay()
            
            # Find engagement buttons
            if engagement_type == "like":
                like_buttons = driver.find_elements(
                    By.XPATH, "//button[contains(@aria-label, 'Like')]"
                )
                for button in like_buttons[:5]:  # Like first 5 posts
                    self.safe_click(driver, button)
                    self.human_like_delay()
            
            return {"success": True, "engagement_type": engagement_type}
            
        except Exception as e:
            logger.error(f"❌ LinkedIn engagement failed: {e}")
            return {"success": False, "error": str(e)}
    
    def follow_users(self, driver, usernames: List[str], config: AutomationConfig) -> Dict:
        try:
            results = []
            
            for username in usernames:
                # Navigate to user profile
                driver.get(f"https://www.linkedin.com/in/{username}/")
                self.human_like_delay()
                
                # Find follow button
                follow_button = self.wait_for_clickable(
                    driver, By.XPATH, "//button[contains(text(), 'Follow')]"
                )
                self.safe_click(driver, follow_button)
                
                results.append({"username": username, "followed": True})
                self.human_like_delay()
            
            return {"success": True, "followed_users": results}
            
        except Exception as e:
            logger.error(f"❌ LinkedIn follow failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_analytics(self, driver) -> Dict:
        try:
            # Navigate to analytics page
            driver.get("https://www.linkedin.com/analytics/")
            self.human_like_delay()
            
            # Extract analytics data (simplified)
            analytics = {
                "profile_views": "N/A",
                "post_impressions": "N/A",
                "connection_requests": "N/A"
            }
            
            return {"success": True, "analytics": analytics}
            
        except Exception as e:
            logger.error(f"❌ LinkedIn analytics failed: {e}")
            return {"success": False, "error": str(e)}

class TwitterAutomation(BasePlatformAutomation):
    """Twitter-specific automation."""
    
    def post_content(self, driver, content: PostContent, config: AutomationConfig) -> Dict:
        try:
            # Navigate to Twitter
            driver.get("https://twitter.com/home")
            self.human_like_delay()
            
            # Find the tweet compose button
            tweet_button = self.wait_for_clickable(
                driver, By.XPATH, "//a[@aria-label='Tweet']"
            )
            self.safe_click(driver, tweet_button)
            self.human_like_delay()
            
            # Find the tweet text area
            tweet_area = self.wait_for_element(
                driver, By.XPATH, "//div[@role='textbox']"
            )
            
            # Compose tweet
            tweet_text = content.text
            
            # Add hashtags
            if content.hashtags:
                tweet_text += "\n\n" + " ".join([f"#{tag}" for tag in content.hashtags])
            
            # Add mentions
            if content.mentions:
                tweet_text += "\n\n" + " ".join([f"@{mention}" for mention in content.mentions])
            
            # Type the tweet
            for char in tweet_text:
                tweet_area.send_keys(char)
                if config.safe_mode:
                    time.sleep(random.uniform(0.01, 0.05))
            
            self.human_like_delay()
            
            # Click tweet button
            post_button = self.wait_for_clickable(
                driver, By.XPATH, "//div[@data-testid='tweetButton']"
            )
            self.safe_click(driver, post_button)
            
            logger.info("✅ Twitter tweet successful")
            return {"success": True, "platform": "twitter"}
            
        except Exception as e:
            logger.error(f"❌ Twitter tweet failed: {e}")
            return {"success": False, "error": str(e)}
    
    def engage_with_content(self, driver, engagement_type: str, config: AutomationConfig) -> Dict:
        try:
            # Navigate to home timeline
            driver.get("https://twitter.com/home")
            self.human_like_delay()
            
            if engagement_type == "like":
                like_buttons = driver.find_elements(
                    By.XPATH, "//div[@data-testid='like']"
                )
                for button in like_buttons[:5]:
                    self.safe_click(driver, button)
                    self.human_like_delay()
            
            elif engagement_type == "retweet":
                retweet_buttons = driver.find_elements(
                    By.XPATH, "//div[@data-testid='retweet']"
                )
                for button in retweet_buttons[:3]:
                    self.safe_click(driver, button)
                    self.human_like_delay()
            
            return {"success": True, "engagement_type": engagement_type}
            
        except Exception as e:
            logger.error(f"❌ Twitter engagement failed: {e}")
            return {"success": False, "error": str(e)}
    
    def follow_users(self, driver, usernames: List[str], config: AutomationConfig) -> Dict:
        try:
            results = []
            
            for username in usernames:
                # Navigate to user profile
                driver.get(f"https://twitter.com/{username}")
                self.human_like_delay()
                
                # Find follow button
                follow_button = self.wait_for_clickable(
                    driver, By.XPATH, "//div[@data-testid='followButton']"
                )
                self.safe_click(driver, follow_button)
                
                results.append({"username": username, "followed": True})
                self.human_like_delay()
            
            return {"success": True, "followed_users": results}
            
        except Exception as e:
            logger.error(f"❌ Twitter follow failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_analytics(self, driver) -> Dict:
        try:
            # Navigate to analytics
            driver.get("https://analytics.twitter.com/")
            self.human_like_delay()
            
            analytics = {
                "tweets": "N/A",
                "impressions": "N/A",
                "profile_visits": "N/A"
            }
            
            return {"success": True, "analytics": analytics}
            
        except Exception as e:
            logger.error(f"❌ Twitter analytics failed: {e}")
            return {"success": False, "error": str(e)}

class FacebookAutomation(BasePlatformAutomation):
    """Facebook-specific automation."""
    
    def post_content(self, driver, content: PostContent, config: AutomationConfig) -> Dict:
        try:
            # Navigate to Facebook
            driver.get("https://www.facebook.com/")
            self.human_like_delay()
            
            # Find the post creation area
            post_area = self.wait_for_element(
                driver, By.XPATH, "//div[@contenteditable='true' and @role='textbox']"
            )
            
            # Type the post
            post_text = content.text
            
            if content.hashtags:
                post_text += "\n\n" + " ".join([f"#{tag}" for tag in content.hashtags])
            
            if content.mentions:
                post_text += "\n\n" + " ".join([f"@{mention}" for mention in content.mentions])
            
            # Type the content
            for char in post_text:
                post_area.send_keys(char)
                if config.safe_mode:
                    time.sleep(random.uniform(0.01, 0.05))
            
            self.human_like_delay()
            
            # Click post button
            post_button = self.wait_for_clickable(
                driver, By.XPATH, "//div[@aria-label='Post']"
            )
            self.safe_click(driver, post_button)
            
            logger.info("✅ Facebook post successful")
            return {"success": True, "platform": "facebook"}
            
        except Exception as e:
            logger.error(f"❌ Facebook post failed: {e}")
            return {"success": False, "error": str(e)}
    
    def engage_with_content(self, driver, engagement_type: str, config: AutomationConfig) -> Dict:
        try:
            # Navigate to Facebook
            driver.get("https://www.facebook.com/")
            self.human_like_delay()
            
            if engagement_type == "like":
                like_buttons = driver.find_elements(
                    By.XPATH, "//div[@aria-label='Like']"
                )
                for button in like_buttons[:5]:
                    self.safe_click(driver, button)
                    self.human_like_delay()
            
            return {"success": True, "engagement_type": engagement_type}
            
        except Exception as e:
            logger.error(f"❌ Facebook engagement failed: {e}")
            return {"success": False, "error": str(e)}
    
    def follow_users(self, driver, usernames: List[str], config: AutomationConfig) -> Dict:
        try:
            results = []
            
            for username in usernames:
                # Navigate to user profile
                driver.get(f"https://www.facebook.com/{username}")
                self.human_like_delay()
                
                # Find follow button
                follow_button = self.wait_for_clickable(
                    driver, By.XPATH, "//div[@aria-label='Follow']"
                )
                self.safe_click(driver, follow_button)
                
                results.append({"username": username, "followed": True})
                self.human_like_delay()
            
            return {"success": True, "followed_users": results}
            
        except Exception as e:
            logger.error(f"❌ Facebook follow failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_analytics(self, driver) -> Dict:
        try:
            # Navigate to insights
            driver.get("https://www.facebook.com/insights/")
            self.human_like_delay()
            
            analytics = {
                "page_likes": "N/A",
                "post_reach": "N/A",
                "engagement": "N/A"
            }
            
            return {"success": True, "analytics": analytics}
            
        except Exception as e:
            logger.error(f"❌ Facebook analytics failed: {e}")
            return {"success": False, "error": str(e)}

class InstagramAutomation(BasePlatformAutomation):
    """Instagram-specific automation."""
    
    def post_content(self, driver, content: PostContent, config: AutomationConfig) -> Dict:
        try:
            # Navigate to Instagram
            driver.get("https://www.instagram.com/")
            self.human_like_delay()
            
            # Find the new post button
            new_post_button = self.wait_for_clickable(
                driver, By.XPATH, "//div[@aria-label='New post']"
            )
            self.safe_click(driver, new_post_button)
            self.human_like_delay()
            
            # Upload media if provided
            if content.media_paths:
                file_input = self.wait_for_element(
                    driver, By.XPATH, "//input[@type='file']"
                )
                file_input.send_keys(content.media_paths[0])
                self.human_like_delay()
            
            # Add caption
            caption_area = self.wait_for_element(
                driver, By.XPATH, "//textarea[@aria-label='Write a caption...']"
            )
            
            caption_text = content.text
            
            if content.hashtags:
                caption_text += "\n\n" + " ".join([f"#{tag}" for tag in content.hashtags])
            
            if content.mentions:
                caption_text += "\n\n" + " ".join([f"@{mention}" for mention in content.mentions])
            
            # Type the caption
            for char in caption_text:
                caption_area.send_keys(char)
                if config.safe_mode:
                    time.sleep(random.uniform(0.01, 0.05))
            
            self.human_like_delay()
            
            # Click share button
            share_button = self.wait_for_clickable(
                driver, By.XPATH, "//div[text()='Share']"
            )
            self.safe_click(driver, share_button)
            
            logger.info("✅ Instagram post successful")
            return {"success": True, "platform": "instagram"}
            
        except Exception as e:
            logger.error(f"❌ Instagram post failed: {e}")
            return {"success": False, "error": str(e)}
    
    def engage_with_content(self, driver, engagement_type: str, config: AutomationConfig) -> Dict:
        try:
            # Navigate to Instagram
            driver.get("https://www.instagram.com/")
            self.human_like_delay()
            
            if engagement_type == "like":
                like_buttons = driver.find_elements(
                    By.XPATH, "//div[@aria-label='Like']"
                )
                for button in like_buttons[:5]:
                    self.safe_click(driver, button)
                    self.human_like_delay()
            
            return {"success": True, "engagement_type": engagement_type}
            
        except Exception as e:
            logger.error(f"❌ Instagram engagement failed: {e}")
            return {"success": False, "error": str(e)}
    
    def follow_users(self, driver, usernames: List[str], config: AutomationConfig) -> Dict:
        try:
            results = []
            
            for username in usernames:
                # Navigate to user profile
                driver.get(f"https://www.instagram.com/{username}/")
                self.human_like_delay()
                
                # Find follow button
                follow_button = self.wait_for_clickable(
                    driver, By.XPATH, "//button[text()='Follow']"
                )
                self.safe_click(driver, follow_button)
                
                results.append({"username": username, "followed": True})
                self.human_like_delay()
            
            return {"success": True, "followed_users": results}
            
        except Exception as e:
            logger.error(f"❌ Instagram follow failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_analytics(self, driver) -> Dict:
        try:
            # Navigate to insights
            driver.get("https://www.instagram.com/accounts/activity/")
            self.human_like_delay()
            
            analytics = {
                "followers": "N/A",
                "posts": "N/A",
                "engagement_rate": "N/A"
            }
            
            return {"success": True, "analytics": analytics}
            
        except Exception as e:
            logger.error(f"❌ Instagram analytics failed: {e}")
            return {"success": False, "error": str(e)}

class RedditAutomation(BasePlatformAutomation):
    """Reddit-specific automation."""
    
    def post_content(self, driver, content: PostContent, config: AutomationConfig) -> Dict:
        try:
            # Navigate to Reddit
            driver.get("https://www.reddit.com/submit")
            self.human_like_delay()
            
            # Select post type (text)
            text_tab = self.wait_for_clickable(
                driver, By.XPATH, "//button[contains(text(), 'Text')]"
            )
            self.safe_click(driver, text_tab)
            self.human_like_delay()
            
            # Find title field
            title_field = self.wait_for_element(
                driver, By.XPATH, "//textarea[@placeholder='Title']"
            )
            title_field.send_keys(content.text[:300])  # Reddit title limit
            
            # Find text field
            text_field = self.wait_for_element(
                driver, By.XPATH, "//div[@contenteditable='true']"
            )
            
            post_text = content.text
            
            if content.hashtags:
                post_text += "\n\n" + " ".join([f"#{tag}" for tag in content.hashtags])
            
            # Type the post
            for char in post_text:
                text_field.send_keys(char)
                if config.safe_mode:
                    time.sleep(random.uniform(0.01, 0.05))
            
            self.human_like_delay()
            
            # Click post button
            post_button = self.wait_for_clickable(
                driver, By.XPATH, "//button[contains(text(), 'Post')]"
            )
            self.safe_click(driver, post_button)
            
            logger.info("✅ Reddit post successful")
            return {"success": True, "platform": "reddit"}
            
        except Exception as e:
            logger.error(f"❌ Reddit post failed: {e}")
            return {"success": False, "error": str(e)}
    
    def engage_with_content(self, driver, engagement_type: str, config: AutomationConfig) -> Dict:
        try:
            # Navigate to Reddit
            driver.get("https://www.reddit.com/")
            self.human_like_delay()
            
            if engagement_type == "upvote":
                upvote_buttons = driver.find_elements(
                    By.XPATH, "//button[@aria-label='upvote']"
                )
                for button in upvote_buttons[:5]:
                    self.safe_click(driver, button)
                    self.human_like_delay()
            
            return {"success": True, "engagement_type": engagement_type}
            
        except Exception as e:
            logger.error(f"❌ Reddit engagement failed: {e}")
            return {"success": False, "error": str(e)}
    
    def follow_users(self, driver, usernames: List[str], config: AutomationConfig) -> Dict:
        try:
            results = []
            
            for username in usernames:
                # Navigate to user profile
                driver.get(f"https://www.reddit.com/user/{username}/")
                self.human_like_delay()
                
                # Find follow button
                follow_button = self.wait_for_clickable(
                    driver, By.XPATH, "//button[contains(text(), 'Follow')]"
                )
                self.safe_click(driver, follow_button)
                
                results.append({"username": username, "followed": True})
                self.human_like_delay()
            
            return {"success": True, "followed_users": results}
            
        except Exception as e:
            logger.error(f"❌ Reddit follow failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_analytics(self, driver) -> Dict:
        try:
            # Navigate to user profile for analytics
            driver.get("https://www.reddit.com/user/me/")
            self.human_like_delay()
            
            analytics = {
                "karma": "N/A",
                "posts": "N/A",
                "comments": "N/A"
            }
            
            return {"success": True, "analytics": analytics}
            
        except Exception as e:
            logger.error(f"❌ Reddit analytics failed: {e}")
            return {"success": False, "error": str(e)}

class DiscordAutomation(BasePlatformAutomation):
    """Discord-specific automation."""
    
    def post_content(self, driver, content: PostContent, config: AutomationConfig) -> Dict:
        try:
            # Navigate to Discord
            driver.get("https://discord.com/channels/@me")
            self.human_like_delay()
            
            # Find message input
            message_input = self.wait_for_element(
                driver, By.XPATH, "//div[@role='textbox']"
            )
            
            # Type the message
            message_text = content.text
            
            if content.hashtags:
                message_text += "\n\n" + " ".join([f"#{tag}" for tag in content.hashtags])
            
            if content.mentions:
                message_text += "\n\n" + " ".join([f"@{mention}" for mention in content.mentions])
            
            # Type the message
            for char in message_text:
                message_input.send_keys(char)
                if config.safe_mode:
                    time.sleep(random.uniform(0.01, 0.05))
            
            self.human_like_delay()
            
            # Send message
            message_input.send_keys(Keys.RETURN)
            
            logger.info("✅ Discord message sent")
            return {"success": True, "platform": "discord"}
            
        except Exception as e:
            logger.error(f"❌ Discord message failed: {e}")
            return {"success": False, "error": str(e)}
    
    def engage_with_content(self, driver, engagement_type: str, config: AutomationConfig) -> Dict:
        try:
            # Navigate to Discord
            driver.get("https://discord.com/channels/@me")
            self.human_like_delay()
            
            if engagement_type == "react":
                # Find messages and add reactions
                messages = driver.find_elements(
                    By.XPATH, "//div[@class='message-2qnXI6']"
                )
                
                for message in messages[:3]:
                    # Hover over message to show reaction button
                    ActionChains(driver).move_to_element(message).perform()
                    self.human_like_delay()
                    
                    # Find and click reaction button
                    reaction_button = message.find_element(
                        By.XPATH, ".//button[@aria-label='Add Reaction']"
                    )
                    self.safe_click(driver, reaction_button)
                    self.human_like_delay()
            
            return {"success": True, "engagement_type": engagement_type}
            
        except Exception as e:
            logger.error(f"❌ Discord engagement failed: {e}")
            return {"success": False, "error": str(e)}
    
    def follow_users(self, driver, usernames: List[str], config: AutomationConfig) -> Dict:
        try:
            results = []
            
            for username in usernames:
                # Navigate to user profile
                driver.get(f"https://discord.com/users/{username}")
                self.human_like_delay()
                
                # Find add friend button
                add_friend_button = self.wait_for_clickable(
                    driver, By.XPATH, "//button[contains(text(), 'Add Friend')]"
                )
                self.safe_click(driver, add_friend_button)
                
                results.append({"username": username, "followed": True})
                self.human_like_delay()
            
            return {"success": True, "followed_users": results}
            
        except Exception as e:
            logger.error(f"❌ Discord follow failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_analytics(self, driver) -> Dict:
        try:
            # Discord doesn't have public analytics
            analytics = {
                "servers": "N/A",
                "friends": "N/A",
                "messages": "N/A"
            }
            
            return {"success": True, "analytics": analytics}
            
        except Exception as e:
            logger.error(f"❌ Discord analytics failed: {e}")
            return {"success": False, "error": str(e)}

class StocktwitsAutomation(BasePlatformAutomation):
    """Stocktwits-specific automation."""
    
    def post_content(self, driver, content: PostContent, config: AutomationConfig) -> Dict:
        try:
            # Navigate to Stocktwits
            driver.get("https://stocktwits.com/")
            self.human_like_delay()
            
            # Find the post creation area
            post_area = self.wait_for_element(
                driver, By.XPATH, "//textarea[@placeholder='What's happening?']"
            )
            
            # Compose the post
            post_text = content.text
            
            if content.hashtags:
                post_text += "\n\n" + " ".join([f"#{tag}" for tag in content.hashtags])
            
            if content.mentions:
                post_text += "\n\n" + " ".join([f"@{mention}" for mention in content.mentions])
            
            # Type the post
            for char in post_text:
                post_area.send_keys(char)
                if config.safe_mode:
                    time.sleep(random.uniform(0.01, 0.05))
            
            self.human_like_delay()
            
            # Click post button
            post_button = self.wait_for_clickable(
                driver, By.XPATH, "//button[contains(text(), 'Post')]"
            )
            self.safe_click(driver, post_button)
            
            logger.info("✅ Stocktwits post successful")
            return {"success": True, "platform": "stocktwits"}
            
        except Exception as e:
            logger.error(f"❌ Stocktwits post failed: {e}")
            return {"success": False, "error": str(e)}
    
    def engage_with_content(self, driver, engagement_type: str, config: AutomationConfig) -> Dict:
        try:
            # Navigate to Stocktwits
            driver.get("https://stocktwits.com/")
            self.human_like_delay()
            
            if engagement_type == "like":
                like_buttons = driver.find_elements(
                    By.XPATH, "//button[@aria-label='Like']"
                )
                for button in like_buttons[:5]:
                    self.safe_click(driver, button)
                    self.human_like_delay()
            
            return {"success": True, "engagement_type": engagement_type}
            
        except Exception as e:
            logger.error(f"❌ Stocktwits engagement failed: {e}")
            return {"success": False, "error": str(e)}
    
    def follow_users(self, driver, usernames: List[str], config: AutomationConfig) -> Dict:
        try:
            results = []
            
            for username in usernames:
                # Navigate to user profile
                driver.get(f"https://stocktwits.com/{username}")
                self.human_like_delay()
                
                # Find follow button
                follow_button = self.wait_for_clickable(
                    driver, By.XPATH, "//button[contains(text(), 'Follow')]"
                )
                self.safe_click(driver, follow_button)
                
                results.append({"username": username, "followed": True})
                self.human_like_delay()
            
            return {"success": True, "followed_users": results}
            
        except Exception as e:
            logger.error(f"❌ Stocktwits follow failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_analytics(self, driver) -> Dict:
        try:
            # Navigate to profile for analytics
            driver.get("https://stocktwits.com/settings/profile")
            self.human_like_delay()
            
            analytics = {
                "followers": "N/A",
                "following": "N/A",
                "posts": "N/A"
            }
            
            return {"success": True, "analytics": analytics}
            
        except Exception as e:
            logger.error(f"❌ Stocktwits analytics failed: {e}")
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Example usage
    automation = SocialMediaAutomation()
    
    # Create sample content
    content = PostContent(
        text="Excited to share our latest project! 🚀 #innovation #tech",
        content_type=ContentType.TEXT,
        hashtags=["innovation", "tech", "automation"],
        mentions=["team"]
    )
    
    # Post to all platforms
    results = automation.post_to_all_platforms(content)
    print(f"Posting results: {results}")
    
    # Get analytics for each platform
    for platform in PlatformType:
        analytics = automation.get_analytics(platform)
        print(f"{platform.value} analytics: {analytics}")
    
    automation.close_driver() 