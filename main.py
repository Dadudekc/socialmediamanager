#!/usr/bin/env python3
"""
Ultimate Follow Builder - Integrated System
The most comprehensive social media growth automation system.
Combines follow automation, engagement automation, AI content generation, and web dashboard.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from ultimate_follow_builder import UltimateFollowBuilder, BuilderConfig, BuilderMode
from ai_content_generator import AIContentGenerator, ContentRequest, ContentType, ToneType
from web_dashboard import DASHBOARD_HTML, ConnectionManager

app = FastAPI(title="Ultimate Follow Builder - Integrated System", version="2.0.0")

# Global systems
ai_generator = AIContentGenerator()
manager = ConnectionManager()

# Global state
system_state = {
    "active_campaigns": [],
    "total_follows": 0,
    "total_engagements": 0,
    "total_followers_gained": 0,
    "total_content_generated": 0,
    "account_health": {},
    "recent_activities": [],
    "growth_metrics": {},
    "roi_data": {},
    "ai_analytics": {}
}

class IntegratedUltimateFollowBuilder:
    """Integrated Ultimate Follow Builder with all systems."""
    
    def __init__(self):
        self.builder = None
        self.ai_generator = ai_generator
        self.active_campaigns = []
        self.generated_content = []
    
    async def start_campaign(self, niche: str, platform: str, mode: str, 
                           follow_limit: int, target_audience: Dict[str, Any]) -> Dict[str, Any]:
        """Start a comprehensive campaign with all systems."""
        
        # Create builder configuration
        config = BuilderConfig(
            mode=BuilderMode(mode),
            platforms=[platform],
            daily_follow_limit=follow_limit,
            daily_unfollow_limit=int(follow_limit * 0.8),
            daily_engagement_limit=follow_limit * 2,
            engagement_window_days=3,
            safety_settings={},
            ai_features_enabled=True,
            analytics_enabled=True
        )
        
        # Initialize builder
        self.builder = UltimateFollowBuilder(config)
        
        # Run the Ultimate Follow Builder
        result = await self.builder.run_ultimate_builder(niche, target_audience)
        
        # Generate AI content for the campaign
        content_result = await self._generate_campaign_content(niche, platform, target_audience)
        
        # Combine results
        integrated_result = {
            "campaign_id": result.get("strategy_id", f"campaign-{int(time.time())}"),
            "niche": niche,
            "platform": platform,
            "mode": mode,
            "follow_results": result.get("execution_results", {}),
            "content_results": content_result,
            "integrated_metrics": self._calculate_integrated_metrics(result, content_result),
            "timestamp": datetime.now().isoformat()
        }
        
        # Update global state
        self._update_system_state(integrated_result)
        
        return integrated_result
    
    async def _generate_campaign_content(self, niche: str, platform: str, 
                                       target_audience: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI content for the campaign."""
        
        # Create content requests for different tones
        content_requests = [
            ContentRequest(
                niche=niche,
                content_type=ContentType.CAPTION,
                tone=ToneType.MOTIVATIONAL,
                platform=platform,
                target_audience=target_audience,
                keywords=[niche, "growth", "success"]
            ),
            ContentRequest(
                niche=niche,
                content_type=ContentType.CAPTION,
                tone=ToneType.EDUCATIONAL,
                platform=platform,
                target_audience=target_audience,
                keywords=[niche, "tips", "advice"]
            ),
            ContentRequest(
                niche=niche,
                content_type=ContentType.CAPTION,
                tone=ToneType.INSPIRATIONAL,
                platform=platform,
                target_audience=target_audience,
                keywords=[niche, "inspiration", "motivation"]
            )
        ]
        
        # Generate content
        generated_content = await self.ai_generator.generate_batch_content(content_requests)
        
        # Get content analytics
        content_analytics = await self.ai_generator.get_content_analytics(generated_content)
        
        # Store generated content
        self.generated_content.extend(generated_content)
        
        return {
            "total_content": len(generated_content),
            "content_list": [
                {
                    "id": content.id,
                    "content": content.content,
                    "hashtags": content.hashtags,
                    "engagement_score": content.engagement_score,
                    "viral_potential": content.viral_potential
                }
                for content in generated_content
            ],
            "analytics": content_analytics
        }
    
    def _calculate_integrated_metrics(self, follow_result: Dict, content_result: Dict) -> Dict[str, Any]:
        """Calculate integrated metrics combining follow and content results."""
        
        follow_metrics = follow_result.get("execution_results", {}).get("growth_metrics", {})
        content_analytics = content_result.get("analytics", {})
        
        total_follows = follow_metrics.get("total_follows", 0)
        total_engagements = follow_metrics.get("total_engagements", 0)
        estimated_followers_gained = follow_metrics.get("estimated_followers_gained", 0)
        
        avg_content_engagement = content_analytics.get("average_engagement", 0)
        avg_viral_potential = content_analytics.get("average_viral_potential", 0)
        
        # Calculate integrated engagement rate
        integrated_engagement_rate = (avg_content_engagement + (total_engagements / max(total_follows, 1))) / 2
        
        # Calculate viral growth potential
        viral_growth_potential = estimated_followers_gained * avg_viral_potential
        
        # Calculate ROI
        estimated_value_per_follower = 2.0
        total_roi = estimated_followers_gained * estimated_value_per_follower
        
        return {
            "total_follows": total_follows,
            "total_engagements": total_engagements,
            "estimated_followers_gained": estimated_followers_gained,
            "integrated_engagement_rate": integrated_engagement_rate,
            "viral_growth_potential": viral_growth_potential,
            "content_engagement_score": avg_content_engagement,
            "content_viral_potential": avg_viral_potential,
            "estimated_roi": total_roi,
            "campaign_efficiency": (integrated_engagement_rate + avg_viral_potential) / 2
        }
    
    def _update_system_state(self, result: Dict[str, Any]):
        """Update the global system state."""
        integrated_metrics = result.get("integrated_metrics", {})
        
        system_state["total_follows"] += integrated_metrics.get("total_follows", 0)
        system_state["total_engagements"] += integrated_metrics.get("total_engagements", 0)
        system_state["total_followers_gained"] += integrated_metrics.get("estimated_followers_gained", 0)
        system_state["total_content_generated"] += result.get("content_results", {}).get("total_content", 0)
        
        # Update ROI
        system_state["roi_data"]["estimated_roi"] = system_state["total_followers_gained"] * 2.0
        
        # Update account health
        if "follow_results" in result and "account_health" in result["follow_results"]:
            system_state["account_health"] = result["follow_results"]["account_health"]
        
        # Add recent activity
        activity = f"Campaign completed: {result.get('campaign_id', 'Unknown')} - {result.get('niche', 'Unknown')} on {result.get('platform', 'Unknown')}"
        system_state["recent_activities"].insert(0, activity)
        if len(system_state["recent_activities"]) > 10:
            system_state["recent_activities"] = system_state["recent_activities"][:10]
        
        # Update AI analytics
        content_analytics = result.get("content_results", {}).get("analytics", {})
        system_state["ai_analytics"] = content_analytics

# Global integrated builder
integrated_builder = IntegratedUltimateFollowBuilder()

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the integrated dashboard."""
    return DASHBOARD_HTML

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        # Send initial data
        await websocket.send_text(json.dumps(system_state))
        
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "start_campaign":
                await handle_start_campaign(message, websocket)
            elif message.get("action") == "stop_campaign":
                await handle_stop_campaign(websocket)
            elif message.get("action") == "refresh_data":
                await handle_refresh_data(websocket)
            elif message.get("action") == "generate_content":
                await handle_generate_content(message, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def handle_start_campaign(data: Dict, websocket: WebSocket):
    """Handle integrated campaign start request."""
    try:
        niche = data.get("niche", "fitness")
        platform = data.get("platform", "instagram")
        mode = data.get("mode", "moderate")
        follow_limit = data.get("follow_limit", 50)
        
        target_audience = {
            "min_followers": 2000,
            "max_followers": 50000,
            "min_engagement_rate": 0.02,
            "interests": [niche],
            "locations": ["United States", "Canada"]
        }
        
        # Start integrated campaign
        result = await integrated_builder.start_campaign(
            niche=niche,
            platform=platform,
            mode=mode,
            follow_limit=follow_limit,
            target_audience=target_audience
        )
        
        # Send updated data to client
        await websocket.send_text(json.dumps(system_state))
        
        # Send detailed result
        await websocket.send_text(json.dumps({
            "type": "campaign_result",
            "data": result
        }))
        
    except Exception as e:
        await websocket.send_text(json.dumps({"error": str(e)}))

async def handle_stop_campaign(websocket: WebSocket):
    """Handle campaign stop request."""
    system_state["active_campaigns"] = []
    await websocket.send_text(json.dumps({"message": "Campaigns stopped"}))

async def handle_refresh_data(websocket: WebSocket):
    """Handle data refresh request."""
    await websocket.send_text(json.dumps(system_state))

async def handle_generate_content(data: Dict, websocket: WebSocket):
    """Handle content generation request."""
    try:
        niche = data.get("niche", "fitness")
        platform = data.get("platform", "instagram")
        tone = data.get("tone", "motivational")
        
        request = ContentRequest(
            niche=niche,
            content_type=ContentType.CAPTION,
            tone=ToneType(tone),
            platform=platform,
            target_audience={},
            keywords=[niche]
        )
        
        content = await ai_generator.generate_content(request)
        
        await websocket.send_text(json.dumps({
            "type": "content_generated",
            "data": {
                "id": content.id,
                "content": content.content,
                "hashtags": content.hashtags,
                "engagement_score": content.engagement_score,
                "viral_potential": content.viral_potential
            }
        }))
        
    except Exception as e:
        await websocket.send_text(json.dumps({"error": str(e)}))

@app.get("/api/stats")
async def get_stats():
    """Get current system statistics."""
    return system_state

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/content")
async def get_generated_content():
    """Get all generated content."""
    return {
        "total_content": len(integrated_builder.generated_content),
        "content_list": [
            {
                "id": content.id,
                "content": content.content,
                "hashtags": content.hashtags,
                "engagement_score": content.engagement_score,
                "viral_potential": content.viral_potential,
                "niche": content.niche,
                "platform": content.platform
            }
            for content in integrated_builder.generated_content
        ]
    }

async def test_integrated_system():
    """Test the integrated Ultimate Follow Builder system."""
    print("🚀 ULTIMATE FOLLOW BUILDER - INTEGRATED SYSTEM TEST")
    print("=" * 60)
    
    # Test integrated campaign
    target_audience = {
        "min_followers": 2000,
        "max_followers": 50000,
        "min_engagement_rate": 0.02,
        "interests": ["fitness", "health"],
        "locations": ["United States", "Canada"]
    }
    
    try:
        result = await integrated_builder.start_campaign(
            niche="fitness",
            platform="instagram",
            mode="moderate",
            follow_limit=30,
            target_audience=target_audience
        )
        
        print(f"✅ Campaign ID: {result['campaign_id']}")
        print(f"📈 Integrated Metrics:")
        metrics = result['integrated_metrics']
        print(f"   - Total Follows: {metrics.get('total_follows', 0)}")
        print(f"   - Total Engagements: {metrics.get('total_engagements', 0)}")
        print(f"   - Followers Gained: {metrics.get('estimated_followers_gained', 0)}")
        print(f"   - Integrated Engagement Rate: {metrics.get('integrated_engagement_rate', 0):.2%}")
        print(f"   - Viral Growth Potential: {metrics.get('viral_growth_potential', 0):.2f}")
        print(f"   - Estimated ROI: ${metrics.get('estimated_roi', 0):.2f}")
        print(f"   - Campaign Efficiency: {metrics.get('campaign_efficiency', 0):.2%}")
        
        print(f"\n🤖 AI Content Generated:")
        content_results = result['content_results']
        print(f"   - Total Content: {content_results.get('total_content', 0)}")
        
        content_list = content_results.get('content_list', [])
        for i, content in enumerate(content_list[:3], 1):
            print(f"   {i}. {content['content'][:50]}...")
            print(f"      Engagement: {content['engagement_score']:.2f}, Viral: {content['viral_potential']:.2f}")
        
        print(f"\n📊 System State:")
        print(f"   - Total Follows: {system_state['total_follows']}")
        print(f"   - Total Engagements: {system_state['total_engagements']}")
        print(f"   - Total Followers Gained: {system_state['total_followers_gained']}")
        print(f"   - Total Content Generated: {system_state['total_content_generated']}")
        print(f"   - Estimated ROI: ${system_state['roi_data'].get('estimated_roi', 0):.2f}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Starting Ultimate Follow Builder - Integrated System...")
    print("📊 Dashboard available at: http://localhost:8004")
    print("🌐 WebSocket endpoint: ws://localhost:8004/ws")
    print("🤖 AI Content Generator: Active")
    print("📈 Growth Automation: Active")
    print("🛡️ Safety Features: Active")
    
    # Run test
    asyncio.run(test_integrated_system())
    
    # Start web server
    uvicorn.run(app, host="0.0.0.0", port=8004) 