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

## Disclaimers
- This open source project is provided **as is** for research and educational
  purposes. It does not offer financial or investment advice.
- Sentiment classifications rely on third‑party NLP libraries and may contain
  inaccuracies.
- The scraping utilities are intended only for publicly accessible data and
  must be used in accordance with each platform's terms of service.
- The maintainers are not affiliated with Stocktwits, Reddit, Twitter,
  Discord, or any brokerage platform.
- Do not scrape private data or bypass security mechanisms. Consult your local
  regulations before deploying the software in a production environment.
- The project investigates advanced web scraping techniques, including running
  Chrome in headless or "undetected" modes, to research automation
  capabilities. These approaches must comply with each platform's terms of
  service and should never be used to circumvent authentication or paywalls.

## Features
1. **Multi‑Platform Scraping**
   - Unified crawler for Stocktwits, Reddit, Twitter, and Discord.
   - Ephemeral Selenium sessions for Stocktwits to prevent stale logins.
   - Optionally run headless or "undetected" Chrome sessions when researching
     advanced scraping for social media management.
   - Asynchronous fetchers for Reddit, Twitter, and Discord.
   - Cookie management and login automation for platforms requiring authentication.
2. **Real‑Time Sentiment Tracking**
   - Continuous streaming and sentiment evaluation of new messages.
   - FinBERT combined with TextBlob & VADER for classification.
   - Spam detection and deduplication to maintain data quality.
   - Automated summaries posted to Discord.
3. **Data Storage and Backfill**
   - Store scraped data in CSV/JSON files and a MySQL database.
   - Optional backfill of historical messages for deeper analysis.
   - Configurable via environment variables with validation.
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

## Roadmap
- **Phase 1**: Establish basic scraping and sentiment analysis for Stocktwits (complete).
- **Phase 2**: Add asynchronous multi-platform streaming and Discord bot integration (in progress).
- **Phase 3**: Build dashboard, notifications, and predictive models.
- **Phase 4**: Integrate trading API and finalize cloud deployment.
- **Phase 5**: Ingest additional sources such as news feeds and podcasts; support multilingual sentiment.
- **Phase 6**: Release a public API with role-based access and advanced analytics.
- **Phase 7**: Explore automated trading strategies with portfolio management tools.

