import os
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error
from sklearn.linear_model import LinearRegression
from sklearn.svm import SVR
import joblib
import pickle
from pathlib import Path

from project_config import config
from db_handler import DatabaseHandler
from setup_logging import setup_logging

logger = setup_logging("predictive_models", log_dir=config.LOG_DIR)

class SentimentPredictor:
    """Predictive models for sentiment analysis and stock movement forecasting."""
    
    def __init__(self):
        self.db = DatabaseHandler(logger)
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
        # Model storage
        self.sentiment_model = None
        self.stock_movement_model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # Load existing models if available
        self.load_models()
    
    def load_models(self):
        """Load pre-trained models from disk."""
        try:
            if (self.models_dir / "sentiment_model.pkl").exists():
                self.sentiment_model = joblib.load(self.models_dir / "sentiment_model.pkl")
                logger.info("✅ Loaded sentiment prediction model")
            
            if (self.models_dir / "stock_movement_model.pkl").exists():
                self.stock_movement_model = joblib.load(self.models_dir / "stock_movement_model.pkl")
                logger.info("✅ Loaded stock movement prediction model")
            
            if (self.models_dir / "scaler.pkl").exists():
                self.scaler = joblib.load(self.models_dir / "scaler.pkl")
                logger.info("✅ Loaded feature scaler")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not load existing models: {e}")
    
    def save_models(self):
        """Save trained models to disk."""
        try:
            if self.sentiment_model:
                joblib.dump(self.sentiment_model, self.models_dir / "sentiment_model.pkl")
            
            if self.stock_movement_model:
                joblib.dump(self.stock_movement_model, self.models_dir / "stock_movement_model.pkl")
            
            joblib.dump(self.scaler, self.models_dir / "scaler.pkl")
            logger.info("✅ Models saved successfully")
            
        except Exception as e:
            logger.error(f"❌ Error saving models: {e}")
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for machine learning models."""
        df = data.copy()
        
        # Time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Sentiment features
        df['sentiment_numeric'] = df['category'].map({
            'Bullish': 1,
            'Neutral': 0,
            'Bearish': -1
        })
        
        # Rolling statistics
        df['sentiment_ma_1h'] = df['sentiment_numeric'].rolling(window=60, min_periods=1).mean()
        df['sentiment_ma_4h'] = df['sentiment_numeric'].rolling(window=240, min_periods=1).mean()
        df['sentiment_std_1h'] = df['sentiment_numeric'].rolling(window=60, min_periods=1).std()
        
        # Volume features
        df['message_count_1h'] = df.groupby(df['timestamp'].dt.floor('H')).transform('count')['id']
        df['message_count_4h'] = df.groupby(df['timestamp'].dt.floor('4H')).transform('count')['id']
        
        # Sentiment score features
        df['vader_ma_1h'] = df['vader'].rolling(window=60, min_periods=1).mean()
        df['textblob_ma_1h'] = df['textblob'].rolling(window=60, min_periods=1).mean()
        
        # Lag features
        df['sentiment_lag_1'] = df['sentiment_numeric'].shift(1)
        df['sentiment_lag_2'] = df['sentiment_numeric'].shift(2)
        df['vader_lag_1'] = df['vader'].shift(1)
        
        # Fill NaN values
        df = df.fillna(0)
        
        return df
    
    def train_sentiment_model(self, ticker: str, days: int = 30) -> Dict:
        """Train a model to predict sentiment trends."""
        try:
            # Get historical data
            data = self.db.fetch_sentiment(ticker, limit=10000)
            if not data:
                raise ValueError(f"No data available for ticker {ticker}")
            
            df = pd.DataFrame(data, columns=['id', 'ticker', 'timestamp', 'content', 'textblob', 'vader', 'category'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filter by time range
            cutoff_date = datetime.now() - timedelta(days=days)
            df = df[df['timestamp'] >= cutoff_date]
            
            # Prepare features
            df = self.prepare_features(df)
            
            # Create target variable (next hour's sentiment)
            df['target_sentiment'] = df['sentiment_numeric'].shift(-60).fillna(0)
            
            # Select features
            feature_columns = [
                'hour', 'day_of_week', 'is_weekend',
                'sentiment_numeric', 'sentiment_ma_1h', 'sentiment_ma_4h',
                'sentiment_std_1h', 'message_count_1h', 'message_count_4h',
                'vader_ma_1h', 'textblob_ma_1h', 'sentiment_lag_1', 'sentiment_lag_2',
                'vader_lag_1', 'vader', 'textblob'
            ]
            
            X = df[feature_columns].dropna()
            y = df.loc[X.index, 'target_sentiment']
            
            # Remove rows where target is 0 (no prediction)
            mask = y != 0
            X = X[mask]
            y = y[mask]
            
            if len(X) < 100:
                raise ValueError(f"Insufficient data for training: {len(X)} samples")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.sentiment_model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.sentiment_model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.sentiment_model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Save model
            self.save_models()
            
            logger.info(f"✅ Sentiment model trained with {len(X)} samples, accuracy: {accuracy:.3f}")
            
            return {
                "accuracy": accuracy,
                "samples": len(X),
                "feature_importance": dict(zip(feature_columns, self.sentiment_model.feature_importances_))
            }
            
        except Exception as e:
            logger.error(f"❌ Error training sentiment model: {e}")
            raise
    
    def train_stock_movement_model(self, ticker: str, days: int = 30) -> Dict:
        """Train a model to predict stock price movements based on sentiment."""
        try:
            # Get historical data
            data = self.db.fetch_sentiment(ticker, limit=10000)
            if not data:
                raise ValueError(f"No data available for ticker {ticker}")
            
            df = pd.DataFrame(data, columns=['id', 'ticker', 'timestamp', 'content', 'textblob', 'vader', 'category'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filter by time range
            cutoff_date = datetime.now() - timedelta(days=days)
            df = df[df['timestamp'] >= cutoff_date]
            
            # Prepare features
            df = self.prepare_features(df)
            
            # Create target variable (simplified - we'd need actual price data)
            # For now, we'll predict sentiment intensity
            df['target_movement'] = df['vader'].shift(-60).fillna(0)
            
            # Select features
            feature_columns = [
                'hour', 'day_of_week', 'is_weekend',
                'sentiment_numeric', 'sentiment_ma_1h', 'sentiment_ma_4h',
                'sentiment_std_1h', 'message_count_1h', 'message_count_4h',
                'vader_ma_1h', 'textblob_ma_1h', 'sentiment_lag_1', 'sentiment_lag_2',
                'vader_lag_1', 'vader', 'textblob'
            ]
            
            X = df[feature_columns].dropna()
            y = df.loc[X.index, 'target_movement']
            
            # Remove rows where target is 0
            mask = y != 0
            X = X[mask]
            y = y[mask]
            
            if len(X) < 100:
                raise ValueError(f"Insufficient data for training: {len(X)} samples")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.stock_movement_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            self.stock_movement_model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.stock_movement_model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            
            # Save model
            self.save_models()
            
            logger.info(f"✅ Stock movement model trained with {len(X)} samples, MSE: {mse:.4f}")
            
            return {
                "mse": mse,
                "samples": len(X),
                "feature_importance": dict(zip(feature_columns, self.stock_movement_model.feature_importances_))
            }
            
        except Exception as e:
            logger.error(f"❌ Error training stock movement model: {e}")
            raise
    
    def predict_sentiment_trend(self, ticker: str, hours_ahead: int = 1) -> Dict:
        """Predict sentiment trend for the next few hours."""
        try:
            if not self.sentiment_model:
                raise ValueError("Sentiment model not trained. Run train_sentiment_model() first.")
            
            # Get recent data
            data = self.db.fetch_sentiment(ticker, limit=1000)
            if not data:
                return {"error": f"No data available for ticker {ticker}"}
            
            df = pd.DataFrame(data, columns=['id', 'ticker', 'timestamp', 'content', 'textblob', 'vader', 'category'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Prepare features
            df = self.prepare_features(df)
            
            # Get latest features
            latest_features = df.iloc[-1:][self.sentiment_model.feature_names_in_]
            latest_features_scaled = self.scaler.transform(latest_features)
            
            # Make prediction
            prediction = self.sentiment_model.predict(latest_features_scaled)[0]
            confidence = np.max(self.sentiment_model.predict_proba(latest_features_scaled))
            
            sentiment_map = {1: "Bullish", 0: "Neutral", -1: "Bearish"}
            predicted_sentiment = sentiment_map.get(prediction, "Neutral")
            
            return {
                "ticker": ticker,
                "predicted_sentiment": predicted_sentiment,
                "confidence": confidence,
                "hours_ahead": hours_ahead,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error predicting sentiment trend: {e}")
            return {"error": str(e)}
    
    def predict_stock_movement(self, ticker: str, hours_ahead: int = 1) -> Dict:
        """Predict stock movement based on sentiment."""
        try:
            if not self.stock_movement_model:
                raise ValueError("Stock movement model not trained. Run train_stock_movement_model() first.")
            
            # Get recent data
            data = self.db.fetch_sentiment(ticker, limit=1000)
            if not data:
                return {"error": f"No data available for ticker {ticker}"}
            
            df = pd.DataFrame(data, columns=['id', 'ticker', 'timestamp', 'content', 'textblob', 'vader', 'category'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Prepare features
            df = self.prepare_features(df)
            
            # Get latest features
            latest_features = df.iloc[-1:][self.stock_movement_model.feature_names_in_]
            latest_features_scaled = self.scaler.transform(latest_features)
            
            # Make prediction
            predicted_movement = self.stock_movement_model.predict(latest_features_scaled)[0]
            
            # Interpret prediction
            if predicted_movement > 0.1:
                direction = "UP"
                strength = "Strong"
            elif predicted_movement > 0.05:
                direction = "UP"
                strength = "Moderate"
            elif predicted_movement < -0.1:
                direction = "DOWN"
                strength = "Strong"
            elif predicted_movement < -0.05:
                direction = "DOWN"
                strength = "Moderate"
            else:
                direction = "SIDEWAYS"
                strength = "Weak"
            
            return {
                "ticker": ticker,
                "predicted_direction": direction,
                "predicted_strength": strength,
                "predicted_value": predicted_movement,
                "hours_ahead": hours_ahead,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error predicting stock movement: {e}")
            return {"error": str(e)}
    
    def get_model_performance(self) -> Dict:
        """Get performance metrics for trained models."""
        try:
            performance = {
                "sentiment_model": {
                    "trained": self.sentiment_model is not None,
                    "last_updated": None
                },
                "stock_movement_model": {
                    "trained": self.stock_movement_model is not None,
                    "last_updated": None
                }
            }
            
            # Check model files for last updated time
            sentiment_model_path = self.models_dir / "sentiment_model.pkl"
            if sentiment_model_path.exists():
                performance["sentiment_model"]["last_updated"] = datetime.fromtimestamp(
                    sentiment_model_path.stat().st_mtime
                ).isoformat()
            
            stock_model_path = self.models_dir / "stock_movement_model.pkl"
            if stock_model_path.exists():
                performance["stock_movement_model"]["last_updated"] = datetime.fromtimestamp(
                    stock_model_path.stat().st_mtime
                ).isoformat()
            
            return performance
            
        except Exception as e:
            logger.error(f"❌ Error getting model performance: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    # Example usage
    predictor = SentimentPredictor()
    
    # Train models
    try:
        sentiment_results = predictor.train_sentiment_model("TSLA", days=30)
        print(f"Sentiment model results: {sentiment_results}")
        
        movement_results = predictor.train_stock_movement_model("TSLA", days=30)
        print(f"Stock movement model results: {movement_results}")
        
        # Make predictions
        sentiment_prediction = predictor.predict_sentiment_trend("TSLA")
        print(f"Sentiment prediction: {sentiment_prediction}")
        
        movement_prediction = predictor.predict_stock_movement("TSLA")
        print(f"Stock movement prediction: {movement_prediction}")
        
    except Exception as e:
        print(f"Error: {e}") 