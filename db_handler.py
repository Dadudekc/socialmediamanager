import mysql.connector
import logging
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from project_config import config

 

class DatabaseHandler:
    """
    Handles database operations for storing sentiment data and raw posts.
    Supports MySQL as the backend.
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.db_type = config.get_env("DB_TYPE", "mysql").lower()

        if self.db_type != "mysql":
            raise ValueError("❌ Unsupported database type. Only MySQL is supported.")

        self.logger.info(f"✅ Initializing DatabaseHandler for {self.db_type}")
        self.conn = self.get_connection()
        self.cursor = self.conn.cursor()
        # Expose table initialization publicly:
        self.initialize_table()

    def get_connection(self):
        """Establishes a new database connection."""
        try:
            conn = mysql.connector.connect(
                database=config.get_env("MYSQL_DB_NAME"),
                user=config.get_env("MYSQL_DB_USER"),
                password=config.get_env("MYSQL_DB_PASSWORD"),
                host=config.get_env("MYSQL_DB_HOST", "localhost"),
                port=config.get_env("MYSQL_DB_PORT", 3306, int)
            )
            self.logger.info("✅ Database connection established.")
            return conn
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to MySQL: {e}")
            raise

    def close_connection(self):
        """Closes the database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.logger.info("✅ Database connection closed.")

    def initialize_table(self):
        """Ensures database tables exist."""
        sentiment_query = """
        CREATE TABLE IF NOT EXISTS SentimentData (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ticker VARCHAR(10),
            timestamp DATETIME,
            content TEXT,
            textblob_sentiment FLOAT,
            vader_sentiment FLOAT,
            sentiment_category VARCHAR(20)
        );
        """

        posts_query = """
        CREATE TABLE IF NOT EXISTS RawPosts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            platform VARCHAR(20),
            text TEXT,
            timestamp DATETIME
        );
        """

        try:
            self.cursor.execute(sentiment_query)
            self.cursor.execute(posts_query)
            self.conn.commit()
            self.logger.info("✅ SentimentData table initialized successfully.")
            self.logger.info("✅ RawPosts table initialized successfully.")
        except Exception as e:
            self.logger.error(f"❌ Error initializing tables: {e}")
            raise

    def bulk_insert_sentiment(self, data):
        """Inserts multiple sentiment records in a batch transaction."""
        query = """
        INSERT INTO SentimentData (ticker, timestamp, content, textblob_sentiment, vader_sentiment, sentiment_category)
        VALUES (%s, %s, %s, %s, %s, %s);
        """
        try:
            self.cursor.executemany(query, data)
            self.conn.commit()
            self.logger.info(f"✅ Bulk insert successful. Inserted {len(data)} records.")
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"⚠️ Database bulk insert failed: {e}")
            raise

    def bulk_insert_posts(self, data):
        """Inserts multiple raw social media posts."""
        query = """
        INSERT INTO RawPosts (platform, text, timestamp)
        VALUES (%s, %s, %s);
        """
        try:
            self.cursor.executemany(query, data)
            self.conn.commit()
            self.logger.info(f"✅ Inserted {len(data)} raw posts.")
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"⚠️ Database post insert failed: {e}")
            raise

    def save_sentiment(self, ticker, timestamp, content, textblob_sentiment, vader_sentiment, sentiment_category):
        """
        Saves a single sentiment data point into the database.
        """
        query = """
        INSERT INTO SentimentData (ticker, timestamp, content, textblob_sentiment, vader_sentiment, sentiment_category)
        VALUES (%s, %s, %s, %s, %s, %s);
        """
        try:
            self.cursor.execute(query, (ticker, timestamp, content, textblob_sentiment, vader_sentiment, sentiment_category))
            self.conn.commit()
            self.logger.info(f"✅ Saved sentiment data for {ticker}.")
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"⚠️ Error saving sentiment data: {e}")
            raise

    def save_post(self, platform, text, timestamp):
        """Saves a single raw post."""
        query = """
        INSERT INTO RawPosts (platform, text, timestamp)
        VALUES (%s, %s, %s);
        """
        try:
            self.cursor.execute(query, (platform, text, timestamp))
            self.conn.commit()
            self.logger.info("✅ Saved post from %s", platform)
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"⚠️ Error saving post: {e}")
            raise

    def fetch_sentiment(self, ticker, limit=10):
        """
        Fetches the most recent sentiment data for a given ticker.
        :param ticker: Stock ticker symbol.
        :param limit: Maximum number of records to retrieve.
        :return: List of tuples containing sentiment data.
        """
        query = """
        SELECT id, ticker, timestamp, content, textblob_sentiment, vader_sentiment, sentiment_category
        FROM SentimentData WHERE ticker = %s ORDER BY timestamp DESC LIMIT %s;
        """
        try:
            self.cursor.execute(query, (ticker, limit))
            rows = self.cursor.fetchall()
            return rows
        except Exception as e:
            self.logger.error(f"⚠️ Error fetching sentiment data: {e}")
            return []

    def get_available_tickers(self):
        """Get list of available tickers in the database."""
        query = """
        SELECT DISTINCT ticker FROM SentimentData ORDER BY ticker;
        """
        try:
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            return [row[0] for row in rows]
        except Exception as e:
            self.logger.error(f"⚠️ Error fetching available tickers: {e}")
            return []

    def get_summary_stats(self):
        """Get summary statistics for the dashboard."""
        try:
            # Total records
            self.cursor.execute("SELECT COUNT(*) FROM SentimentData")
            total_records = self.cursor.fetchone()[0]
            
            # Records by sentiment
            self.cursor.execute("""
                SELECT sentiment_category, COUNT(*) 
                FROM SentimentData 
                GROUP BY sentiment_category
            """)
            sentiment_counts = dict(self.cursor.fetchall())
            
            # Recent activity (last 24 hours)
            self.cursor.execute("""
                SELECT COUNT(*) 
                FROM SentimentData 
                WHERE timestamp >= NOW() - INTERVAL 24 HOUR
            """)
            recent_activity = self.cursor.fetchone()[0]
            
            return {
                "total_records": total_records,
                "sentiment_distribution": sentiment_counts,
                "recent_activity_24h": recent_activity,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"⚠️ Error fetching summary stats: {e}")
            return {"error": str(e)}
