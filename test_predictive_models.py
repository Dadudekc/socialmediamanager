#!/usr/bin/env python3
"""
Simplified predictive models for testing without database dependencies.
"""

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

from setup_logging import setup_logging

logger = setup_logging("test_predictive_models", log_dir="./logs")

class TestSentimentPredictor:
    """Simplified predictive models for testing without database dependencies."""
    
    def __init__(self):
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
        # Model storage
        self.sentiment_model = None
        self.stock_movement_model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # Load existing models if available
        self.load_models()
        
        logger.info("✅ TestSentimentPredictor initialized")
    
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
    
    def generate_sample_data(self, ticker: str, days: int = 30) -> pd.DataFrame:
        """Generate sample data for testing."""
        logger.info(f"📊 Generating sample data for {ticker}")
        
        # Generate sample timestamps
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        timestamps = pd.date_range(start=start_date, end=end_date, freq='H')
        
        # Generate sample sentiment data
        np.random.seed(42)  # For reproducible results
        n_samples = len(timestamps)
        
        data = {
            'timestamp': timestamps,
            'ticker': [ticker] * n_samples,
            'textblob': np.random.uniform(-1, 1, n_samples),
            'vader': np.random.uniform(-1, 1, n_samples),
            'category': np.random.choice(['Bullish', 'Neutral', 'Bearish'], n_samples),
            'content': [f"Sample post about {ticker} #{i}" for i in range(n_samples)]
        }
        
        df = pd.DataFrame(data)
        logger.info(f"✅ Generated {len(df)} sample records")
        return df
    
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
        df['message_count_1h'] = df.groupby(df['timestamp'].dt.floor('H')).transform('count')['ticker']
        df['message_count_4h'] = df.groupby(df['timestamp'].dt.floor('4H')).transform('count')['ticker']
        
        # Sentiment score features
        df['vader_ma_1h'] = df['vader'].rolling(window=60, min_periods=1).mean()
        df['textblob_ma_1h'] = df['textblob'].rolling(window=60, min_periods=1).mean()
        
        # Fill NaN values
        df = df.fillna(0)
        
        return df
    
    def train_sentiment_model(self, ticker: str, days: int = 30) -> Dict:
        """Train sentiment prediction model using sample data."""
        logger.info(f"🤖 Training sentiment model for {ticker}")
        
        try:
            # Generate sample data
            data = self.generate_sample_data(ticker, days)
            df = self.prepare_features(data)
            
            # Prepare features and target
            feature_columns = [
                'hour', 'day_of_week', 'is_weekend', 'sentiment_numeric',
                'sentiment_ma_1h', 'sentiment_ma_4h', 'sentiment_std_1h',
                'message_count_1h', 'message_count_4h', 'vader_ma_1h', 'textblob_ma_1h'
            ]
            
            X = df[feature_columns].values
            y = df['sentiment_numeric'].values
            
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
            
            results = {
                'accuracy': accuracy,
                'model_type': 'RandomForest',
                'features_used': len(feature_columns),
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
            logger.info(f"✅ Sentiment model trained successfully. Accuracy: {accuracy:.3f}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error training sentiment model: {e}")
            return {'error': str(e)}
    
    def train_stock_movement_model(self, ticker: str, days: int = 30) -> Dict:
        """Train stock movement prediction model using sample data."""
        logger.info(f"🤖 Training stock movement model for {ticker}")
        
        try:
            # Generate sample data
            data = self.generate_sample_data(ticker, days)
            df = self.prepare_features(data)
            
            # Simulate stock price movements based on sentiment
            df['price_change'] = df['sentiment_numeric'] * np.random.uniform(0.01, 0.05, len(df))
            df['price_direction'] = (df['price_change'] > 0).astype(int)
            
            # Prepare features and target
            feature_columns = [
                'hour', 'day_of_week', 'is_weekend', 'sentiment_numeric',
                'sentiment_ma_1h', 'sentiment_ma_4h', 'sentiment_std_1h',
                'message_count_1h', 'message_count_4h', 'vader_ma_1h', 'textblob_ma_1h'
            ]
            
            X = df[feature_columns].values
            y = df['price_direction'].values
            
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
            
            results = {
                'mse': mse,
                'model_type': 'GradientBoosting',
                'features_used': len(feature_columns),
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
            logger.info(f"✅ Stock movement model trained successfully. MSE: {mse:.4f}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error training stock movement model: {e}")
            return {'error': str(e)}
    
    def predict_sentiment_trend(self, ticker: str, hours_ahead: int = 1) -> Dict:
        """Predict sentiment trend for the next few hours."""
        if not self.sentiment_model:
            return {'error': 'No sentiment model available'}
        
        try:
            # Generate recent sample data
            recent_data = self.generate_sample_data(ticker, days=7)
            df = self.prepare_features(recent_data)
            
            # Use the most recent data point
            latest_features = df.iloc[-1:][[
                'hour', 'day_of_week', 'is_weekend', 'sentiment_numeric',
                'sentiment_ma_1h', 'sentiment_ma_4h', 'sentiment_std_1h',
                'message_count_1h', 'message_count_4h', 'vader_ma_1h', 'textblob_ma_1h'
            ]].values
            
            # Scale features
            latest_features_scaled = self.scaler.transform(latest_features)
            
            # Make prediction
            prediction = self.sentiment_model.predict(latest_features_scaled)[0]
            confidence = np.max(self.sentiment_model.predict_proba(latest_features_scaled))
            
            sentiment_map = {1: 'Bullish', 0: 'Neutral', -1: 'Bearish'}
            predicted_sentiment = sentiment_map.get(prediction, 'Neutral')
            
            return {
                'ticker': ticker,
                'predicted_sentiment': predicted_sentiment,
                'confidence': confidence,
                'hours_ahead': hours_ahead,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error predicting sentiment trend: {e}")
            return {'error': str(e)}
    
    def predict_stock_movement(self, ticker: str, hours_ahead: int = 1) -> Dict:
        """Predict stock movement for the next few hours."""
        if not self.stock_movement_model:
            return {'error': 'No stock movement model available'}
        
        try:
            # Generate recent sample data
            recent_data = self.generate_sample_data(ticker, days=7)
            df = self.prepare_features(recent_data)
            
            # Use the most recent data point
            latest_features = df.iloc[-1:][[
                'hour', 'day_of_week', 'is_weekend', 'sentiment_numeric',
                'sentiment_ma_1h', 'sentiment_ma_4h', 'sentiment_std_1h',
                'message_count_1h', 'message_count_4h', 'vader_ma_1h', 'textblob_ma_1h'
            ]].values
            
            # Scale features
            latest_features_scaled = self.scaler.transform(latest_features)
            
            # Make prediction
            prediction = self.stock_movement_model.predict(latest_features_scaled)[0]
            
            # Determine direction
            direction = 'UP' if prediction > 0.5 else 'DOWN'
            confidence = abs(prediction - 0.5) * 2  # Convert to 0-1 scale
            
            return {
                'ticker': ticker,
                'predicted_direction': direction,
                'confidence': confidence,
                'hours_ahead': hours_ahead,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error predicting stock movement: {e}")
            return {'error': str(e)}
    
    def get_model_performance(self) -> Dict:
        """Get performance metrics for all models."""
        performance = {
            'sentiment_model': {
                'available': self.sentiment_model is not None,
                'type': 'RandomForest' if self.sentiment_model else None
            },
            'stock_movement_model': {
                'available': self.stock_movement_model is not None,
                'type': 'GradientBoosting' if self.stock_movement_model else None
            },
            'last_updated': datetime.now().isoformat()
        }
        
        return performance

if __name__ == "__main__":
    # Test the predictor
    predictor = TestSentimentPredictor()
    
    # Train models
    sentiment_results = predictor.train_sentiment_model("TSLA", days=30)
    print(f"Sentiment model results: {sentiment_results}")
    
    movement_results = predictor.train_stock_movement_model("TSLA", days=30)
    print(f"Stock movement model results: {movement_results}")
    
    # Test predictions
    sentiment_prediction = predictor.predict_sentiment_trend("TSLA")
    print(f"Sentiment prediction: {sentiment_prediction}")
    
    movement_prediction = predictor.predict_stock_movement("TSLA")
    print(f"Stock movement prediction: {movement_prediction}")
    
    # Get performance
    performance = predictor.get_model_performance()
    print(f"Model performance: {performance}") 