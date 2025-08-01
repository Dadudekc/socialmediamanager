#!/usr/bin/env python3
"""
Growth Engine API - FastAPI web interface for the growth engine.
Provides REST API endpoints for all growth engine functionality.
"""

import os
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from growth_engine import GrowthEngine, CommunityType, BadgeType
from setup_logging import setup_logging

logger = setup_logging("growth_engine_api", log_dir="./logs")

# Pydantic models for API requests/responses
class CommunityCreateRequest(BaseModel):
    name: str
    type: str  # niche_finder, problem_solver, collaboration, engagement
    description: str
    templates: Optional[List[Dict]] = []

class UserCreateRequest(BaseModel):
    user_id: str
    username: str

class CollaborationCreateRequest(BaseModel):
    user1_id: str
    user2_id: str
    platform: str
    content_type: str

class ContentTemplateRequest(BaseModel):
    name: str
    content_type: str
    template_data: Dict[str, Any]

class ContentGenerateRequest(BaseModel):
    template_id: str
    custom_data: Optional[Dict[str, Any]] = {}

class BadgeAwardRequest(BaseModel):
    user_id: str
    badge_type: str

# Initialize FastAPI app
app = FastAPI(
    title="Growth Engine API",
    description="Social Media Growth Automation API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize growth engine
growth_engine = GrowthEngine()

@app.on_event("startup")
async def startup_event():
    """Initialize the growth engine on startup."""
    logger.info("Starting Growth Engine API")
    await growth_engine.schedule_background_jobs()

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Growth Engine API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "communities": "/api/communities",
            "users": "/api/users",
            "collaborations": "/api/collaborations",
            "content": "/api/content",
            "leaderboard": "/api/leaderboard"
        }
    }

# Community endpoints
@app.get("/api/communities")
async def list_communities():
    """List all micro-communities."""
    communities = []
    for comm in growth_engine.communities.values():
        communities.append({
            "id": comm.id,
            "name": comm.name,
            "type": comm.type.value,
            "description": comm.description,
            "member_count": len(comm.members),
            "engagement_score": comm.engagement_score,
            "created_at": comm.created_at.isoformat()
        })
    return {"communities": communities}

@app.post("/api/communities")
async def create_community(request: CommunityCreateRequest):
    """Create a new micro-community."""
    try:
        community_type = CommunityType(request.type)
        community_id = await growth_engine.create_micro_community(
            name=request.name,
            community_type=community_type,
            description=request.description,
            templates=request.templates
        )
        return {"message": "Community created", "community_id": community_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid community type: {request.type}")

@app.post("/api/communities/{community_id}/join")
async def join_community(community_id: str, user_id: str):
    """Join a micro-community."""
    success = await growth_engine.join_community(user_id, community_id)
    if success:
        return {"message": f"User {user_id} joined community {community_id}"}
    else:
        raise HTTPException(status_code=400, detail="Failed to join community")

# User endpoints
@app.get("/api/users")
async def list_users():
    """List all users."""
    users = []
    for user in growth_engine.users.values():
        users.append({
            "user_id": user.user_id,
            "username": user.username,
            "xp_points": user.xp_points,
            "level": user.level,
            "badges": [badge.value for badge in user.badges],
            "communities": user.communities,
            "weekly_engagement": user.weekly_engagement,
            "total_posts": user.total_posts,
            "collaboration_count": user.collaboration_count
        })
    return {"users": users}

@app.post("/api/users")
async def create_user(request: UserCreateRequest):
    """Create a new user profile."""
    user = await growth_engine.create_user_profile(request.user_id, request.username)
    return {
        "message": "User created",
        "user": {
            "user_id": user.user_id,
            "username": user.username,
            "xp_points": user.xp_points,
            "level": user.level
        }
    }

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    """Get user profile."""
    if user_id not in growth_engine.users:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = growth_engine.users[user_id]
    return {
        "user_id": user.user_id,
        "username": user.username,
        "xp_points": user.xp_points,
        "level": user.level,
        "badges": [badge.value for badge in user.badges],
        "communities": user.communities,
        "weekly_engagement": user.weekly_engagement,
        "total_posts": user.total_posts,
        "collaboration_count": user.collaboration_count
    }

@app.post("/api/users/badges")
async def award_badge(request: BadgeAwardRequest):
    """Award a badge to a user."""
    try:
        badge_type = BadgeType(request.badge_type)
        success = await growth_engine.award_badge(request.user_id, badge_type)
        if success:
            return {"message": f"Badge {request.badge_type} awarded to user {request.user_id}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to award badge")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid badge type: {request.badge_type}")

# Collaboration endpoints
@app.get("/api/collaborations")
async def list_collaborations():
    """List all collaborations."""
    collaborations = []
    for collab in growth_engine.collaborations.values():
        collaborations.append({
            "id": collab.id,
            "user1_id": collab.user1_id,
            "user2_id": collab.user2_id,
            "platform": collab.platform,
            "content_type": collab.content_type,
            "status": collab.status,
            "engagement_metrics": collab.engagement_metrics
        })
    return {"collaborations": collaborations}

@app.post("/api/collaborations")
async def create_collaboration(request: CollaborationCreateRequest):
    """Create a new collaboration."""
    collab_id = await growth_engine.create_collaboration(
        user1_id=request.user1_id,
        user2_id=request.user2_id,
        platform=request.platform,
        content_type=request.content_type
    )
    return {"message": "Collaboration created", "collaboration_id": collab_id}

# Content endpoints
@app.get("/api/content/templates")
async def list_templates():
    """List all content templates."""
    templates = []
    for template in growth_engine.templates.values():
        templates.append({
            "id": template.id,
            "name": template.name,
            "type": template.type,
            "engagement_score": template.engagement_score,
            "usage_count": template.usage_count
        })
    return {"templates": templates}

@app.post("/api/content/templates")
async def create_template(request: ContentTemplateRequest):
    """Create a new content template."""
    template_id = await growth_engine.create_content_template(
        name=request.name,
        content_type=request.content_type,
        template_data=request.template_data
    )
    return {"message": "Template created", "template_id": template_id}

@app.post("/api/content/generate")
async def generate_content(request: ContentGenerateRequest):
    """Generate content using a template."""
    content = await growth_engine.generate_content_with_template(
        template_id=request.template_id,
        custom_data=request.custom_data
    )
    if not content:
        raise HTTPException(status_code=404, detail="Template not found")
    return content

@app.post("/api/content/share")
async def share_content(content_data: Dict[str, Any]):
    """Share content across platforms."""
    # This would integrate with the existing social media automation
    return {
        "message": "Content shared",
        "platforms": content_data.get("platforms", []),
        "content_id": f"content-{datetime.now().timestamp()}"
    }

# Leaderboard endpoints
@app.get("/api/leaderboard")
async def get_leaderboard(platform: str = "all"):
    """Get the current leaderboard."""
    leaderboard = await growth_engine.update_leaderboard(platform)
    return {"leaderboard": leaderboard}

# Background jobs endpoints
@app.get("/api/jobs")
async def list_background_jobs():
    """List all background jobs."""
    jobs = []
    for job in growth_engine.background_jobs:
        jobs.append({
            "id": job["id"],
            "type": job["type"],
            "schedule": job["schedule"]
        })
    return {"jobs": jobs}

@app.post("/api/jobs/{job_id}/run")
async def run_background_job(job_id: str):
    """Run a specific background job."""
    job = next((j for j in growth_engine.background_jobs if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        result = await job["function"]()
        return {"message": f"Job {job_id} completed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job failed: {str(e)}")

# API hooks endpoint
@app.get("/api/hooks")
async def get_api_hooks():
    """Get API hooks for external integrations."""
    hooks = await growth_engine.get_api_hooks()
    return {"hooks": hooks}

# Export endpoint
@app.post("/api/export/{network_name}")
async def export_data(network_name: str):
    """Export data for external network integration."""
    export_data = await growth_engine.export_data_for_external_network(network_name)
    return export_data

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "stats": {
            "users": len(growth_engine.users),
            "communities": len(growth_engine.communities),
            "collaborations": len(growth_engine.collaborations),
            "templates": len(growth_engine.templates)
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 