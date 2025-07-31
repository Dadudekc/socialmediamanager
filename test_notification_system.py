#!/usr/bin/env python3
"""
Simplified notification system for testing without database dependencies.
"""

import os
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from setup_logging import setup_logging

logger = setup_logging("test_notification_system", log_dir="./logs")

class NotificationType(Enum):
    DISCORD = "discord"
    EMAIL = "email"
    PUSH = "push"
    WEBHOOK = "webhook"

@dataclass
class AlertThreshold:
    """Configuration for alert thresholds."""
    sentiment_change_threshold: float = 0.3
    volume_spike_threshold: float = 2.0
    confidence_threshold: float = 0.7
    time_window_hours: int = 1

@dataclass
class NotificationMessage:
    """Represents a notification message."""
    title: str
    content: str
    priority: str  # "low", "medium", "high", "critical"
    timestamp: datetime
    data: Dict
    notification_type: NotificationType

class TestNotificationSystem:
    """Simplified notification system for testing without database dependencies."""
    
    def __init__(self):
        self.thresholds = AlertThreshold()
        
        # Alert history to prevent spam
        self.alert_history = {}
        self.alert_cooldown = timedelta(minutes=15)
        
        logger.info("✅ TestNotificationSystem initialized")
    
    def check_sentiment_alert(self, ticker: str, current_data: Dict, historical_data: List[Dict]) -> Optional[NotificationMessage]:
        """Check if sentiment change warrants an alert."""
        try:
            if not historical_data:
                return None
            
            # Calculate sentiment change
            current_sentiment = current_data.get('sentiment', 0)
            historical_sentiment = sum(d.get('sentiment', 0) for d in historical_data) / len(historical_data)
            sentiment_change = abs(current_sentiment - historical_sentiment)
            
            # Check if change exceeds threshold
            if sentiment_change > self.thresholds.sentiment_change_threshold:
                # Check cooldown
                alert_key = f"{ticker}_sentiment"
                last_alert = self.alert_history.get(alert_key)
                
                if not last_alert or (datetime.now() - last_alert) > self.alert_cooldown:
                    self.alert_history[alert_key] = datetime.now()
                    
                    return NotificationMessage(
                        title=f"Sentiment Alert: {ticker}",
                        content=self._format_sentiment_alert(ticker, current_data, historical_data),
                        priority="medium" if sentiment_change < 0.5 else "high",
                        timestamp=datetime.now(),
                        data={
                            'ticker': ticker,
                            'current_sentiment': current_sentiment,
                            'historical_sentiment': historical_sentiment,
                            'change': sentiment_change
                        },
                        notification_type=NotificationType.WEBHOOK
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error checking sentiment alert: {e}")
            return None
    
    def _format_sentiment_alert(self, ticker: str, current_data: Dict, historical_data: List[Dict]) -> str:
        """Format sentiment alert message."""
        current_sentiment = current_data.get('sentiment', 0)
        historical_sentiment = sum(d.get('sentiment', 0) for d in historical_data) / len(historical_data)
        change = current_sentiment - historical_sentiment
        
        direction = "📈 Bullish" if change > 0 else "📉 Bearish"
        magnitude = "significant" if abs(change) > 0.5 else "moderate"
        
        return f"""
🚨 **Sentiment Alert for {ticker}**
{direction} shift detected!

**Current Sentiment:** {current_sentiment:.3f}
**Historical Average:** {historical_sentiment:.3f}
**Change:** {change:+.3f} ({magnitude})

**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
    
    async def send_webhook_notification(self, message: NotificationMessage) -> bool:
        """Send notification via webhook (simulated)."""
        try:
            # Simulate webhook call
            webhook_data = {
                "title": message.title,
                "content": message.content,
                "priority": message.priority,
                "timestamp": message.timestamp.isoformat(),
                "data": message.data
            }
            
            logger.info(f"📡 Webhook notification sent: {message.title}")
            logger.info(f"📝 Content: {message.content[:100]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending webhook notification: {e}")
            return False
    
    async def send_notification(self, message: NotificationMessage) -> Dict:
        """Send notification through appropriate channels."""
        results = {
            'success': False,
            'channels': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Send via webhook (simulated)
            if message.notification_type == NotificationType.WEBHOOK:
                success = await self.send_webhook_notification(message)
                results['channels']['webhook'] = success
            
            # Log the notification
            logger.info(f"📢 Notification sent: {message.title}")
            logger.info(f"📊 Priority: {message.priority}")
            
            results['success'] = any(results['channels'].values())
            
        except Exception as e:
            logger.error(f"❌ Error sending notification: {e}")
            results['error'] = str(e)
        
        return results
    
    async def monitor_sentiment_changes(self, tickers: List[str], interval_minutes: int = 5):
        """Monitor sentiment changes for given tickers."""
        logger.info(f"🔔 Starting sentiment monitoring for {tickers}")
        
        while True:
            try:
                for ticker in tickers:
                    # Generate sample data for testing
                    current_data = {
                        'sentiment': 0.8,  # Sample bullish sentiment
                        'volume': 1000,
                        'timestamp': datetime.now()
                    }
                    
                    # Generate historical data
                    historical_data = [
                        {'sentiment': 0.2, 'volume': 800, 'timestamp': datetime.now() - timedelta(hours=1)},
                        {'sentiment': 0.3, 'volume': 900, 'timestamp': datetime.now() - timedelta(hours=2)},
                        {'sentiment': 0.1, 'volume': 700, 'timestamp': datetime.now() - timedelta(hours=3)}
                    ]
                    
                    # Check for alerts
                    alert = self.check_sentiment_alert(ticker, current_data, historical_data)
                    
                    if alert:
                        logger.info(f"🚨 Alert triggered for {ticker}")
                        result = await self.send_notification(alert)
                        logger.info(f"📤 Alert sent: {result}")
                    else:
                        logger.debug(f"✅ No alert for {ticker}")
                
                # Wait for next check
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"❌ Error in sentiment monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

async def main():
    """Test the notification system."""
    notification_system = TestNotificationSystem()
    
    # Test alert generation
    current_data = {'sentiment': 0.8, 'volume': 1000, 'timestamp': datetime.now()}
    historical_data = [
        {'sentiment': 0.2, 'volume': 800, 'timestamp': datetime.now() - timedelta(hours=1)},
        {'sentiment': 0.3, 'volume': 900, 'timestamp': datetime.now() - timedelta(hours=2)}
    ]
    
    alert = notification_system.check_sentiment_alert("TSLA", current_data, historical_data)
    if alert:
        print(f"Alert generated: {alert.title}")
        result = await notification_system.send_notification(alert)
        print(f"Notification result: {result}")
    
    # Test monitoring
    await notification_system.monitor_sentiment_changes(["TSLA", "SPY"], interval_minutes=1)

if __name__ == "__main__":
    asyncio.run(main()) 