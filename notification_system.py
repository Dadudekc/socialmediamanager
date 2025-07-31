import os
import asyncio
import logging
import smtplib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import discord
from discord.ext import commands
import requests
from dataclasses import dataclass
from enum import Enum

from project_config import config
from db_handler import DatabaseHandler
from predictive_models import SentimentPredictor
from setup_logging import setup_logging

logger = setup_logging("notification_system", log_dir=config.LOG_DIR)

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

class NotificationSystem:
    """Handles sending notifications for significant sentiment changes."""
    
    def __init__(self):
        self.db = DatabaseHandler(logger)
        self.predictor = SentimentPredictor()
        self.thresholds = AlertThreshold()
        
        # Initialize notification channels
        self.discord_bot = None
        self.email_config = self._load_email_config()
        self.webhook_urls = self._load_webhook_config()
        
        # Alert history to prevent spam
        self.alert_history = {}
        self.alert_cooldown = timedelta(minutes=15)
        
        logger.info("✅ Notification system initialized")
    
    def _load_email_config(self) -> Dict:
        """Load email configuration from environment."""
        return {
            "smtp_server": config.get_env("SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": config.get_env("SMTP_PORT", 587, int),
            "email_address": config.get_env("NOTIFICATION_EMAIL"),
            "email_password": config.get_env("NOTIFICATION_EMAIL_PASSWORD"),
            "recipients": config.get_env("NOTIFICATION_RECIPIENTS", "").split(",")
        }
    
    def _load_webhook_config(self) -> List[str]:
        """Load webhook URLs from environment."""
        webhook_urls = config.get_env("WEBHOOK_URLS", "")
        return [url.strip() for url in webhook_urls.split(",") if url.strip()]
    
    async def initialize_discord_bot(self):
        """Initialize Discord bot for notifications."""
        try:
            token = config.get_env("DISCORD_TOKEN")
            if not token:
                logger.warning("⚠️ Discord token not configured")
                return
            
            intents = discord.Intents.default()
            self.discord_bot = commands.Bot(command_prefix="!", intents=intents)
            
            @self.discord_bot.event
            async def on_ready():
                logger.info(f"✅ Discord bot logged in as {self.discord_bot.user}")
            
            # Start bot in background
            asyncio.create_task(self.discord_bot.start(token))
            
        except Exception as e:
            logger.error(f"❌ Error initializing Discord bot: {e}")
    
    def check_sentiment_alert(self, ticker: str, current_data: Dict, historical_data: List[Dict]) -> Optional[NotificationMessage]:
        """Check if sentiment change warrants an alert."""
        try:
            if not historical_data or len(historical_data) < 2:
                return None
            
            # Calculate sentiment change
            current_sentiment = current_data.get("sentiment_score", 0)
            historical_sentiment = historical_data[-2].get("sentiment_score", 0)
            sentiment_change = abs(current_sentiment - historical_sentiment)
            
            # Check volume spike
            current_volume = current_data.get("message_count", 0)
            avg_volume = sum(d.get("message_count", 0) for d in historical_data[-10:]) / 10
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Determine alert priority
            priority = "low"
            if sentiment_change > self.thresholds.sentiment_change_threshold * 2:
                priority = "critical"
            elif sentiment_change > self.thresholds.sentiment_change_threshold:
                priority = "high"
            elif volume_ratio > self.thresholds.volume_spike_threshold:
                priority = "medium"
            
            # Check if we should send alert
            if (sentiment_change > self.thresholds.sentiment_change_threshold or 
                volume_ratio > self.thresholds.volume_spike_threshold):
                
                # Check cooldown
                alert_key = f"{ticker}_{priority}"
                last_alert = self.alert_history.get(alert_key)
                if last_alert and datetime.now() - last_alert < self.alert_cooldown:
                    return None
                
                # Create notification message
                title = f"🚨 Sentiment Alert: {ticker}"
                content = self._format_sentiment_alert(ticker, current_data, historical_data)
                
                message = NotificationMessage(
                    title=title,
                    content=content,
                    priority=priority,
                    timestamp=datetime.now(),
                    data={
                        "ticker": ticker,
                        "sentiment_change": sentiment_change,
                        "volume_ratio": volume_ratio,
                        "current_sentiment": current_sentiment,
                        "historical_sentiment": historical_sentiment
                    },
                    notification_type=NotificationType.DISCORD
                )
                
                # Update alert history
                self.alert_history[alert_key] = datetime.now()
                
                return message
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error checking sentiment alert: {e}")
            return None
    
    def _format_sentiment_alert(self, ticker: str, current_data: Dict, historical_data: List[Dict]) -> str:
        """Format sentiment alert message."""
        current_sentiment = current_data.get("sentiment_score", 0)
        historical_sentiment = historical_data[-2].get("sentiment_score", 0) if len(historical_data) >= 2 else 0
        sentiment_change = current_sentiment - historical_sentiment
        
        current_volume = current_data.get("message_count", 0)
        avg_volume = sum(d.get("message_count", 0) for d in historical_data[-10:]) / 10
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Determine sentiment direction
        if sentiment_change > 0:
            direction = "📈 Bullish"
            emoji = "🚀"
        elif sentiment_change < 0:
            direction = "📉 Bearish"
            emoji = "📉"
        else:
            direction = "➡️ Neutral"
            emoji = "➡️"
        
        return f"""
{emoji} **{ticker} Sentiment Alert**

**Direction:** {direction}
**Sentiment Change:** {sentiment_change:.3f}
**Current Sentiment:** {current_sentiment:.3f}
**Volume Ratio:** {volume_ratio:.2f}x average

**Analysis:**
- Sentiment shifted from {historical_sentiment:.3f} to {current_sentiment:.3f}
- Message volume is {volume_ratio:.1f}x the 10-period average
- Confidence: {current_data.get('confidence', 0):.2f}

**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
    
    async def send_discord_notification(self, message: NotificationMessage) -> bool:
        """Send notification via Discord."""
        try:
            if not self.discord_bot:
                logger.warning("⚠️ Discord bot not initialized")
                return False
            
            channel_id = config.get_env("DISCORD_CHANNEL_ID", cast_type=int)
            if not channel_id:
                logger.warning("⚠️ Discord channel ID not configured")
                return False
            
            channel = self.discord_bot.get_channel(channel_id)
            if not channel:
                logger.error(f"❌ Could not find Discord channel {channel_id}")
                return False
            
            # Create embed
            embed = discord.Embed(
                title=message.title,
                description=message.content,
                color=self._get_priority_color(message.priority),
                timestamp=message.timestamp
            )
            
            embed.add_field(
                name="Priority",
                value=message.priority.upper(),
                inline=True
            )
            
            embed.add_field(
                name="Ticker",
                value=message.data.get("ticker", "Unknown"),
                inline=True
            )
            
            await channel.send(embed=embed)
            logger.info(f"✅ Discord notification sent: {message.title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending Discord notification: {e}")
            return False
    
    def send_email_notification(self, message: NotificationMessage) -> bool:
        """Send notification via email."""
        try:
            if not self.email_config.get("email_address") or not self.email_config.get("email_password"):
                logger.warning("⚠️ Email credentials not configured")
                return False
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.email_config["email_address"]
            msg['To'] = ", ".join(self.email_config["recipients"])
            msg['Subject'] = f"[{message.priority.upper()}] {message.title}"
            
            # Create HTML content
            html_content = f"""
            <html>
            <body>
                <h2>{message.title}</h2>
                <p><strong>Priority:</strong> {message.priority.upper()}</p>
                <p><strong>Time:</strong> {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <pre>{message.content}</pre>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"]) as server:
                server.starttls()
                server.login(self.email_config["email_address"], self.email_config["email_password"])
                server.send_message(msg)
            
            logger.info(f"✅ Email notification sent: {message.title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending email notification: {e}")
            return False
    
    async def send_webhook_notification(self, message: NotificationMessage) -> bool:
        """Send notification via webhook."""
        try:
            if not self.webhook_urls:
                logger.warning("⚠️ No webhook URLs configured")
                return False
            
            # Prepare webhook payload
            payload = {
                "text": message.title,
                "attachments": [{
                    "title": message.title,
                    "text": message.content,
                    "color": self._get_priority_color_hex(message.priority),
                    "fields": [
                        {
                            "title": "Priority",
                            "value": message.priority.upper(),
                            "short": True
                        },
                        {
                            "title": "Ticker",
                            "value": message.data.get("ticker", "Unknown"),
                            "short": True
                        }
                    ],
                    "ts": int(message.timestamp.timestamp())
                }]
            }
            
            # Send to all webhook URLs
            success_count = 0
            for webhook_url in self.webhook_urls:
                try:
                    response = requests.post(webhook_url, json=payload, timeout=10)
                    if response.status_code == 200:
                        success_count += 1
                    else:
                        logger.warning(f"⚠️ Webhook failed with status {response.status_code}")
                except Exception as e:
                    logger.error(f"❌ Error sending webhook to {webhook_url}: {e}")
            
            if success_count > 0:
                logger.info(f"✅ Webhook notifications sent to {success_count}/{len(self.webhook_urls)} endpoints")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending webhook notification: {e}")
            return False
    
    def _get_priority_color(self, priority: str) -> int:
        """Get Discord embed color for priority."""
        color_map = {
            "low": 0x00ff00,      # Green
            "medium": 0xffff00,   # Yellow
            "high": 0xff8800,     # Orange
            "critical": 0xff0000   # Red
        }
        return color_map.get(priority, 0x808080)
    
    def _get_priority_color_hex(self, priority: str) -> str:
        """Get hex color for webhook."""
        color_map = {
            "low": "#00ff00",
            "medium": "#ffff00",
            "high": "#ff8800",
            "critical": "#ff0000"
        }
        return color_map.get(priority, "#808080")
    
    async def send_notification(self, message: NotificationMessage) -> Dict:
        """Send notification through all configured channels."""
        results = {
            "discord": False,
            "email": False,
            "webhook": False
        }
        
        try:
            # Send Discord notification
            if message.notification_type == NotificationType.DISCORD:
                results["discord"] = await self.send_discord_notification(message)
            
            # Send email notification
            if self.email_config.get("email_address"):
                results["email"] = self.send_email_notification(message)
            
            # Send webhook notification
            if self.webhook_urls:
                results["webhook"] = await self.send_webhook_notification(message)
            
            logger.info(f"✅ Notification sent: {results}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error sending notification: {e}")
            return {"error": str(e)}
    
    async def monitor_sentiment_changes(self, tickers: List[str], interval_minutes: int = 5):
        """Continuously monitor sentiment changes and send alerts."""
        logger.info(f"🔍 Starting sentiment monitoring for {tickers}")
        
        while True:
            try:
                for ticker in tickers:
                    # Get recent sentiment data
                    data = self.db.fetch_sentiment(ticker, limit=100)
                    if not data or len(data) < 2:
                        continue
                    
                    # Convert to list of dicts
                    historical_data = []
                    for row in data:
                        historical_data.append({
                            "sentiment_score": row[5],  # vader score
                            "message_count": 1,  # Simplified
                            "confidence": 0.8,  # Placeholder
                            "timestamp": row[2]
                        })
                    
                    # Check for alerts
                    current_data = historical_data[-1]
                    alert_message = self.check_sentiment_alert(ticker, current_data, historical_data)
                    
                    if alert_message:
                        await self.send_notification(alert_message)
                
                # Wait for next check
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"❌ Error in sentiment monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    # Example usage
    async def main():
        notification_system = NotificationSystem()
        
        # Initialize Discord bot
        await notification_system.initialize_discord_bot()
        
        # Start monitoring
        await notification_system.monitor_sentiment_changes(["TSLA", "SPY", "QQQ"])
    
    # Run the monitoring
    asyncio.run(main()) 