#!/usr/bin/env python3
"""
Growth Engine Scheduler - Background job scheduler for automated growth tasks.
Handles leaderboards, collaboration suggestions, metrics logging, and content scheduling.
"""

import os
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import schedule
import time
from pathlib import Path
import threading

from growth_engine import GrowthEngine, CommunityType, BadgeType
from setup_logging import setup_logging

logger = setup_logging("growth_engine_scheduler", log_dir="./logs")

class GrowthEngineScheduler:
    """Background job scheduler for growth engine automation."""
    
    def __init__(self):
        self.growth_engine = GrowthEngine()
        self.running = False
        self.jobs = {}
        self.metrics_history = []
        
    async def start_scheduler(self):
        """Start the background job scheduler."""
        self.running = True
        logger.info("Starting Growth Engine Scheduler")
        
        # Schedule jobs
        await self._schedule_all_jobs()
        
        # Start the scheduler loop
        while self.running:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute
    
    async def stop_scheduler(self):
        """Stop the background job scheduler."""
        self.running = False
        logger.info("Stopping Growth Engine Scheduler")
    
    async def _schedule_all_jobs(self):
        """Schedule all background jobs."""
        # Weekly leaderboard update
        schedule.every().sunday.at("00:00").do(self._weekly_leaderboard_job)
        
        # Daily collaboration suggestions
        schedule.every().day.at("09:00").do(self._daily_collab_suggestions_job)
        
        # Hourly metrics logging
        schedule.every().hour.do(self._hourly_metrics_job)
        
        # Daily content scheduling
        schedule.every().day.at("08:00").do(self._daily_content_scheduling_job)
        
        # Weekly community engagement analysis
        schedule.every().saturday.at("14:00").do(self._weekly_community_analysis_job)
        
        # Daily badge awards
        schedule.every().day.at("18:00").do(self._daily_badge_awards_job)
        
        logger.info("Scheduled all background jobs")
    
    def _weekly_leaderboard_job(self):
        """Update weekly leaderboard and reset weekly engagement."""
        asyncio.create_task(self._async_weekly_leaderboard_job())
    
    async def _async_weekly_leaderboard_job(self):
        """Async version of weekly leaderboard job."""
        try:
            logger.info("Running weekly leaderboard update")
            
            # Update leaderboard
            leaderboard = await self.growth_engine.update_leaderboard()
            
            # Award weekly top performer badges
            if leaderboard:
                top_user_id = leaderboard[0]["user_id"]
                await self.growth_engine.award_badge(top_user_id, BadgeType.WEEKLY_TOP)
                logger.info(f"Awarded weekly top badge to user {top_user_id}")
            
            # Reset weekly engagement for all users
            for user in self.growth_engine.users.values():
                user.weekly_engagement = 0
            
            # Save leaderboard data
            leaderboard_data = {
                "timestamp": datetime.now().isoformat(),
                "leaderboard": leaderboard,
                "type": "weekly"
            }
            
            self._save_metrics("leaderboard", leaderboard_data)
            logger.info("Weekly leaderboard update completed")
            
        except Exception as e:
            logger.error(f"Error in weekly leaderboard job: {e}")
    
    def _daily_collab_suggestions_job(self):
        """Generate daily collaboration suggestions."""
        asyncio.create_task(self._async_daily_collab_suggestions_job())
    
    async def _async_daily_collab_suggestions_job(self):
        """Async version of daily collaboration suggestions job."""
        try:
            logger.info("Generating daily collaboration suggestions")
            
            suggestions = await self.growth_engine._generate_collab_suggestions()
            
            # Filter and rank suggestions
            ranked_suggestions = []
            for suggestion in suggestions:
                score = suggestion["score"]
                if score >= 2:  # Minimum similarity threshold
                    ranked_suggestions.append(suggestion)
            
            # Sort by score
            ranked_suggestions.sort(key=lambda x: x["score"], reverse=True)
            
            # Save suggestions
            suggestions_data = {
                "timestamp": datetime.now().isoformat(),
                "suggestions": ranked_suggestions[:10],  # Top 10
                "total_generated": len(suggestions)
            }
            
            self._save_metrics("collab_suggestions", suggestions_data)
            logger.info(f"Generated {len(ranked_suggestions)} collaboration suggestions")
            
        except Exception as e:
            logger.error(f"Error in daily collaboration suggestions job: {e}")
    
    def _hourly_metrics_job(self):
        """Log hourly engagement metrics."""
        asyncio.create_task(self._async_hourly_metrics_job())
    
    async def _async_hourly_metrics_job(self):
        """Async version of hourly metrics job."""
        try:
            logger.info("Logging hourly engagement metrics")
            
            metrics = await self.growth_engine._log_engagement_metrics()
            
            # Add to history
            self.metrics_history.append(metrics)
            
            # Keep only last 24 hours of data
            if len(self.metrics_history) > 24:
                self.metrics_history = self.metrics_history[-24:]
            
            logger.info("Hourly metrics logged successfully")
            
        except Exception as e:
            logger.error(f"Error in hourly metrics job: {e}")
    
    def _daily_content_scheduling_job(self):
        """Schedule daily content creation and posting."""
        asyncio.create_task(self._async_daily_content_scheduling_job())
    
    async def _async_daily_content_scheduling_job(self):
        """Async version of daily content scheduling job."""
        try:
            logger.info("Scheduling daily content creation")
            
            # Get popular templates
            popular_templates = sorted(
                self.growth_engine.templates.values(),
                key=lambda t: t.usage_count,
                reverse=True
            )[:5]
            
            # Generate content for each template
            scheduled_content = []
            for template in popular_templates:
                content = await self.growth_engine.generate_content_with_template(
                    template.id,
                    {
                        "scheduled_time": datetime.now() + timedelta(hours=2),
                        "platforms": ["instagram", "twitter", "linkedin"],
                        "auto_schedule": True
                    }
                )
                
                if content:
                    scheduled_content.append(content)
            
            # Save scheduled content
            content_data = {
                "timestamp": datetime.now().isoformat(),
                "scheduled_content": scheduled_content,
                "templates_used": [t.name for t in popular_templates]
            }
            
            self._save_metrics("content_scheduling", content_data)
            logger.info(f"Scheduled {len(scheduled_content)} content pieces")
            
        except Exception as e:
            logger.error(f"Error in daily content scheduling job: {e}")
    
    def _weekly_community_analysis_job(self):
        """Analyze weekly community engagement and growth."""
        asyncio.create_task(self._async_weekly_community_analysis_job())
    
    async def _async_weekly_community_analysis_job(self):
        """Async version of weekly community analysis job."""
        try:
            logger.info("Running weekly community analysis")
            
            community_analysis = []
            
            for community in self.growth_engine.communities.values():
                # Calculate engagement metrics
                total_members = len(community.members)
                active_members = sum(
                    1 for user_id in community.members
                    if user_id in self.growth_engine.users and 
                    self.growth_engine.users[user_id].weekly_engagement > 0
                )
                
                engagement_rate = active_members / max(total_members, 1)
                
                analysis = {
                    "community_id": community.id,
                    "community_name": community.name,
                    "total_members": total_members,
                    "active_members": active_members,
                    "engagement_rate": engagement_rate,
                    "growth_score": total_members * engagement_rate
                }
                
                community_analysis.append(analysis)
            
            # Sort by growth score
            community_analysis.sort(key=lambda x: x["growth_score"], reverse=True)
            
            # Save analysis
            analysis_data = {
                "timestamp": datetime.now().isoformat(),
                "community_analysis": community_analysis,
                "top_growing_community": community_analysis[0] if community_analysis else None
            }
            
            self._save_metrics("community_analysis", analysis_data)
            logger.info("Weekly community analysis completed")
            
        except Exception as e:
            logger.error(f"Error in weekly community analysis job: {e}")
    
    def _daily_badge_awards_job(self):
        """Award daily badges based on user activity."""
        asyncio.create_task(self._async_daily_badge_awards_job())
    
    async def _async_daily_badge_awards_job(self):
        """Async version of daily badge awards job."""
        try:
            logger.info("Processing daily badge awards")
            
            awards_given = []
            
            for user in self.growth_engine.users.values():
                # Check for first comment badge
                if (user.weekly_engagement > 0 and 
                    BadgeType.FIRST_COMMENT not in user.badges):
                    await self.growth_engine.award_badge(user.user_id, BadgeType.FIRST_COMMENT)
                    awards_given.append({
                        "user_id": user.user_id,
                        "badge": BadgeType.FIRST_COMMENT.value,
                        "reason": "First engagement of the week"
                    })
                
                # Check for content creator badge
                if (user.total_posts >= 5 and 
                    BadgeType.CONTENT_CREATOR not in user.badges):
                    await self.growth_engine.award_badge(user.user_id, BadgeType.CONTENT_CREATOR)
                    awards_given.append({
                        "user_id": user.user_id,
                        "badge": BadgeType.CONTENT_CREATOR.value,
                        "reason": "Created 5+ content pieces"
                    })
                
                # Check for collaboration master badge
                if (user.collaboration_count >= 3 and 
                    BadgeType.COLLAB_MASTER not in user.badges):
                    await self.growth_engine.award_badge(user.user_id, BadgeType.COLLAB_MASTER)
                    awards_given.append({
                        "user_id": user.user_id,
                        "badge": BadgeType.COLLAB_MASTER.value,
                        "reason": "Completed 3+ collaborations"
                    })
            
            # Save badge awards
            awards_data = {
                "timestamp": datetime.now().isoformat(),
                "awards_given": awards_given,
                "total_awards": len(awards_given)
            }
            
            self._save_metrics("badge_awards", awards_data)
            logger.info(f"Awarded {len(awards_given)} badges")
            
        except Exception as e:
            logger.error(f"Error in daily badge awards job: {e}")
    
    def _save_metrics(self, metric_type: str, data: Dict[str, Any]):
        """Save metrics to file."""
        metrics_dir = Path("./data/metrics")
        metrics_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{metric_type}_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = metrics_dir / filename
        
        # Load existing data or create new
        if filepath.exists():
            with open(filepath, "r") as f:
                existing_data = json.load(f)
        else:
            existing_data = []
        
        # Add new data
        existing_data.append(data)
        
        # Save back to file
        with open(filepath, "w") as f:
            json.dump(existing_data, f, indent=2)
    
    async def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status."""
        return {
            "running": self.running,
            "next_jobs": [
                {
                    "job": str(job),
                    "next_run": job.next_run.isoformat() if job.next_run else None
                }
                for job in schedule.jobs
            ],
            "metrics_history_count": len(self.metrics_history),
            "total_users": len(self.growth_engine.users),
            "total_communities": len(self.growth_engine.communities)
        }
    
    async def run_manual_job(self, job_type: str) -> Dict[str, Any]:
        """Manually run a specific job type."""
        try:
            if job_type == "leaderboard":
                await self._async_weekly_leaderboard_job()
                return {"status": "success", "job": "leaderboard"}
            
            elif job_type == "collab_suggestions":
                await self._async_daily_collab_suggestions_job()
                return {"status": "success", "job": "collab_suggestions"}
            
            elif job_type == "metrics":
                await self._async_hourly_metrics_job()
                return {"status": "success", "job": "metrics"}
            
            elif job_type == "content_scheduling":
                await self._async_daily_content_scheduling_job()
                return {"status": "success", "job": "content_scheduling"}
            
            elif job_type == "community_analysis":
                await self._async_weekly_community_analysis_job()
                return {"status": "success", "job": "community_analysis"}
            
            elif job_type == "badge_awards":
                await self._async_daily_badge_awards_job()
                return {"status": "success", "job": "badge_awards"}
            
            else:
                return {"status": "error", "message": f"Unknown job type: {job_type}"}
                
        except Exception as e:
            logger.error(f"Error running manual job {job_type}: {e}")
            return {"status": "error", "message": str(e)}

# Example usage
async def test_scheduler():
    """Test the scheduler functionality."""
    scheduler = GrowthEngineScheduler()
    
    # Create some test data
    user1 = await scheduler.growth_engine.create_user_profile("user1", "alice_social")
    user2 = await scheduler.growth_engine.create_user_profile("user2", "bob_creator")
    
    # Add some engagement
    user1.weekly_engagement = 10
    user2.weekly_engagement = 15
    
    # Run a manual job
    result = await scheduler.run_manual_job("leaderboard")
    print(f"Manual job result: {result}")
    
    # Get scheduler status
    status = await scheduler.get_scheduler_status()
    print(f"Scheduler status: {status}")

if __name__ == "__main__":
    asyncio.run(test_scheduler()) 