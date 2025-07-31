#!/usr/bin/env python3
"""
Simplified dashboard for testing without database dependencies.
"""

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

from setup_logging import setup_logging

logger = setup_logging("test_dashboard", log_dir="./logs")

class TestDashboard:
    """Simplified web dashboard for sentiment analysis visualization."""
    
    def __init__(self):
        self.app = FastAPI(title="Social Media Sentiment Dashboard", version="1.0.0")
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
        logger.info("✅ TestDashboard initialized")
    
    def setup_routes(self):
        """Setup API routes and WebSocket endpoints."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def get_dashboard():
            """Serve the main dashboard HTML."""
            return self.get_dashboard_html()
        
        @self.app.get("/api/sentiment/{ticker}")
        async def get_sentiment_data(ticker: str, hours: int = 24):
            """Get sentiment data for a specific ticker (simulated)."""
            try:
                # Generate sample data
                data = self.generate_sample_sentiment_data(ticker, hours)
                return JSONResponse(content=data)
            except Exception as e:
                logger.error(f"Error fetching sentiment data: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/tickers")
        async def get_available_tickers():
            """Get list of available tickers."""
            try:
                tickers = ["TSLA", "SPY", "QQQ", "AAPL", "MSFT"]
                return JSONResponse(content={"tickers": tickers})
            except Exception as e:
                logger.error(f"Error fetching tickers: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/summary")
        async def get_summary_stats():
            """Get summary statistics (simulated)."""
            try:
                stats = {
                    "total_posts": 1250,
                    "total_tickers": 5,
                    "avg_sentiment": 0.15,
                    "bullish_posts": 450,
                    "bearish_posts": 380,
                    "neutral_posts": 420,
                    "last_updated": datetime.now().isoformat()
                }
                return JSONResponse(content=stats)
            except Exception as e:
                logger.error(f"Error fetching summary stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/status")
        async def get_status():
            """Get system status."""
            try:
                status = {
                    "status": "running",
                    "timestamp": datetime.now().isoformat(),
                    "components": {
                        "database": "simulated",
                        "sentiment_analysis": "active",
                        "notifications": "active",
                        "dashboard": "active"
                    },
                    "uptime": "00:05:30"
                }
                return JSONResponse(content=status)
            except Exception as e:
                logger.error(f"Error fetching status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.active_connections.append(websocket)
            try:
                while True:
                    # Send real-time updates every 30 seconds
                    data = await self.get_realtime_data()
                    await websocket.send_text(json.dumps(data))
                    await asyncio.sleep(30)
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)
    
    def generate_sample_sentiment_data(self, ticker: str, hours: int = 24) -> List[Dict]:
        """Generate sample sentiment data for testing."""
        import numpy as np
        
        # Generate timestamps
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        timestamps = pd.date_range(start=start_time, end=end_time, freq='H')
        
        # Generate sample data
        np.random.seed(42)  # For reproducible results
        n_samples = len(timestamps)
        
        data = []
        for i, timestamp in enumerate(timestamps):
            # Generate realistic sentiment values
            base_sentiment = 0.1 + 0.2 * np.sin(i / 10)  # Cyclical pattern
            noise = np.random.normal(0, 0.1)
            textblob = np.clip(base_sentiment + noise, -1, 1)
            vader = np.clip(base_sentiment + noise * 0.8, -1, 1)
            
            # Determine category
            avg_sentiment = (textblob + vader) / 2
            if avg_sentiment > 0.1:
                category = "Bullish"
            elif avg_sentiment < -0.1:
                category = "Bearish"
            else:
                category = "Neutral"
            
            data.append({
                "id": i + 1,
                "ticker": ticker,
                "timestamp": timestamp.isoformat(),
                "content": f"Sample post about {ticker} #{i+1}",
                "textblob": round(textblob, 3),
                "vader": round(vader, 3),
                "category": category
            })
        
        return data
    
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
            color: white;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .card h3 {
            margin-top: 0;
            color: #fff;
            font-size: 1.3em;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-online { background-color: #4CAF50; }
        .status-offline { background-color: #f44336; }
        .chart-container {
            height: 300px;
            margin-top: 15px;
        }
        .ticker-selector {
            margin-bottom: 20px;
        }
        .ticker-selector select {
            padding: 10px 15px;
            border: none;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            font-size: 16px;
            cursor: pointer;
        }
        .ticker-selector select option {
            background: #333;
            color: white;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-item {
            text-align: center;
            padding: 15px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #4CAF50;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Social Media Sentiment Dashboard</h1>
            <p>Real-time sentiment analysis for stock market insights</p>
        </div>
        
        <div class="ticker-selector">
            <select id="tickerSelect" onchange="loadTickerData()">
                <option value="TSLA">TSLA - Tesla</option>
                <option value="SPY">SPY - S&P 500 ETF</option>
                <option value="QQQ">QQQ - NASDAQ ETF</option>
                <option value="AAPL">AAPL - Apple</option>
                <option value="MSFT">MSFT - Microsoft</option>
            </select>
        </div>
        
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value" id="totalPosts">1,250</div>
                <div class="stat-label">Total Posts</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="avgSentiment">0.15</div>
                <div class="stat-label">Avg Sentiment</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="bullishPosts">450</div>
                <div class="stat-label">Bullish</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="bearishPosts">380</div>
                <div class="stat-label">Bearish</div>
            </div>
        </div>
        
        <div class="dashboard-grid">
            <div class="card">
                <h3><span class="status-indicator status-online"></span>Sentiment Trend</h3>
                <div id="sentimentChart" class="chart-container"></div>
            </div>
            
            <div class="card">
                <h3><span class="status-indicator status-online"></span>Sentiment Distribution</h3>
                <div id="distributionChart" class="chart-container"></div>
            </div>
            
            <div class="card">
                <h3><span class="status-indicator status-online"></span>System Status</h3>
                <div id="statusInfo">
                    <p><strong>Database:</strong> <span class="status-online"></span>Simulated</p>
                    <p><strong>Sentiment Analysis:</strong> <span class="status-online"></span>Active</p>
                    <p><strong>Notifications:</strong> <span class="status-online"></span>Active</p>
                    <p><strong>Dashboard:</strong> <span class="status-online"></span>Active</p>
                    <p><strong>Last Updated:</strong> <span id="lastUpdated">Loading...</span></p>
                </div>
            </div>
            
            <div class="card">
                <h3><span class="status-indicator status-online"></span>Real-time Feed</h3>
                <div id="realtimeFeed" style="height: 300px; overflow-y: auto;">
                    <p>Loading real-time data...</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentTicker = 'TSLA';
        
        function loadTickerData() {
            currentTicker = document.getElementById('tickerSelect').value;
            fetchSentimentData();
            fetchSummaryStats();
        }
        
        async function fetchSentimentData() {
            try {
                const response = await fetch(`/api/sentiment/${currentTicker}?hours=24`);
                const data = await response.json();
                updateSentimentChart(data);
                updateDistributionChart(data);
            } catch (error) {
                console.error('Error fetching sentiment data:', error);
            }
        }
        
        async function fetchSummaryStats() {
            try {
                const response = await fetch('/api/summary');
                const data = await response.json();
                updateStats(data);
            } catch (error) {
                console.error('Error fetching summary stats:', error);
            }
        }
        
        function updateSentimentChart(data) {
            const timestamps = data.map(d => d.timestamp);
            const textblob = data.map(d => d.textblob);
            const vader = data.map(d => d.vader);
            
            const trace1 = {
                x: timestamps,
                y: textblob,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'TextBlob',
                line: {color: '#4CAF50'}
            };
            
            const trace2 = {
                x: timestamps,
                y: vader,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'VADER',
                line: {color: '#2196F3'}
            };
            
            const layout = {
                title: `${currentTicker} Sentiment Over Time`,
                xaxis: {title: 'Time'},
                yaxis: {title: 'Sentiment Score', range: [-1, 1]},
                plot_bgcolor: 'rgba(0,0,0,0)',
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: {color: 'white'}
            };
            
            Plotly.newPlot('sentimentChart', [trace1, trace2], layout);
        }
        
        function updateDistributionChart(data) {
            const categories = data.reduce((acc, d) => {
                acc[d.category] = (acc[d.category] || 0) + 1;
                return acc;
            }, {});
            
            const trace = {
                values: Object.values(categories),
                labels: Object.keys(categories),
                type: 'pie',
                marker: {
                    colors: ['#4CAF50', '#FFC107', '#f44336']
                }
            };
            
            const layout = {
                title: 'Sentiment Distribution',
                plot_bgcolor: 'rgba(0,0,0,0)',
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: {color: 'white'}
            };
            
            Plotly.newPlot('distributionChart', [trace], layout);
        }
        
        function updateStats(data) {
            document.getElementById('totalPosts').textContent = data.total_posts.toLocaleString();
            document.getElementById('avgSentiment').textContent = data.avg_sentiment.toFixed(2);
            document.getElementById('bullishPosts').textContent = data.bullish_posts.toLocaleString();
            document.getElementById('bearishPosts').textContent = data.bearish_posts.toLocaleString();
            document.getElementById('lastUpdated').textContent = new Date().toLocaleTimeString();
        }
        
        // WebSocket connection for real-time updates
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            updateRealtimeFeed(data);
        };
        
        function updateRealtimeFeed(data) {
            const feed = document.getElementById('realtimeFeed');
            const timestamp = new Date().toLocaleTimeString();
            const entry = document.createElement('p');
            entry.innerHTML = `<strong>${timestamp}</strong>: ${data.message || 'System update'}`;
            feed.insertBefore(entry, feed.firstChild);
            
            // Keep only last 10 entries
            while (feed.children.length > 10) {
                feed.removeChild(feed.lastChild);
            }
        }
        
        // Initial load
        loadTickerData();
        
        // Refresh data every 30 seconds
        setInterval(loadTickerData, 30000);
    </script>
</body>
</html>
        """
    
    async def get_realtime_data(self) -> Dict:
        """Get real-time data for WebSocket updates."""
        return {
            "timestamp": datetime.now().isoformat(),
            "message": f"System update for {datetime.now().strftime('%H:%M:%S')}",
            "status": "running",
            "active_connections": len(self.active_connections)
        }
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the dashboard server."""
        uvicorn.run(self.app, host=host, port=port)

if __name__ == "__main__":
    dashboard = TestDashboard()
    dashboard.run() 