#!/usr/bin/env python3
"""
Social Media CLI
================

Command-line interface for the Unified Social Media Manager.
Provides easy access to all automation features for all platforms.

Usage:
    python social_cli.py [command] [options]

Commands:
    post          - Post content to platforms
    campaign      - Manage content campaigns
    engage        - Engage with content
    follow        - Follow users
    analytics     - Get analytics
    templates     - Manage content templates
    status        - Check platform status
    auto          - Run automated tasks
"""

import argparse
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

from unified_social_manager import UnifiedSocialManager
from social_media_automation import PlatformType
from content_manager import ContentCategory

def parse_platforms(platform_string: str) -> List[PlatformType]:
    """Parse platform string into PlatformType list."""
    platform_map = {
        "linkedin": PlatformType.LINKEDIN,
        "twitter": PlatformType.TWITTER,
        "facebook": PlatformType.FACEBOOK,
        "instagram": PlatformType.INSTAGRAM,
        "reddit": PlatformType.REDDIT,
        "discord": PlatformType.DISCORD,
        "stocktwits": PlatformType.STOCKTWITS,
        "all": list(PlatformType)
    }
    
    platforms = []
    for platform in platform_string.split(","):
        platform = platform.strip().lower()
        if platform == "all":
            platforms.extend(platform_map["all"])
        elif platform in platform_map:
            platforms.append(platform_map[platform])
        else:
            print(f"❌ Unknown platform: {platform}")
            sys.exit(1)
    
    return platforms

def print_json(data: Dict[str, Any]):
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2, default=str))

def post_command(args):
    """Handle post command."""
    manager = UnifiedSocialManager()
    
    try:
        # Initialize platforms
        if not manager.initialize_all_platforms():
            print("❌ Failed to initialize platforms")
            return
        
        # Parse platforms
        platforms = parse_platforms(args.platforms)
        
        # Parse hashtags and mentions
        hashtags = args.hashtags.split(",") if args.hashtags else []
        mentions = args.mentions.split(",") if args.mentions else []
        
        # Remove empty strings
        hashtags = [tag.strip() for tag in hashtags if tag.strip()]
        mentions = [mention.strip() for mention in mentions if mention.strip()]
        
        if args.all_platforms:
            result = manager.post_to_all_platforms(
                text=args.text,
                hashtags=hashtags,
                mentions=mentions
            )
        else:
            result = manager.post_to_specific_platforms(
                text=args.text,
                platforms=platforms,
                hashtags=hashtags,
                mentions=mentions
            )
        
        print("✅ Post completed!")
        print_json(result)
        
    except Exception as e:
        print(f"❌ Error posting: {e}")
    finally:
        manager.cleanup()

def campaign_command(args):
    """Handle campaign command."""
    manager = UnifiedSocialManager()
    
    try:
        if args.action == "create":
            # Parse platforms
            platforms = parse_platforms(args.platforms)
            
            # Parse posts from file or use provided text
            posts = []
            if args.posts_file:
                with open(args.posts_file, 'r') as f:
                    posts = [line.strip() for line in f if line.strip()]
            elif args.posts:
                posts = args.posts.split("|")
            
            # Calculate dates
            start_date = datetime.now()
            end_date = start_date + timedelta(days=args.duration)
            
            result = manager.create_and_schedule_campaign(
                name=args.name,
                description=args.description,
                start_date=start_date,
                end_date=end_date,
                platforms=platforms,
                posts=posts
            )
            
            print("✅ Campaign created!")
            print_json(result)
            
        elif args.action == "list":
            campaigns = manager.content_manager.campaigns
            if campaigns:
                print("📋 Active Campaigns:")
                for name, campaign in campaigns.items():
                    print(f"  - {name}: {campaign.description}")
                    print(f"    Posts: {len(campaign.posts)}")
                    print(f"    Platforms: {[p.value for p in campaign.platforms]}")
                    print(f"    Status: {campaign.status.value}")
                    print()
            else:
                print("📋 No active campaigns found.")
                
        elif args.action == "export":
            result = manager.export_campaign(args.name, args.format)
            if result["success"]:
                print(f"✅ Campaign exported: {args.name}")
                print_json(result)
            else:
                print(f"❌ Error exporting campaign: {result['error']}")
                
    except Exception as e:
        print(f"❌ Error with campaign: {e}")
    finally:
        manager.cleanup()

def engage_command(args):
    """Handle engage command."""
    manager = UnifiedSocialManager()
    
    try:
        # Initialize platforms
        if not manager.initialize_all_platforms():
            print("❌ Failed to initialize platforms")
            return
        
        # Parse platforms
        platforms = parse_platforms(args.platforms)
        
        # Parse engagement types
        engagement_types = args.types.split(",") if args.types else ["like"]
        
        result = manager.engage_with_content(platforms, engagement_types)
        
        print("✅ Engagement completed!")
        print_json(result)
        
    except Exception as e:
        print(f"❌ Error engaging: {e}")
    finally:
        manager.cleanup()

def follow_command(args):
    """Handle follow command."""
    manager = UnifiedSocialManager()
    
    try:
        # Initialize platforms
        if not manager.initialize_all_platforms():
            print("❌ Failed to initialize platforms")
            return
        
        # Parse platforms
        platforms = parse_platforms(args.platforms)
        
        # Parse usernames
        usernames = args.usernames.split(",")
        usernames = [username.strip() for username in usernames if username.strip()]
        
        result = manager.follow_users(usernames, platforms)
        
        print("✅ Follow operation completed!")
        print_json(result)
        
    except Exception as e:
        print(f"❌ Error following users: {e}")
    finally:
        manager.cleanup()

def analytics_command(args):
    """Handle analytics command."""
    manager = UnifiedSocialManager()
    
    try:
        if args.type == "platforms":
            result = manager.get_analytics_for_all_platforms()
        elif args.type == "content":
            result = manager.get_content_analytics()
        elif args.type == "performance":
            result = manager.get_performance_summary()
        else:
            print(f"❌ Unknown analytics type: {args.type}")
            return
        
        print(f"📊 {args.type.title()} Analytics:")
        print_json(result)
        
    except Exception as e:
        print(f"❌ Error getting analytics: {e}")
    finally:
        manager.cleanup()

def templates_command(args):
    """Handle templates command."""
    manager = UnifiedSocialManager()
    
    try:
        if args.action == "create":
            # Parse platforms
            platforms = parse_platforms(args.platforms)
            
            # Parse category
            category_map = {
                "promotional": ContentCategory.PROMOTIONAL,
                "educational": ContentCategory.EDUCATIONAL,
                "entertainment": ContentCategory.ENTERTAINMENT,
                "news": ContentCategory.NEWS,
                "personal": ContentCategory.PERSONAL,
                "interactive": ContentCategory.INTERACTIVE
            }
            
            category = category_map.get(args.category.lower())
            if not category:
                print(f"❌ Unknown category: {args.category}")
                return
            
            # Parse hashtags and mentions
            hashtags = args.hashtags.split(",") if args.hashtags else []
            mentions = args.mentions.split(",") if args.mentions else []
            
            hashtags = [tag.strip() for tag in hashtags if tag.strip()]
            mentions = [mention.strip() for mention in mentions if mention.strip()]
            
            result = manager.create_content_template(
                name=args.name,
                category=category,
                base_text=args.text,
                hashtags=hashtags,
                platforms=platforms,
                mentions=mentions
            )
            
            print("✅ Template created!")
            print_json(result)
            
        elif args.action == "list":
            templates = manager.content_manager.templates
            if templates:
                print("📋 Available Templates:")
                for name, template in templates.items():
                    print(f"  - {name}: {template.category.value}")
                    print(f"    Platforms: {[p.value for p in template.platforms]}")
                    print(f"    Hashtags: {template.hashtags}")
                    print()
            else:
                print("📋 No templates found.")
                
        elif args.action == "generate":
            variables = {}
            if args.variables:
                for var in args.variables.split(","):
                    if "=" in var:
                        key, value = var.split("=", 1)
                        variables[key.strip()] = value.strip()
            
            result = manager.generate_content_from_template(args.name, variables)
            
            if result["success"]:
                print("✅ Content generated!")
                print_json(result)
            else:
                print(f"❌ Error generating content: {result['error']}")
                
    except Exception as e:
        print(f"❌ Error with templates: {e}")
    finally:
        manager.cleanup()

def status_command(args):
    """Handle status command."""
    manager = UnifiedSocialManager()
    
    try:
        # Initialize platforms
        if not manager.initialize_all_platforms():
            print("❌ Failed to initialize platforms")
            return
        
        status = manager.get_platform_status()
        
        print("📊 Platform Status:")
        for platform, info in status.items():
            status_icon = "✅" if info["connected"] else "❌"
            last_check = info["last_check"].strftime("%Y-%m-%d %H:%M:%S") if info["last_check"] else "Never"
            print(f"  {status_icon} {platform.value}: {last_check}")
        
    except Exception as e:
        print(f"❌ Error getting status: {e}")
    finally:
        manager.cleanup()

def auto_command(args):
    """Handle auto command."""
    manager = UnifiedSocialManager()
    
    try:
        # Initialize platforms
        if not manager.initialize_all_platforms():
            print("❌ Failed to initialize platforms")
            return
        
        if args.task == "engagement":
            result = manager.run_automated_engagement(args.duration)
            print("✅ Automated engagement completed!")
            print_json(result)
            
        elif args.task == "recurring":
            # Parse platforms
            platforms = parse_platforms(args.platforms)
            
            result = manager.schedule_recurring_posts(
                text=args.text,
                platforms=platforms,
                interval_hours=args.interval,
                duration_days=args.days
            )
            
            print("✅ Recurring posts scheduled!")
            print_json(result)
            
    except Exception as e:
        print(f"❌ Error with automated task: {e}")
    finally:
        manager.cleanup()

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Social Media CLI - Manage all your social media platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Post command
    post_parser = subparsers.add_parser("post", help="Post content to platforms")
    post_parser.add_argument("text", help="Text content to post")
    post_parser.add_argument("--platforms", default="all", help="Comma-separated list of platforms")
    post_parser.add_argument("--hashtags", help="Comma-separated list of hashtags")
    post_parser.add_argument("--mentions", help="Comma-separated list of mentions")
    post_parser.add_argument("--all-platforms", action="store_true", help="Post to all platforms")
    
    # Campaign command
    campaign_parser = subparsers.add_parser("campaign", help="Manage content campaigns")
    campaign_parser.add_argument("action", choices=["create", "list", "export"], help="Campaign action")
    campaign_parser.add_argument("--name", help="Campaign name")
    campaign_parser.add_argument("--description", help="Campaign description")
    campaign_parser.add_argument("--platforms", default="all", help="Comma-separated list of platforms")
    campaign_parser.add_argument("--posts", help="Pipe-separated list of posts")
    campaign_parser.add_argument("--posts-file", help="File containing posts (one per line)")
    campaign_parser.add_argument("--duration", type=int, default=7, help="Campaign duration in days")
    campaign_parser.add_argument("--format", default="json", help="Export format")
    
    # Engage command
    engage_parser = subparsers.add_parser("engage", help="Engage with content")
    engage_parser.add_argument("--platforms", default="all", help="Comma-separated list of platforms")
    engage_parser.add_argument("--types", default="like", help="Comma-separated list of engagement types")
    
    # Follow command
    follow_parser = subparsers.add_parser("follow", help="Follow users")
    follow_parser.add_argument("usernames", help="Comma-separated list of usernames")
    follow_parser.add_argument("--platforms", default="all", help="Comma-separated list of platforms")
    
    # Analytics command
    analytics_parser = subparsers.add_parser("analytics", help="Get analytics")
    analytics_parser.add_argument("type", choices=["platforms", "content", "performance"], help="Analytics type")
    
    # Templates command
    templates_parser = subparsers.add_parser("templates", help="Manage content templates")
    templates_parser.add_argument("action", choices=["create", "list", "generate"], help="Template action")
    templates_parser.add_argument("--name", help="Template name")
    templates_parser.add_argument("--category", help="Content category")
    templates_parser.add_argument("--text", help="Template base text")
    templates_parser.add_argument("--platforms", default="all", help="Comma-separated list of platforms")
    templates_parser.add_argument("--hashtags", help="Comma-separated list of hashtags")
    templates_parser.add_argument("--mentions", help="Comma-separated list of mentions")
    templates_parser.add_argument("--variables", help="Comma-separated list of variables (key=value)")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check platform status")
    
    # Auto command
    auto_parser = subparsers.add_parser("auto", help="Run automated tasks")
    auto_parser.add_argument("task", choices=["engagement", "recurring"], help="Automated task")
    auto_parser.add_argument("--duration", type=int, default=30, help="Duration in minutes")
    auto_parser.add_argument("--text", help="Text for recurring posts")
    auto_parser.add_argument("--platforms", default="all", help="Comma-separated list of platforms")
    auto_parser.add_argument("--interval", type=int, default=24, help="Interval in hours")
    auto_parser.add_argument("--days", type=int, default=7, help="Duration in days")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Route to appropriate command handler
    command_handlers = {
        "post": post_command,
        "campaign": campaign_command,
        "engage": engage_command,
        "follow": follow_command,
        "analytics": analytics_command,
        "templates": templates_command,
        "status": status_command,
        "auto": auto_command
    }
    
    handler = command_handlers.get(args.command)
    if handler:
        handler(args)
    else:
        print(f"❌ Unknown command: {args.command}")
        parser.print_help()

if __name__ == "__main__":
    main() 