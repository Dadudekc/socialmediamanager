#!/usr/bin/env python3
"""
Growth Engine Dashboard - Web interface for managing and visualizing growth engine data.
Provides real-time dashboard with charts, leaderboards, and management tools.
"""

import os
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

from growth_engine import GrowthEngine, CommunityType, BadgeType
from setup_logging import setup_logging

logger = setup_logging("growth_engine_dashboard", log_dir="./logs")

# Initialize FastAPI app
app = FastAPI(title="Growth Engine Dashboard")

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

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

@app.get("/")
async def get_dashboard():
    """Serve the main dashboard HTML."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Growth Engine Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
            .stat-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .stat-number { font-size: 2em; font-weight: bold; color: #007bff; }
            .chart-container { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .leaderboard { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .leaderboard-item { display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #eee; }
            .badge { background: #007bff; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-left: 10px; }
            .tabs { display: flex; margin-bottom: 20px; }
            .tab { padding: 10px 20px; background: white; border: none; cursor: pointer; border-radius: 5px 5px 0 0; }
            .tab.active { background: #007bff; color: white; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Growth Engine Dashboard</h1>
                <p>Real-time social media growth automation monitoring</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Total Users</h3>
                    <div class="stat-number" id="total-users">0</div>
                </div>
                <div class="stat-card">
                    <h3>Communities</h3>
                    <div class="stat-number" id="total-communities">0</div>
                </div>
                <div class="stat-card">
                    <h3>Collaborations</h3>
                    <div class="stat-number" id="total-collaborations">0</div>
                </div>
                <div class="stat-card">
                    <h3>Content Templates</h3>
                    <div class="stat-number" id="total-templates">0</div>
                </div>
            </div>
            
            <div class="tabs">
                <button class="tab active" onclick="showTab('overview')">Overview</button>
                <button class="tab" onclick="showTab('communities')">Communities</button>
                <button class="tab" onclick="showTab('leaderboard')">Leaderboard</button>
                <button class="tab" onclick="showTab('content')">Content</button>
            </div>
            
            <div id="overview" class="tab-content active">
                <div class="chart-container">
                    <h3>User Growth & Engagement</h3>
                    <div id="user-growth-chart"></div>
                </div>
                <div class="chart-container">
                    <h3>Community Activity</h3>
                    <div id="community-activity-chart"></div>
                </div>
            </div>
            
            <div id="communities" class="tab-content">
                <div class="chart-container">
                    <h3>Community Members</h3>
                    <div id="community-members-chart"></div>
                </div>
                <div class="leaderboard">
                    <h3>Top Communities</h3>
                    <div id="communities-list"></div>
                </div>
            </div>
            
            <div id="leaderboard" class="tab-content">
                <div class="leaderboard">
                    <h3>Weekly Top Performers</h3>
                    <div id="leaderboard-list"></div>
                </div>
                <div class="chart-container">
                    <h3>XP Distribution</h3>
                    <div id="xp-distribution-chart"></div>
                </div>
            </div>
            
            <div id="content" class="tab-content">
                <div class="chart-container">
                    <h3>Content Template Usage</h3>
                    <div id="template-usage-chart"></div>
                </div>
                <div class="leaderboard">
                    <h3>Popular Templates</h3>
                    <div id="templates-list"></div>
                </div>
            </div>
        </div>
        
        <script>
            let ws = new WebSocket('ws://localhost:8002/ws');
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            function showTab(tabName) {
                // Hide all tab contents
                const tabContents = document.querySelectorAll('.tab-content');
                tabContents.forEach(content => content.classList.remove('active'));
                
                // Remove active class from all tabs
                const tabs = document.querySelectorAll('.tab');
                tabs.forEach(tab => tab.classList.remove('active'));
                
                // Show selected tab content
                document.getElementById(tabName).classList.add('active');
                event.target.classList.add('active');
            }
            
            function updateDashboard(data) {
                // Update stats
                document.getElementById('total-users').textContent = data.stats.users;
                document.getElementById('total-communities').textContent = data.stats.communities;
                document.getElementById('total-collaborations').textContent = data.stats.collaborations;
                document.getElementById('total-templates').textContent = data.stats.templates;
                
                // Update charts
                if (data.charts) {
                    if (data.charts.user_growth) {
                        Plotly.newPlot('user-growth-chart', data.charts.user_growth.data, data.charts.user_growth.layout);
                    }
                    if (data.charts.community_activity) {
                        Plotly.newPlot('community-activity-chart', data.charts.community_activity.data, data.charts.community_activity.layout);
                    }
                    if (data.charts.xp_distribution) {
                        Plotly.newPlot('xp-distribution-chart', data.charts.xp_distribution.data, data.charts.xp_distribution.layout);
                    }
                    if (data.charts.template_usage) {
                        Plotly.newPlot('template-usage-chart', data.charts.template_usage.data, data.charts.template_usage.layout);
                    }
                }
                
                // Update lists
                if (data.lists) {
                    if (data.lists.leaderboard) {
                        updateLeaderboardList(data.lists.leaderboard);
                    }
                    if (data.lists.communities) {
                        updateCommunitiesList(data.lists.communities);
                    }
                    if (data.lists.templates) {
                        updateTemplatesList(data.lists.templates);
                    }
                }
            }
            
            function updateLeaderboardList(leaderboard) {
                const container = document.getElementById('leaderboard-list');
                container.innerHTML = '';
                
                leaderboard.forEach((user, index) => {
                    const item = document.createElement('div');
                    item.className = 'leaderboard-item';
                    item.innerHTML = `
                        <div>
                            <strong>${index + 1}. ${user.username}</strong>
                            ${user.badges.map(badge => `<span class="badge">${badge}</span>`).join('')}
                        </div>
                        <div>${user.score} XP</div>
                    `;
                    container.appendChild(item);
                });
            }
            
            function updateCommunitiesList(communities) {
                const container = document.getElementById('communities-list');
                container.innerHTML = '';
                
                communities.forEach(community => {
                    const item = document.createElement('div');
                    item.className = 'leaderboard-item';
                    item.innerHTML = `
                        <div>
                            <strong>${community.name}</strong>
                            <span class="badge">${community.type}</span>
                        </div>
                        <div>${community.member_count} members</div>
                    `;
                    container.appendChild(item);
                });
            }
            
            function updateTemplatesList(templates) {
                const container = document.getElementById('templates-list');
                container.innerHTML = '';
                
                templates.forEach(template => {
                    const item = document.createElement('div');
                    item.className = 'leaderboard-item';
                    item.innerHTML = `
                        <div>
                            <strong>${template.name}</strong>
                            <span class="badge">${template.type}</span>
                        </div>
                        <div>${template.usage_count} uses</div>
                    `;
                    container.appendChild(item);
                });
            }
            
            // Initial load
            fetch('/api/dashboard-data')
                .then(response => response.json())
                .then(data => updateDashboard(data));
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/dashboard-data")
async def get_dashboard_data():
    """Get comprehensive dashboard data."""
    # Generate charts
    charts = await generate_dashboard_charts()
    
    # Get lists
    lists = await generate_dashboard_lists()
    
    # Get stats
    stats = {
        "users": len(growth_engine.users),
        "communities": len(growth_engine.communities),
        "collaborations": len(growth_engine.collaborations),
        "templates": len(growth_engine.templates)
    }
    
    return {
        "stats": stats,
        "charts": charts,
        "lists": lists,
        "timestamp": datetime.now().isoformat()
    }

async def generate_dashboard_charts():
    """Generate charts for the dashboard."""
    charts = {}
    
    # User growth chart
    if growth_engine.users:
        user_data = []
        for user in growth_engine.users.values():
            user_data.append({
                "username": user.username,
                "xp_points": user.xp_points,
                "level": user.level,
                "weekly_engagement": user.weekly_engagement
            })
        
        df = pd.DataFrame(user_data)
        
        # XP distribution chart
        xp_values = [user.xp_points for user in growth_engine.users.values()]
        charts["xp_distribution"] = {
            "data": [go.Histogram(x=xp_values, nbinsx=10, name="XP Distribution")],
            "layout": go.Layout(
                title="XP Distribution",
                xaxis_title="XP Points",
                yaxis_title="Number of Users"
            )
        }
        
        # User engagement chart
        engagement_data = [user.weekly_engagement for user in growth_engine.users.values()]
        usernames = [user.username for user in growth_engine.users.values()]
        
        charts["user_growth"] = {
            "data": [go.Bar(x=usernames, y=engagement_data, name="Weekly Engagement")],
            "layout": go.Layout(
                title="User Engagement",
                xaxis_title="Users",
                yaxis_title="Engagement"
            )
        }
    
    # Community activity chart
    if growth_engine.communities:
        community_names = [comm.name for comm in growth_engine.communities.values()]
        member_counts = [len(comm.members) for comm in growth_engine.communities.values()]
        
        charts["community_activity"] = {
            "data": [go.Bar(x=community_names, y=member_counts, name="Members")],
            "layout": go.Layout(
                title="Community Members",
                xaxis_title="Communities",
                yaxis_title="Member Count"
            )
        }
    
    # Template usage chart
    if growth_engine.templates:
        template_names = [template.name for template in growth_engine.templates.values()]
        usage_counts = [template.usage_count for template in growth_engine.templates.values()]
        
        charts["template_usage"] = {
            "data": [go.Pie(labels=template_names, values=usage_counts, name="Template Usage")],
            "layout": go.Layout(
                title="Content Template Usage"
            )
        }
    
    return charts

async def generate_dashboard_lists():
    """Generate lists for the dashboard."""
    lists = {}
    
    # Leaderboard
    leaderboard = await growth_engine.update_leaderboard()
    lists["leaderboard"] = leaderboard[:10]
    
    # Communities
    communities = []
    for comm in growth_engine.communities.values():
        communities.append({
            "name": comm.name,
            "type": comm.type.value,
            "member_count": len(comm.members),
            "engagement_score": comm.engagement_score
        })
    communities.sort(key=lambda x: x["member_count"], reverse=True)
    lists["communities"] = communities[:10]
    
    # Templates
    templates = []
    for template in growth_engine.templates.values():
        templates.append({
            "name": template.name,
            "type": template.type,
            "usage_count": template.usage_count,
            "engagement_score": template.engagement_score
        })
    templates.sort(key=lambda x: x["usage_count"], reverse=True)
    lists["templates"] = templates[:10]
    
    return lists

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Send dashboard data every 30 seconds
            data = await get_dashboard_data()
            await manager.send_personal_message(json.dumps(data), websocket)
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/communities")
async def get_communities():
    """Get all communities."""
    communities = []
    for comm in growth_engine.communities.values():
        communities.append({
            "id": comm.id,
            "name": comm.name,
            "type": comm.type.value,
            "description": comm.description,
            "member_count": len(comm.members),
            "engagement_score": comm.engagement_score
        })
    return {"communities": communities}

@app.get("/api/users")
async def get_users():
    """Get all users."""
    users = []
    for user in growth_engine.users.values():
        users.append({
            "user_id": user.user_id,
            "username": user.username,
            "xp_points": user.xp_points,
            "level": user.level,
            "badges": [badge.value for badge in user.badges],
            "weekly_engagement": user.weekly_engagement
        })
    return {"users": users}

@app.get("/api/leaderboard")
async def get_leaderboard():
    """Get current leaderboard."""
    leaderboard = await growth_engine.update_leaderboard()
    return {"leaderboard": leaderboard}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002) 