# Product Requirements Document (PRD)

## Overview
This project provides tools to collect and analyze stock market sentiment from social media platforms. It began with Stocktwits scraping and sentiment analysis. The long‑term goal is to deliver actionable insights to traders and investors through automated collection, analysis, and visualization of crowd sentiment.

## Goals
- Gather messages from multiple platforms (Stocktwits, Reddit, Twitter, Discord).
- Perform real‑time sentiment analysis using NLP libraries.
- Store data for historical analysis and predictive modeling.
- Present results in a dashboard and send alerts for notable sentiment shifts.
- Integrate with trading APIs for optional automated trading actions.

## Non‑Goals
- Provide investment advice directly.
- Guarantee the profitability of trading strategies.

## Features
1. **Multi‑Platform Scraping**
   - Unified crawler for Stocktwits, Reddit, Twitter, and Discord.
   - Cookie management and login automation for platforms requiring authentication.
2. **Real‑Time Sentiment Tracking**
   - Continuous streaming and sentiment evaluation of new messages.
   - Spam detection and deduplication to maintain data quality.
3. **Data Storage and Backfill**
   - Store scraped data in CSV/JSON and an SQL database.
   - Optional backfill of historical messages for deeper analysis.
4. **AI‑Powered Predictions**
   - Use stored historical data to train models that forecast sentiment trends and possible stock movements.
5. **Dashboard & Visualization**
   - Web dashboard showing sentiment trends over time with interactive charts.
   - Exportable reports for individual tickers.
6. **Notifications**
   - Send alerts via Discord, email, or mobile push when significant sentiment changes occur.
7. **Trading API Integration**
   - Optional module connecting to brokers like Alpaca to execute trades based on sentiment signals.
8. **Cloud Deployment**
   - Deployable container images and infrastructure scripts for continuous operation in the cloud.

## Success Metrics
- Number of supported platforms and tickers actively tracked.
- Latency from message creation to sentiment update in the dashboard.
- Prediction accuracy over historical benchmarks.
- User engagement with the dashboard and notification features.

## Timeline
- **Phase 1**: Establish basic scraping and sentiment analysis for Stocktwits (complete).
- **Phase 2**: Add additional platforms and real‑time streaming support.
- **Phase 3**: Build dashboard, notifications, and predictive models.
- **Phase 4**: Integrate trading API and finalize cloud deployment.

