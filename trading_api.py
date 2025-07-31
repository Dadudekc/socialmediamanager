import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST, TimeFrame
import yfinance as yf
import pandas as pd
from dataclasses import dataclass
from enum import Enum

from project_config import config
from db_handler import DatabaseHandler
from predictive_models import SentimentPredictor
from setup_logging import setup_logging

logger = setup_logging("trading_api", log_dir=config.LOG_DIR)

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

@dataclass
class TradingSignal:
    """Represents a trading signal based on sentiment analysis."""
    ticker: str
    signal: str  # "BUY", "SELL", "HOLD"
    confidence: float
    sentiment_score: float
    predicted_movement: float
    timestamp: datetime
    reasoning: str

class TradingStrategy:
    """Base class for trading strategies."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"TradingStrategy.{name}")
    
    def generate_signal(self, sentiment_data: Dict, market_data: Dict) -> TradingSignal:
        """Generate trading signal based on sentiment and market data."""
        raise NotImplementedError

class SentimentBasedStrategy(TradingStrategy):
    """Trading strategy based on sentiment analysis."""
    
    def __init__(self, threshold: float = 0.7):
        super().__init__("SentimentBased")
        self.threshold = threshold
    
    def generate_signal(self, sentiment_data: Dict, market_data: Dict) -> TradingSignal:
        """Generate signal based on sentiment analysis."""
        ticker = sentiment_data.get("ticker", "UNKNOWN")
        sentiment_score = sentiment_data.get("sentiment_score", 0)
        confidence = sentiment_data.get("confidence", 0)
        predicted_movement = sentiment_data.get("predicted_movement", 0)
        
        # Simple strategy: buy on strong bullish sentiment, sell on strong bearish
        if sentiment_score > self.threshold and confidence > 0.6:
            signal = "BUY"
            reasoning = f"Strong bullish sentiment ({sentiment_score:.2f}) with high confidence ({confidence:.2f})"
        elif sentiment_score < -self.threshold and confidence > 0.6:
            signal = "SELL"
            reasoning = f"Strong bearish sentiment ({sentiment_score:.2f}) with high confidence ({confidence:.2f})"
        else:
            signal = "HOLD"
            reasoning = f"Neutral sentiment ({sentiment_score:.2f}) or low confidence ({confidence:.2f})"
        
        return TradingSignal(
            ticker=ticker,
            signal=signal,
            confidence=confidence,
            sentiment_score=sentiment_score,
            predicted_movement=predicted_movement,
            timestamp=datetime.now(),
            reasoning=reasoning
        )

class TradingAPI:
    """Handles trading operations through Alpaca API."""
    
    def __init__(self, paper_trading: bool = True):
        self.paper_trading = paper_trading
        self.api_key = config.get_env("ALPACA_API_KEY")
        self.secret_key = config.get_env("ALPACA_SECRET_KEY")
        
        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca API credentials not configured")
        
        # Initialize Alpaca API
        self.api = tradeapi.REST(
            self.api_key,
            self.secret_key,
            'https://paper-api.alpaca.markets' if paper_trading else 'https://api.alpaca.markets',
            api_version='v2'
        )
        
        self.db = DatabaseHandler(logger)
        self.predictor = SentimentPredictor()
        self.strategies = {
            "sentiment": SentimentBasedStrategy()
        }
        
        logger.info(f"✅ Trading API initialized (Paper Trading: {paper_trading})")
    
    def get_account_info(self) -> Dict:
        """Get account information."""
        try:
            account = self.api.get_account()
            return {
                "account_id": account.id,
                "status": account.status,
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "buying_power": float(account.buying_power),
                "equity": float(account.equity),
                "daytrade_count": account.daytrade_count
            }
        except Exception as e:
            logger.error(f"❌ Error getting account info: {e}")
            return {"error": str(e)}
    
    def get_positions(self) -> List[Dict]:
        """Get current positions."""
        try:
            positions = self.api.list_positions()
            return [
                {
                    "symbol": pos.symbol,
                    "quantity": int(pos.qty),
                    "market_value": float(pos.market_value),
                    "unrealized_pl": float(pos.unrealized_pl),
                    "side": pos.side
                }
                for pos in positions
            ]
        except Exception as e:
            logger.error(f"❌ Error getting positions: {e}")
            return []
    
    def get_market_data(self, ticker: str, days: int = 5) -> Dict:
        """Get market data for a ticker."""
        try:
            # Get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            bars = self.api.get_bars(
                ticker,
                TimeFrame.Day,
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d')
            )
            
            if not bars:
                return {"error": f"No market data available for {ticker}"}
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'timestamp': bar.t,
                'open': bar.o,
                'high': bar.h,
                'low': bar.l,
                'close': bar.c,
                'volume': bar.v
            } for bar in bars])
            
            # Calculate technical indicators
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['rsi'] = self.calculate_rsi(df['close'])
            
            latest = df.iloc[-1] if not df.empty else None
            
            return {
                "ticker": ticker,
                "current_price": float(latest['close']) if latest is not None else None,
                "volume": int(latest['volume']) if latest is not None else None,
                "sma_20": float(latest['sma_20']) if latest is not None else None,
                "rsi": float(latest['rsi']) if latest is not None else None,
                "historical_data": df.to_dict('records')
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting market data for {ticker}: {e}")
            return {"error": str(e)}
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI technical indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def place_order(self, ticker: str, quantity: int, side: OrderSide, 
                   order_type: OrderType = OrderType.MARKET, 
                   limit_price: Optional[float] = None) -> Dict:
        """Place a trading order."""
        try:
            order_params = {
                "symbol": ticker,
                "qty": quantity,
                "side": side.value,
                "type": order_type.value,
                "time_in_force": "day"
            }
            
            if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and limit_price:
                order_params["limit_price"] = limit_price
            
            if order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
                # For stop orders, we'd need a stop price
                # This is simplified for now
                pass
            
            order = self.api.submit_order(**order_params)
            
            logger.info(f"✅ Order placed: {side.value} {quantity} {ticker}")
            
            return {
                "order_id": order.id,
                "status": order.status,
                "symbol": order.symbol,
                "quantity": order.qty,
                "side": order.side,
                "type": order.type,
                "filled_at": order.filled_at,
                "filled_avg_price": order.filled_avg_price
            }
            
        except Exception as e:
            logger.error(f"❌ Error placing order: {e}")
            return {"error": str(e)}
    
    def get_sentiment_signal(self, ticker: str) -> Dict:
        """Get sentiment-based trading signal."""
        try:
            # Get sentiment prediction
            sentiment_prediction = self.predictor.predict_sentiment_trend(ticker)
            movement_prediction = self.predictor.predict_stock_movement(ticker)
            
            if "error" in sentiment_prediction:
                return sentiment_prediction
            
            # Get market data
            market_data = self.get_market_data(ticker)
            
            # Generate trading signal
            strategy = self.strategies["sentiment"]
            signal = strategy.generate_signal(sentiment_prediction, market_data)
            
            return {
                "ticker": ticker,
                "signal": signal.signal,
                "confidence": signal.confidence,
                "sentiment_score": signal.sentiment_score,
                "predicted_movement": signal.predicted_movement,
                "reasoning": signal.reasoning,
                "timestamp": signal.timestamp.isoformat(),
                "market_data": market_data
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting sentiment signal: {e}")
            return {"error": str(e)}
    
    def execute_sentiment_trade(self, ticker: str, max_position_value: float = 1000.0) -> Dict:
        """Execute a trade based on sentiment analysis."""
        try:
            # Get signal
            signal_data = self.get_sentiment_signal(ticker)
            
            if "error" in signal_data:
                return signal_data
            
            signal = signal_data["signal"]
            current_price = signal_data.get("market_data", {}).get("current_price")
            
            if not current_price:
                return {"error": "No current price available"}
            
            # Calculate position size
            max_shares = int(max_position_value / current_price)
            
            if signal == "BUY":
                # Check if we already have a position
                positions = self.get_positions()
                existing_position = next((p for p in positions if p["symbol"] == ticker), None)
                
                if existing_position and existing_position["quantity"] > 0:
                    return {"message": f"Already have long position in {ticker}"}
                
                # Place buy order
                order_result = self.place_order(ticker, max_shares, OrderSide.BUY)
                
            elif signal == "SELL":
                # Check if we have a position to sell
                positions = self.get_positions()
                existing_position = next((p for p in positions if p["symbol"] == ticker), None)
                
                if not existing_position or existing_position["quantity"] <= 0:
                    return {"message": f"No position to sell in {ticker}"}
                
                # Place sell order
                order_result = self.place_order(ticker, abs(existing_position["quantity"]), OrderSide.SELL)
                
            else:  # HOLD
                return {"message": f"Holding {ticker} - no action taken"}
            
            return {
                "action": signal,
                "ticker": ticker,
                "order": order_result,
                "signal_data": signal_data
            }
            
        except Exception as e:
            logger.error(f"❌ Error executing sentiment trade: {e}")
            return {"error": str(e)}
    
    def get_trading_history(self, days: int = 30) -> List[Dict]:
        """Get trading history."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            orders = self.api.list_orders(
                status='all',
                after=start_date.strftime('%Y-%m-%d'),
                until=end_date.strftime('%Y-%m-%d')
            )
            
            return [
                {
                    "order_id": order.id,
                    "symbol": order.symbol,
                    "quantity": order.qty,
                    "side": order.side,
                    "type": order.type,
                    "status": order.status,
                    "filled_at": order.filled_at,
                    "filled_avg_price": order.filled_avg_price,
                    "created_at": order.created_at
                }
                for order in orders
            ]
            
        except Exception as e:
            logger.error(f"❌ Error getting trading history: {e}")
            return []
    
    def get_performance_metrics(self) -> Dict:
        """Get trading performance metrics."""
        try:
            account = self.api.get_account()
            positions = self.get_positions()
            
            total_pnl = sum(float(pos["unrealized_pl"]) for pos in positions)
            total_value = sum(float(pos["market_value"]) for pos in positions)
            
            return {
                "total_pnl": total_pnl,
                "total_portfolio_value": float(account.portfolio_value),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
                "positions_count": len(positions),
                "total_positions_value": total_value,
                "account_status": account.status
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting performance metrics: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    # Example usage
    try:
        trading_api = TradingAPI(paper_trading=True)
        
        # Get account info
        account_info = trading_api.get_account_info()
        print(f"Account Info: {account_info}")
        
        # Get sentiment signal
        signal = trading_api.get_sentiment_signal("TSLA")
        print(f"Sentiment Signal: {signal}")
        
        # Execute trade (commented out for safety)
        # trade_result = trading_api.execute_sentiment_trade("TSLA")
        # print(f"Trade Result: {trade_result}")
        
    except Exception as e:
        print(f"Error: {e}") 