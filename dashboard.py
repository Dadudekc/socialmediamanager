import os
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path

from project_config import config
from db_handler import DatabaseHandler
from setup_logging import setup_logging

logger = setup_logging("dashboard", log_dir=config.LOG_DIR)

class Dashboard:
    """Web dashboard for sentiment analysis visualization."""
    
    def __init__(self):
        self.app = FastAPI(title="Social Media Sentiment Dashboard", version="1.0.0")
        self.db = DatabaseHandler(logger)
        self.active_connections: List[WebSocket] = []
        
        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup static files
        static_dir = Path(__file__).parent / "static"
        static_dir.mkdir(exist_ok=True)
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        
        self.setup_routes()
    
    def setup_routes(self):
        """Setup API routes and WebSocket endpoints."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def get_dashboard():
            """Serve the main dashboard HTML."""
            return self.get_dashboard_html()
        
        @self.app.get("/api/sentiment/{ticker}")
        async def get_sentiment_data(ticker: str, hours: int = 24):
            """Get sentiment data for a specific ticker."""
            try:
                data = self.db.fetch_sentiment(ticker, limit=1000)
                df = pd.DataFrame(data, columns=['id', 'ticker', 'timestamp', 'content', 'textblob', 'vader', 'category'])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Filter by time range
                cutoff_time = datetime.now() - timedelta(hours=hours)
                df = df[df['timestamp'] >= cutoff_time]
                
                return JSONResponse(content=df.to_dict('records'))
            except Exception as e:
                logger.error(f"Error fetching sentiment data: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/tickers")
        async def get_available_tickers():
            """Get list of available tickers."""
            try:
                tickers = self.db.get_available_tickers()
                return JSONResponse(content={"tickers": tickers})
            except Exception as e:
                logger.error(f"Error fetching tickers: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/summary")
        async def get_summary_stats():
            """Get summary statistics."""
            try:
                stats = self.db.get_summary_stats()
                return JSONResponse(content=stats)
            except Exception as e:
                logger.error(f"Error fetching summary stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.active_connections.append(websocket)
            try:
                while True:
                    # Send real-time updates every 30 seconds
                    await asyncio.sleep(30)
                    data = await self.get_realtime_data()
                    await websocket.send_text(json.dumps(data))
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
    
    def get_dashboard_html(self) -> str:
        """Generate the main dashboard HTML."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Social Media Sentiment Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .controls {
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }
        .ticker-selector {
            display: flex;
            gap: 10px;
            align-items: center;
            margin-bottom: 20px;
        }
        select, input, button {
            padding: 10px 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            cursor: pointer;
            transition: background 0.3s;
        }
        button:hover {
            background: #5a6fd8;
        }
        .charts-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            padding: 20px;
        }
        .chart {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            padding: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .status-online { background: #28a745; }
        .status-offline { background: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Social Media Sentiment Dashboard</h1>
            <p>Real-time sentiment analysis from multiple platforms</p>
            <div>
                <span class="status-indicator status-online" id="status-indicator"></span>
                <span id="status-text">Connected</span>
            </div>
        </div>
        
        <div class="controls">
            <div class="ticker-selector">
                <label for="ticker-select">Ticker:</label>
                <select id="ticker-select">
                    <option value="TSLA">TSLA</option>
                    <option value="SPY">SPY</option>
                    <option value="QQQ">QQQ</option>
                </select>
                <label for="time-range">Time Range:</label>
                <select id="time-range">
                    <option value="1">1 Hour</option>
                    <option value="6">6 Hours</option>
                    <option value="24" selected>24 Hours</option>
                    <option value="168">7 Days</option>
                </select>
                <button onclick="loadData()">Refresh</button>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="total-messages">-</div>
                <div class="stat-label">Total Messages</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="bullish-percent">-</div>
                <div class="stat-label">Bullish %</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="bearish-percent">-</div>
                <div class="stat-label">Bearish %</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="neutral-percent">-</div>
                <div class="stat-label">Neutral %</div>
            </div>
        </div>
        
        <div class="charts-container">
            <div class="chart">
                <h3>Sentiment Over Time</h3>
                <div id="sentiment-chart"></div>
            </div>
            <div class="chart">
                <h3>Sentiment Distribution</h3>
                <div id="distribution-chart"></div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let currentData = [];
        
        // Initialize WebSocket connection
        function initWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            ws.onopen = function() {
                document.getElementById('status-indicator').className = 'status-indicator status-online';
                document.getElementById('status-text').textContent = 'Connected';
            };
            ws.onclose = function() {
                document.getElementById('status-indicator').className = 'status-indicator status-offline';
                document.getElementById('status-text').textContent = 'Disconnected';
                setTimeout(initWebSocket, 5000);
            };
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
        }
        
        async function loadData() {
            const ticker = document.getElementById('ticker-select').value;
            const hours = document.getElementById('time-range').value;
            
            try {
                const response = await fetch(`/api/sentiment/${ticker}?hours=${hours}`);
                const data = await response.json();
                currentData = data;
                updateCharts(data);
                updateStats(data);
            } catch (error) {
                console.error('Error loading data:', error);
            }
        }
        
        function updateCharts(data) {
            if (!data || data.length === 0) return;
            
            // Sentiment over time chart
            const df = data.map(d => ({
                timestamp: new Date(d.timestamp),
                sentiment: d.category,
                score: d.vader
            }));
            
            const timeData = {
                x: df.map(d => d.timestamp),
                y: df.map(d => d.score),
                mode: 'lines+markers',
                type: 'scatter',
                name: 'Sentiment Score',
                line: {color: '#667eea'}
            };
            
            const layout = {
                title: 'Sentiment Score Over Time',
                xaxis: {title: 'Time'},
                yaxis: {title: 'Sentiment Score'},
                height: 400
            };
            
            Plotly.newPlot('sentiment-chart', [timeData], layout);
            
            // Distribution chart
            const sentimentCounts = {};
            df.forEach(d => {
                sentimentCounts[d.sentiment] = (sentimentCounts[d.sentiment] || 0) + 1;
            });
            
            const pieData = [{
                values: Object.values(sentimentCounts),
                labels: Object.keys(sentimentCounts),
                type: 'pie',
                marker: {
                    colors: ['#28a745', '#dc3545', '#ffc107']
                }
            }];
            
            const pieLayout = {
                title: 'Sentiment Distribution',
                height: 400
            };
            
            Plotly.newPlot('distribution-chart', pieData, pieLayout);
        }
        
        function updateStats(data) {
            if (!data || data.length === 0) return;
            
            const total = data.length;
            const bullish = data.filter(d => d.category === 'Bullish').length;
            const bearish = data.filter(d => d.category === 'Bearish').length;
            const neutral = data.filter(d => d.category === 'Neutral').length;
            
            document.getElementById('total-messages').textContent = total;
            document.getElementById('bullish-percent').textContent = `${((bullish/total)*100).toFixed(1)}%`;
            document.getElementById('bearish-percent').textContent = `${((bearish/total)*100).toFixed(1)}%`;
            document.getElementById('neutral-percent').textContent = `${((neutral/total)*100).toFixed(1)}%`;
        }
        
        function updateDashboard(data) {
            // Update with real-time data
            updateCharts(data);
            updateStats(data);
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            initWebSocket();
            loadData();
            
            // Auto-refresh every 5 minutes
            setInterval(loadData, 300000);
        });
    </script>
</body>
</html>
        """
    
    async def get_realtime_data(self) -> Dict:
        """Get real-time data for WebSocket updates."""
        try:
            # Get latest sentiment data
            data = self.db.fetch_sentiment("TSLA", limit=100)
            return {
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
        except Exception as e:
            logger.error(f"Error getting real-time data: {e}")
            return {"error": str(e)}
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the dashboard server."""
        logger.info(f"🚀 Starting dashboard server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)

if __name__ == "__main__":
    dashboard = Dashboard()
    dashboard.run() 