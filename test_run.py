#!/usr/bin/env python3
"""
Simple test script to run the social media manager without database dependencies.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Set environment variables for testing
os.environ['DEBUG_MODE'] = 'true'
os.environ['LOG_LEVEL'] = 'INFO'
os.environ['LOG_DIR'] = './logs'

# Import components
from setup_logging import setup_logging
from test_dashboard import TestDashboard
from test_notification_system import TestNotificationSystem
from test_predictive_models import TestSentimentPredictor

# Setup logging
logger = setup_logging("test_run", log_dir="./logs")

class TestApp:
    """Test application without database dependencies."""
    
    def __init__(self):
        self.predictor = TestSentimentPredictor()
        self.notification_system = TestNotificationSystem()
        self.dashboard = TestDashboard()
        
        logger.info("✅ Test application initialized")
    
    async def start_dashboard(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the web dashboard."""
        logger.info(f"🌐 Starting dashboard on {host}:{port}")
        
        try:
            import uvicorn
            config = uvicorn.Config(
                app=self.dashboard.app,
                host=host,
                port=port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
        except Exception as e:
            logger.error(f"❌ Error starting dashboard: {e}")
    
    async def test_sentiment_analysis(self, text: str):
        """Test sentiment analysis functionality."""
        logger.info(f"🔍 Testing sentiment analysis for: {text[:50]}...")
        
        try:
            # Test basic sentiment analysis
            from textblob import TextBlob
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            
            # TextBlob analysis
            blob = TextBlob(text)
            textblob_sentiment = blob.sentiment.polarity
            
            # VADER analysis
            analyzer = SentimentIntensityAnalyzer()
            vader_scores = analyzer.polarity_scores(text)
            vader_sentiment = vader_scores['compound']
            
            logger.info(f"📊 TextBlob sentiment: {textblob_sentiment:.3f}")
            logger.info(f"📊 VADER sentiment: {vader_sentiment:.3f}")
            
            return {
                'textblob': textblob_sentiment,
                'vader': vader_sentiment,
                'text': text
            }
            
        except Exception as e:
            logger.error(f"❌ Error in sentiment analysis: {e}")
            return None
    
    def get_status(self):
        """Get the current status of all components."""
        status = {
            "timestamp": "2025-07-31T05:34:00",
            "components": {
                "predictor": "initialized" if self.predictor else "not_initialized",
                "notification_system": "initialized" if self.notification_system else "not_initialized",
                "dashboard": "initialized" if self.dashboard else "not_initialized",
                "database": "disabled_for_testing"
            },
            "models": self.predictor.get_model_performance() if self.predictor else {}
        }
        
        return status

async def main():
    """Main test function."""
    logger.info("🚀 Starting test application...")
    
    # Create test app
    app = TestApp()
    
    # Test sentiment analysis
    test_texts = [
        "Tesla stock is amazing! Great earnings report!",
        "I hate this company, terrible management",
        "The market is neutral today, nothing special",
        "TSLA to the moon! 🚀🚀🚀",
        "This stock is going to crash, sell everything!"
    ]
    
    logger.info("🧪 Testing sentiment analysis...")
    for text in test_texts:
        result = await app.test_sentiment_analysis(text)
        if result:
            logger.info(f"✅ Test passed for: {text[:30]}...")
    
    # Get status
    status = app.get_status()
    logger.info(f"📊 Application status: {status}")
    
    # Start dashboard
    logger.info("🌐 Starting dashboard...")
    await app.start_dashboard(port=8000)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Test application interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test application error: {e}")
        sys.exit(1) 