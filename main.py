#!/usr/bin/env python3
"""
Social Media Sentiment Analysis - Main Application
=================================================

This is the main entry point for the social media sentiment analysis system.
It orchestrates all components including scraping, analysis, prediction, 
trading, notifications, and the dashboard.

Usage:
    python main.py [options]

Options:
    --mode MODE           Operation mode: 'scraping', 'dashboard', 'trading', 'all'
    --tickers TICKERS     Comma-separated list of tickers to monitor
    --interval MINUTES    Scraping interval in minutes (default: 15)
    --duration HOURS      Duration to run in hours (default: 8)
    --port PORT          Dashboard port (default: 8000)
    --host HOST          Dashboard host (default: 0.0.0.0)
"""

import os
import sys
import asyncio
import argparse
import signal
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uvicorn
from pathlib import Path

# Import all components
from project_config import config
from setup_logging import setup_logging
from sentiment_scraper import run_multi_ticker_scraper
from multi_platform_streamer import stream_and_store_posts
from dashboard import Dashboard
from predictive_models import SentimentPredictor
from trading_api import TradingAPI
from notification_system import NotificationSystem
from db_handler import DatabaseHandler

# Setup logging
logger = setup_logging("main", log_dir=config.LOG_DIR)

class SentimentAnalysisApp:
    """Main application class that orchestrates all components."""
    
    def __init__(self):
        self.db = DatabaseHandler(logger)
        self.predictor = SentimentPredictor()
        self.notification_system = NotificationSystem()
        self.dashboard = Dashboard()
        self.trading_api = None
        
        # Initialize trading API if credentials are available
        try:
            if config.get_env("ALPACA_API_KEY") and config.get_env("ALPACA_SECRET_KEY"):
                self.trading_api = TradingAPI(paper_trading=True)
                logger.info("✅ Trading API initialized")
        except Exception as e:
            logger.warning(f"⚠️ Trading API not available: {e}")
        
        # Application state
        self.running = False
        self.tasks = []
        
        logger.info("✅ Sentiment Analysis Application initialized")
    
    async def start_scraping(self, tickers: List[str], interval_minutes: int = 15, 
                           duration_hours: int = 8) -> None:
        """Start the scraping process."""
        logger.info(f"🔍 Starting scraping for tickers: {tickers}")
        
        try:
            # Run the multi-ticker scraper
            await run_multi_ticker_scraper(
                tickers=tickers,
                interval_minutes=interval_minutes,
                run_duration_hours=duration_hours
            )
        except Exception as e:
            logger.error(f"❌ Error in scraping process: {e}")
    
    async def start_streaming(self, config: Dict, interval_seconds: int = 60,
                            duration_seconds: int = 3600) -> None:
        """Start the multi-platform streaming process."""
        logger.info("📡 Starting multi-platform streaming")
        
        try:
            async for batch in stream_and_store_posts(
                config, self.db, interval_seconds, duration_seconds
            ):
                if batch:
                    logger.info(f"📊 Processed {len(batch)} posts from streaming")
        except Exception as e:
            logger.error(f"❌ Error in streaming process: {e}")
    
    async def start_dashboard(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Start the web dashboard."""
        logger.info(f"🌐 Starting dashboard on {host}:{port}")
        
        try:
            # Run dashboard in background
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
    
    async def start_notifications(self, tickers: List[str], interval_minutes: int = 5) -> None:
        """Start the notification monitoring system."""
        logger.info(f"🔔 Starting notification monitoring for {tickers}")
        
        try:
            await self.notification_system.monitor_sentiment_changes(
                tickers=tickers,
                interval_minutes=interval_minutes
            )
        except Exception as e:
            logger.error(f"❌ Error in notification system: {e}")
    
    async def start_trading_monitor(self, tickers: List[str], interval_minutes: int = 30) -> None:
        """Start the trading monitoring system."""
        if not self.trading_api:
            logger.warning("⚠️ Trading API not available, skipping trading monitor")
            return
        
        logger.info(f"💰 Starting trading monitor for {tickers}")
        
        try:
            while self.running:
                for ticker in tickers:
                    # Get trading signal
                    signal = self.trading_api.get_sentiment_signal(ticker)
                    
                    if "error" not in signal:
                        logger.info(f"📈 Trading signal for {ticker}: {signal.get('signal', 'HOLD')}")
                        
                        # Execute trade if signal is strong
                        if signal.get("signal") in ["BUY", "SELL"] and signal.get("confidence", 0) > 0.7:
                            trade_result = self.trading_api.execute_sentiment_trade(ticker)
                            logger.info(f"💼 Trade executed: {trade_result}")
                
                # Wait for next check
                await asyncio.sleep(interval_minutes * 60)
                
        except Exception as e:
            logger.error(f"❌ Error in trading monitor: {e}")
    
    async def train_models(self, tickers: List[str], days: int = 30) -> None:
        """Train predictive models for all tickers."""
        logger.info(f"🤖 Training models for {tickers}")
        
        try:
            for ticker in tickers:
                logger.info(f"Training sentiment model for {ticker}")
                sentiment_results = self.predictor.train_sentiment_model(ticker, days)
                logger.info(f"Sentiment model results for {ticker}: {sentiment_results}")
                
                logger.info(f"Training stock movement model for {ticker}")
                movement_results = self.predictor.train_stock_movement_model(ticker, days)
                logger.info(f"Stock movement model results for {ticker}: {movement_results}")
                
        except Exception as e:
            logger.error(f"❌ Error training models: {e}")
    
    async def run_all_services(self, tickers: List[str], interval_minutes: int = 15,
                              dashboard_port: int = 8000) -> None:
        """Run all services concurrently."""
        self.running = True
        
        # Create tasks for all services
        tasks = []
        
        # Scraping task
        scraping_task = asyncio.create_task(
            self.start_scraping(tickers, interval_minutes, duration_hours=24)
        )
        tasks.append(scraping_task)
        
        # Dashboard task
        dashboard_task = asyncio.create_task(
            self.start_dashboard(port=dashboard_port)
        )
        tasks.append(dashboard_task)
        
        # Notification task
        notification_task = asyncio.create_task(
            self.start_notifications(tickers, interval_minutes=5)
        )
        tasks.append(notification_task)
        
        # Trading monitor task
        if self.trading_api:
            trading_task = asyncio.create_task(
                self.start_trading_monitor(tickers, interval_minutes=30)
            )
            tasks.append(trading_task)
        
        # Model training task (run once at startup)
        training_task = asyncio.create_task(
            self.train_models(tickers, days=30)
        )
        tasks.append(training_task)
        
        # Store tasks for cleanup
        self.tasks = tasks
        
        logger.info(f"🚀 All services started. Monitoring {len(tickers)} tickers.")
        
        try:
            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal, shutting down...")
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Gracefully shutdown all services."""
        logger.info("🔄 Shutting down services...")
        
        self.running = False
        
        # Cancel all running tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close database connections
        if hasattr(self.db, 'close_connection'):
            self.db.close_connection()
        
        logger.info("✅ Shutdown complete")
    
    def get_status(self) -> Dict:
        """Get the current status of all components."""
        status = {
            "running": self.running,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": "connected" if self.db else "disconnected",
                "predictor": "initialized" if self.predictor else "not_initialized",
                "notification_system": "initialized" if self.notification_system else "not_initialized",
                "dashboard": "initialized" if self.dashboard else "not_initialized",
                "trading_api": "available" if self.trading_api else "not_available"
            },
            "models": self.predictor.get_model_performance() if self.predictor else {},
            "account_info": self.trading_api.get_account_info() if self.trading_api else {}
        }
        
        return status

def signal_handler(signum, frame):
    """Handle interrupt signals."""
    logger.info(f"🛑 Received signal {signum}, initiating shutdown...")
    sys.exit(0)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Social Media Sentiment Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--mode",
        choices=["scraping", "dashboard", "trading", "all"],
        default="all",
        help="Operation mode"
    )
    
    parser.add_argument(
        "--tickers",
        default="TSLA,SPY,QQQ",
        help="Comma-separated list of tickers to monitor"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=15,
        help="Scraping interval in minutes"
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        default=8,
        help="Duration to run in hours"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Dashboard port"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Dashboard host"
    )
    
    parser.add_argument(
        "--train-models",
        action="store_true",
        help="Train predictive models"
    )
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse tickers
    tickers = [ticker.strip().upper() for ticker in args.tickers.split(",")]
    
    # Create application
    app = SentimentAnalysisApp()
    
    async def run_app():
        """Run the application based on mode."""
        try:
            if args.mode == "scraping":
                await app.start_scraping(tickers, args.interval, args.duration)
            
            elif args.mode == "dashboard":
                await app.start_dashboard(args.host, args.port)
            
            elif args.mode == "trading":
                if app.trading_api:
                    await app.start_trading_monitor(tickers, args.interval)
                else:
                    logger.error("❌ Trading API not available")
                    sys.exit(1)
            
            elif args.mode == "all":
                # Train models if requested
                if args.train_models:
                    await app.train_models(tickers, days=30)
                
                # Run all services
                await app.run_all_services(tickers, args.interval, args.port)
            
        except Exception as e:
            logger.error(f"❌ Application error: {e}")
            sys.exit(1)
    
    # Run the application
    try:
        asyncio.run(run_app())
    except KeyboardInterrupt:
        logger.info("🛑 Application interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 