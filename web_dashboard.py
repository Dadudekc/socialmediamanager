#!/usr/bin/env python3
"""
Ultimate Follow Builder Web Dashboard - Real-time monitoring and control interface.
Provides live analytics, campaign management, and growth tracking.
"""

import os
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from pathlib import Path

from ultimate_follow_builder import UltimateFollowBuilder, BuilderConfig, BuilderMode

app = FastAPI(title="Ultimate Follow Builder Dashboard", version="1.0.0")

# Global dashboard state
dashboard_state = {
    "active_campaigns": [],
    "total_follows": 0,
    "total_engagements": 0,
    "total_followers_gained": 0,
    "account_health": {},
    "recent_activities": [],
    "growth_metrics": {},
    "roi_data": {}
}

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

# HTML Dashboard Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ultimate Follow Builder Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f0f23; color: #fff; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; background: linear-gradient(45deg, #ff6b6b, #4ecdc4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: #1a1a2e; padding: 20px; border-radius: 10px; border: 1px solid #333; }
        .stat-card h3 { color: #4ecdc4; margin-bottom: 10px; }
        .stat-value { font-size: 2em; font-weight: bold; color: #ff6b6b; }
        .charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
        .chart-container { background: #1a1a2e; padding: 20px; border-radius: 10px; border: 1px solid #333; }
        .chart-container h3 { color: #4ecdc4; margin-bottom: 15px; }
        .controls { background: #1a1a2e; padding: 20px; border-radius: 10px; border: 1px solid #333; margin-bottom: 30px; }
        .controls h3 { color: #4ecdc4; margin-bottom: 15px; }
        .control-group { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .control-item { display: flex; flex-direction: column; }
        .control-item label { margin-bottom: 5px; color: #ccc; }
        .control-item input, .control-item select { padding: 8px; border-radius: 5px; border: 1px solid #333; background: #2a2a3e; color: #fff; }
        .btn { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .btn-primary { background: #4ecdc4; color: #000; }
        .btn-danger { background: #ff6b6b; color: #fff; }
        .btn-success { background: #51cf66; color: #fff; }
        .activities { background: #1a1a2e; padding: 20px; border-radius: 10px; border: 1px solid #333; }
        .activities h3 { color: #4ecdc4; margin-bottom: 15px; }
        .activity-item { padding: 10px; border-bottom: 1px solid #333; }
        .activity-item:last-child { border-bottom: none; }
        .status-online { color: #51cf66; }
        .status-offline { color: #ff6b6b; }
        .status-warning { color: #ffd43b; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Ultimate Follow Builder Dashboard</h1>
            <p>Real-time social media growth automation monitoring</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>📈 Total Follows</h3>
                <div class="stat-value" id="total-follows">0</div>
            </div>
            <div class="stat-card">
                <h3>💬 Total Engagements</h3>
                <div class="stat-value" id="total-engagements">0</div>
            </div>
            <div class="stat-card">
                <h3>👥 Followers Gained</h3>
                <div class="stat-value" id="followers-gained">0</div>
            </div>
            <div class="stat-card">
                <h3>💰 Estimated ROI</h3>
                <div class="stat-value" id="estimated-roi">$0</div>
            </div>
        </div>

        <div class="charts-grid">
            <div class="chart-container">
                <h3>📊 Growth Metrics</h3>
                <canvas id="growthChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>🏥 Account Health</h3>
                <canvas id="healthChart"></canvas>
            </div>
        </div>

        <div class="controls">
            <h3>🎛️ Campaign Controls</h3>
            <div class="control-group">
                <div class="control-item">
                    <label>Niche:</label>
                    <select id="niche-select">
                        <option value="fitness">Fitness</option>
                        <option value="technology">Technology</option>
                        <option value="fashion">Fashion</option>
                        <option value="business">Business</option>
                        <option value="lifestyle">Lifestyle</option>
                    </select>
                </div>
                <div class="control-item">
                    <label>Platform:</label>
                    <select id="platform-select">
                        <option value="instagram">Instagram</option>
                        <option value="twitter">Twitter</option>
                        <option value="tiktok">TikTok</option>
                        <option value="linkedin">LinkedIn</option>
                    </select>
                </div>
                <div class="control-item">
                    <label>Mode:</label>
                    <select id="mode-select">
                        <option value="safe">Safe</option>
                        <option value="conservative">Conservative</option>
                        <option value="moderate">Moderate</option>
                        <option value="aggressive">Aggressive</option>
                    </select>
                </div>
                <div class="control-item">
                    <label>Daily Follow Limit:</label>
                    <input type="number" id="follow-limit" value="50" min="10" max="200">
                </div>
            </div>
            <div style="margin-top: 15px;">
                <button class="btn btn-success" onclick="startCampaign()">🚀 Start Campaign</button>
                <button class="btn btn-danger" onclick="stopCampaign()">⏹️ Stop Campaign</button>
                <button class="btn btn-primary" onclick="refreshData()">🔄 Refresh Data</button>
            </div>
        </div>

        <div class="activities">
            <h3>📝 Recent Activities</h3>
            <div id="activities-list">
                <div class="activity-item">Dashboard loaded. Ready to start campaigns.</div>
            </div>
        </div>
    </div>

    <script>
        let growthChart, healthChart;
        let ws;

        // Initialize charts
        function initCharts() {
            const growthCtx = document.getElementById('growthChart').getContext('2d');
            growthChart = new Chart(growthCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Followers Gained',
                        data: [],
                        borderColor: '#4ecdc4',
                        backgroundColor: 'rgba(78, 205, 196, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            labels: { color: '#fff' }
                        }
                    },
                    scales: {
                        y: {
                            ticks: { color: '#fff' }
                        },
                        x: {
                            ticks: { color: '#fff' }
                        }
                    }
                }
            });

            const healthCtx = document.getElementById('healthChart').getContext('2d');
            healthChart = new Chart(healthCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Instagram', 'Twitter', 'TikTok', 'LinkedIn'],
                    datasets: [{
                        data: [100, 100, 100, 100],
                        backgroundColor: ['#4ecdc4', '#ff6b6b', '#ffd43b', '#51cf66']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            labels: { color: '#fff' }
                        }
                    }
                }
            });
        }

        // Connect to WebSocket
        function connectWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onopen = function() {
                addActivity('Connected to dashboard', 'status-online');
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            ws.onclose = function() {
                addActivity('Disconnected from dashboard', 'status-offline');
                setTimeout(connectWebSocket, 5000);
            };
        }

        // Update dashboard with new data
        function updateDashboard(data) {
            if (data.total_follows !== undefined) {
                document.getElementById('total-follows').textContent = data.total_follows;
            }
            if (data.total_engagements !== undefined) {
                document.getElementById('total-engagements').textContent = data.total_engagements;
            }
            if (data.total_followers_gained !== undefined) {
                document.getElementById('followers-gained').textContent = data.total_followers_gained;
            }
            if (data.estimated_roi !== undefined) {
                document.getElementById('estimated-roi').textContent = `$${data.estimated_roi}`;
            }
            if (data.account_health !== undefined) {
                updateHealthChart(data.account_health);
            }
            if (data.growth_metrics !== undefined) {
                updateGrowthChart(data.growth_metrics);
            }
            if (data.recent_activities !== undefined) {
                updateActivities(data.recent_activities);
            }
        }

        // Update health chart
        function updateHealthChart(health) {
            const platforms = ['instagram', 'twitter', 'tiktok', 'linkedin'];
            const values = platforms.map(p => health[p]?.health_score || 0);
            
            healthChart.data.datasets[0].data = values;
            healthChart.update();
        }

        // Update growth chart
        function updateGrowthChart(metrics) {
            const now = new Date().toLocaleTimeString();
            growthChart.data.labels.push(now);
            growthChart.data.datasets[0].data.push(metrics.followers_gained || 0);
            
            if (growthChart.data.labels.length > 20) {
                growthChart.data.labels.shift();
                growthChart.data.datasets[0].data.shift();
            }
            
            growthChart.update();
        }

        // Add activity to list
        function addActivity(message, className = '') {
            const activitiesList = document.getElementById('activities-list');
            const activityItem = document.createElement('div');
            activityItem.className = `activity-item ${className}`;
            activityItem.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            activitiesList.insertBefore(activityItem, activitiesList.firstChild);
            
            if (activitiesList.children.length > 10) {
                activitiesList.removeChild(activitiesList.lastChild);
            }
        }

        // Update activities list
        function updateActivities(activities) {
            const activitiesList = document.getElementById('activities-list');
            activitiesList.innerHTML = '';
            activities.forEach(activity => {
                const activityItem = document.createElement('div');
                activityItem.className = 'activity-item';
                activityItem.textContent = activity;
                activitiesList.appendChild(activityItem);
            });
        }

        // Campaign controls
        function startCampaign() {
            const niche = document.getElementById('niche-select').value;
            const platform = document.getElementById('platform-select').value;
            const mode = document.getElementById('mode-select').value;
            const followLimit = document.getElementById('follow-limit').value;
            
            const campaignData = {
                action: 'start_campaign',
                niche: niche,
                platform: platform,
                mode: mode,
                follow_limit: parseInt(followLimit)
            };
            
            ws.send(JSON.stringify(campaignData));
            addActivity(`Starting ${niche} campaign on ${platform}`, 'status-online');
        }

        function stopCampaign() {
            ws.send(JSON.stringify({action: 'stop_campaign'}));
            addActivity('Stopping all campaigns', 'status-warning');
        }

        function refreshData() {
            ws.send(JSON.stringify({action: 'refresh_data'}));
            addActivity('Refreshing dashboard data', 'status-online');
        }

        // Initialize dashboard
        window.onload = function() {
            initCharts();
            connectWebSocket();
        };
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the main dashboard page."""
    return DASHBOARD_HTML

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        # Send initial data
        await websocket.send_text(json.dumps(dashboard_state))
        
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
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def handle_start_campaign(data: Dict, websocket: WebSocket):
    """Handle campaign start request."""
    try:
        # Create builder configuration
        config = BuilderConfig(
            mode=BuilderMode(data["mode"]),
            platforms=[data["platform"]],
            daily_follow_limit=data["follow_limit"],
            daily_unfollow_limit=int(data["follow_limit"] * 0.8),
            daily_engagement_limit=data["follow_limit"] * 2,
            engagement_window_days=3,
            safety_settings={},
            ai_features_enabled=True,
            analytics_enabled=True
        )
        
        # Initialize builder
        builder = UltimateFollowBuilder(config)
        
        # Create target audience
        target_audience = {
            "min_followers": 2000,
            "max_followers": 50000,
            "min_engagement_rate": 0.02,
            "interests": [data["niche"]],
            "locations": ["United States", "Canada"]
        }
        
        # Run campaign
        result = await builder.run_ultimate_builder(data["niche"], target_audience)
        
        # Update dashboard state
        update_dashboard_state(result)
        
        # Send updated data to client
        await websocket.send_text(json.dumps(dashboard_state))
        
    except Exception as e:
        await websocket.send_text(json.dumps({"error": str(e)}))

async def handle_stop_campaign(websocket: WebSocket):
    """Handle campaign stop request."""
    dashboard_state["active_campaigns"] = []
    await websocket.send_text(json.dumps({"message": "Campaigns stopped"}))

async def handle_refresh_data(websocket: WebSocket):
    """Handle data refresh request."""
    await websocket.send_text(json.dumps(dashboard_state))

def update_dashboard_state(result: Dict):
    """Update dashboard state with campaign results."""
    if "execution_results" in result:
        metrics = result["execution_results"].get("growth_metrics", {})
        
        dashboard_state["total_follows"] += metrics.get("total_follows", 0)
        dashboard_state["total_engagements"] += metrics.get("total_engagements", 0)
        dashboard_state["total_followers_gained"] += metrics.get("estimated_followers_gained", 0)
        
        # Calculate ROI
        estimated_value_per_follower = 2.0
        dashboard_state["roi_data"]["estimated_roi"] = dashboard_state["total_followers_gained"] * estimated_value_per_follower
        
        # Update account health
        if "account_health" in result["execution_results"]:
            dashboard_state["account_health"] = result["execution_results"]["account_health"]
        
        # Add recent activity
        activity = f"Campaign completed: {result.get('strategy_id', 'Unknown')}"
        dashboard_state["recent_activities"].insert(0, activity)
        if len(dashboard_state["recent_activities"]) > 10:
            dashboard_state["recent_activities"] = dashboard_state["recent_activities"][:10]

@app.get("/api/stats")
async def get_stats():
    """Get current dashboard statistics."""
    return dashboard_state

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    print("🚀 Starting Ultimate Follow Builder Dashboard...")
    print("📊 Dashboard available at: http://localhost:8003")
    print("🌐 WebSocket endpoint: ws://localhost:8003/ws")
    
    uvicorn.run(app, host="0.0.0.0", port=8003) 