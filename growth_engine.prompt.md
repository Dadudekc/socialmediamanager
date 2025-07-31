# Growth Engine Prompt

## Objective
Translate viral social media growth tactics (Instagram, TikTok, X/Twitter, LinkedIn, YouTube, etc.) into community-building app mechanics that drive user engagement and retention across platforms.

## Features

### 1. Micro-communities
- Allow creation and discovery of highly specific channels (e.g., "First-Time Texas Home Buyers" instead of generic "Real Estate").
- Build an onboarding **Niche Finder** that routes new users to aligned micro-topics.
- Support problem-solving content types such as Q&A threads, how‑tos, and quick wins.
- Enable top posts to be saved and shared across other groups to prioritize shareability over raw visibility.

### 2. Partner Growth Loops
- Let creators or moderators trade visibility through collab posts or pinned shoutouts between micro-communities.
- Provide a **Value Trade** board where users can exchange services (graphics, consults, code) for exposure.
- Auto-suggest relevant community collabs based on niche alignment and content themes.
- Include cross-platform collaborations by allowing users to link or tag profiles on other networks and share co-created content.

### 3. Smart Social Rituals
- Gamify thoughtful replies, reactions, and meaningful DMs with badges or XP.
- Reward "starter comments" and replies that spark discussion rather than simple likes.
- Surface highly engaged members in a weekly **Top Human** leaderboard.
- Give recognition for cross-posting community highlights to external networks.

### Bonus Mechanics
- **Weekly Content Builder:** create platform-specific templates (carousels for IG/LinkedIn, threads for X/Twitter, shorts for YouTube/TikTok/Reels) within the app.
- **Short-form Video Integration:** prompt users to share 2–3 quick video updates or stories per week for platforms like TikTok, Reels, or Shorts.
- **Smart Pinning and Cross-Posting:** recommend pinning high-engagement posts and provide one-click sharing to networks such as X, Facebook, or LinkedIn.

## Core Loop
1. **Niche Activation:** User joins a micro-topic group and solves problems or shares value.
2. **Collab Expansion:** User gains visibility through value trades, shout loops, or cross-platform collabs.
3. **Human Recognition:** Consistent, thoughtful engagement earns status, visibility, and growth.
4. **Content Sync:** Best posts are repurposed across external platforms in their optimal format.

## Implementation Notes
- Define data models and API endpoints for micro-communities, collabs, and engagement tracking.
- Schedule background tasks for weekly leaderboards, collab suggestions, and multi-platform content pushes.
- Expose hooks so external platforms can import content (threads, reels, carousels, shorts) directly from the app.
- Log user engagement metrics to feed gamification and recognition systems.
