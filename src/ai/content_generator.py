#!/usr/bin/env python3
"""
AI Content Generator - Advanced content creation for the Ultimate Follow Builder.
Generates captions, hashtags, and viral content using AI models.
"""

import os
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import random

class ContentType(Enum):
    """Types of content to generate."""
    CAPTION = "caption"
    HASHTAG = "hashtag"
    POST = "post"
    STORY = "story"
    REEL = "reel"
    THREAD = "thread"

class ToneType(Enum):
    """Content tone types."""
    MOTIVATIONAL = "motivational"
    EDUCATIONAL = "educational"
    FUNNY = "funny"
    INSPIRATIONAL = "inspirational"
    PROFESSIONAL = "professional"
    CASUAL = "casual"

@dataclass
class ContentRequest:
    """Request for content generation."""
    niche: str
    content_type: ContentType
    tone: ToneType
    platform: str
    target_audience: Dict[str, Any]
    keywords: List[str] = field(default_factory=list)
    max_length: int = 280
    include_hashtags: bool = True
    include_emoji: bool = True

@dataclass
class GeneratedContent:
    """Generated content result."""
    id: str
    content: str
    hashtags: List[str]
    engagement_score: float
    viral_potential: float
    niche: str
    platform: str
    created_at: datetime = field(default_factory=datetime.now)

class AIContentGenerator:
    """AI-powered content generation system."""
    
    def __init__(self):
        self.content_templates = self._initialize_templates()
        self.hashtag_database = self._initialize_hashtags()
        self.engagement_patterns = self._initialize_engagement_patterns()
        self.viral_indicators = self._initialize_viral_indicators()
    
    def _initialize_templates(self) -> Dict[str, List[str]]:
        """Initialize content templates for different niches."""
        return {
            "fitness": {
                "motivational": [
                    "🔥 {keyword} is not just about the body, it's about the mind too!",
                    "💪 Every {keyword} session brings you closer to your goals!",
                    "🏃‍♂️ Consistency in {keyword} beats perfection every time!",
                    "🌟 Your {keyword} journey is unique - embrace it!",
                    "💯 Small {keyword} steps lead to big transformations!"
                ],
                "educational": [
                    "📚 Did you know? {keyword} can improve your {benefit}!",
                    "🧠 The science behind {keyword}: {fact}!",
                    "💡 Pro tip: {keyword} works best when combined with {tip}!",
                    "🔬 Research shows {keyword} increases {benefit} by {percentage}!",
                    "📖 Understanding {keyword}: The complete guide!"
                ],
                "inspirational": [
                    "✨ Your {keyword} story inspires others!",
                    "🌟 Every {keyword} challenge makes you stronger!",
                    "💫 The {keyword} journey is about progress, not perfection!",
                    "⭐ Your {keyword} dedication is changing lives!",
                    "🌙 Dream big, {keyword} bigger!"
                ]
            },
            "technology": {
                "professional": [
                    "🚀 The future of {keyword} is here!",
                    "💻 {keyword} is revolutionizing {industry}!",
                    "🔧 How {keyword} is solving {problem}!",
                    "📱 {keyword} innovation at its finest!",
                    "⚡ {keyword} technology explained!"
                ],
                "educational": [
                    "📚 Understanding {keyword}: A beginner's guide!",
                    "🧠 The psychology behind {keyword}!",
                    "💡 {keyword} best practices you need to know!",
                    "🔬 The science of {keyword}!",
                    "📖 {keyword} fundamentals explained!"
                ],
                "casual": [
                    "😎 {keyword} is pretty cool, right?",
                    "🤖 My thoughts on {keyword}!",
                    "💭 {keyword} is changing everything!",
                    "🎯 Why {keyword} matters!",
                    "🔥 {keyword} is the future!"
                ]
            },
            "fashion": {
                "inspirational": [
                    "👗 Style is a way to say who you are!",
                    "✨ Confidence is the best outfit!",
                    "🌟 Fashion fades, style is eternal!",
                    "💫 Your style, your story!",
                    "⭐ Fashion is the armor to survive reality!"
                ],
                "educational": [
                    "📚 The history of {keyword} fashion!",
                    "🧠 Psychology of {keyword} style!",
                    "💡 {keyword} styling tips for everyone!",
                    "🔬 The science of {keyword} trends!",
                    "📖 {keyword} fashion guide!"
                ],
                "casual": [
                    "😍 Loving this {keyword} look!",
                    "🤩 {keyword} style goals!",
                    "💕 Obsessed with {keyword}!",
                    "🎯 {keyword} fashion is everything!",
                    "🔥 {keyword} trends are fire!"
                ]
            },
            "business": {
                "professional": [
                    "💼 {keyword} strategies that work!",
                    "📈 How {keyword} drives growth!",
                    "🎯 {keyword} insights for success!",
                    "🚀 {keyword} innovation in business!",
                    "⚡ {keyword} best practices!"
                ],
                "educational": [
                    "📚 Understanding {keyword} in business!",
                    "🧠 The psychology of {keyword}!",
                    "💡 {keyword} strategies explained!",
                    "🔬 Research on {keyword} effectiveness!",
                    "📖 {keyword} business guide!"
                ],
                "motivational": [
                    "🔥 Your {keyword} journey starts now!",
                    "💪 Every {keyword} challenge makes you stronger!",
                    "🌟 {keyword} success is within reach!",
                    "💫 Dream big, {keyword} bigger!",
                    "⭐ Your {keyword} dedication pays off!"
                ]
            }
        }
    
    def _initialize_hashtags(self) -> Dict[str, List[str]]:
        """Initialize hashtag database."""
        return {
            "fitness": [
                "#fitness", "#workout", "#gym", "#health", "#fitnessmotivation",
                "#fit", "#training", "#exercise", "#healthy", "#lifestyle",
                "#fitnessgoals", "#workoutmotivation", "#gymlife", "#healthylifestyle",
                "#fitnessjourney", "#fitfam", "#training", "#exercise", "#motivation"
            ],
            "technology": [
                "#tech", "#technology", "#innovation", "#programming", "#ai",
                "#startup", "#coding", "#software", "#digital", "#future",
                "#technews", "#innovation", "#programming", "#artificialintelligence",
                "#startup", "#coding", "#software", "#digitaltransformation"
            ],
            "fashion": [
                "#fashion", "#style", "#outfit", "#fashionista", "#ootd",
                "#fashionblogger", "#streetstyle", "#fashionstyle", "#fashionable",
                "#fashioninspiration", "#style", "#outfit", "#fashionista", "#ootd",
                "#fashionblogger", "#streetstyle", "#fashionstyle", "#fashionable"
            ],
            "business": [
                "#business", "#entrepreneur", "#success", "#marketing", "#leadership",
                "#startup", "#entrepreneurship", "#businessowner", "#smallbusiness",
                "#businessgrowth", "#entrepreneur", "#success", "#marketing", "#leadership",
                "#startup", "#entrepreneurship", "#businessowner", "#smallbusiness"
            ]
        }
    
    def _initialize_engagement_patterns(self) -> Dict[str, Any]:
        """Initialize engagement patterns for different content types."""
        return {
            "caption": {
                "question_marks": 0.15,
                "emojis": 0.25,
                "hashtags": 0.20,
                "call_to_action": 0.30,
                "personal_story": 0.40
            },
            "story": {
                "polls": 0.35,
                "questions": 0.30,
                "behind_scenes": 0.25,
                "daily_updates": 0.20
            },
            "reel": {
                "trending_audio": 0.40,
                "educational": 0.30,
                "entertainment": 0.25,
                "inspirational": 0.20
            }
        }
    
    def _initialize_viral_indicators(self) -> Dict[str, float]:
        """Initialize viral potential indicators."""
        return {
            "trending_topic": 0.8,
            "emotional_trigger": 0.7,
            "controversial": 0.6,
            "educational": 0.5,
            "entertaining": 0.6,
            "inspirational": 0.7,
            "relatable": 0.6,
            "timely": 0.8
        }
    
    async def generate_content(self, request: ContentRequest) -> GeneratedContent:
        """Generate content based on the request."""
        content_id = f"content-{request.niche}-{int(time.time())}"
        
        # Generate main content
        content = await self._generate_main_content(request)
        
        # Generate hashtags
        hashtags = await self._generate_hashtags(request)
        
        # Calculate engagement score
        engagement_score = await self._calculate_engagement_score(content, hashtags, request)
        
        # Calculate viral potential
        viral_potential = await self._calculate_viral_potential(content, request)
        
        return GeneratedContent(
            id=content_id,
            content=content,
            hashtags=hashtags,
            engagement_score=engagement_score,
            viral_potential=viral_potential,
            niche=request.niche,
            platform=request.platform
        )
    
    async def _generate_main_content(self, request: ContentRequest) -> str:
        """Generate the main content text."""
        templates = self.content_templates.get(request.niche, {})
        tone_templates = templates.get(request.tone.value, [])
        
        if not tone_templates:
            # Fallback template
            tone_templates = [
                "🔥 Amazing {keyword} content!",
                "💪 Great {keyword} insights!",
                "🌟 Wonderful {keyword} information!"
            ]
        
        # Select random template
        template = random.choice(tone_templates)
        
        # Fill template with keywords
        keywords = request.keywords or [request.niche]
        keyword = random.choice(keywords)
        
        # Add benefits and facts for educational content
        if request.tone == ToneType.EDUCATIONAL:
            benefits = ["focus", "energy", "creativity", "productivity", "happiness"]
            facts = ["improves performance", "boosts confidence", "increases efficiency"]
            percentages = ["25%", "30%", "40%", "50%"]
            
            template = template.replace("{benefit}", random.choice(benefits))
            template = template.replace("{fact}", random.choice(facts))
            template = template.replace("{percentage}", random.choice(percentages))
        
        # Fill template
        content = template.replace("{keyword}", keyword)
        
        # Add emoji if requested
        if request.include_emoji:
            emojis = ["🔥", "💪", "🌟", "✨", "💯", "🚀", "💡", "🎯", "⭐", "💫"]
            content = f"{random.choice(emojis)} {content}"
        
        # Add call to action
        if random.random() < 0.3:  # 30% chance
            ctas = [
                "What do you think?",
                "Share your thoughts!",
                "Comment below!",
                "Tag a friend!",
                "Save for later!"
            ]
            content += f" {random.choice(ctas)}"
        
        return content
    
    async def _generate_hashtags(self, request: ContentRequest) -> List[str]:
        """Generate relevant hashtags."""
        if not request.include_hashtags:
            return []
        
        # Get base hashtags for niche
        base_hashtags = self.hashtag_database.get(request.niche, [])
        
        # Select random hashtags (3-7 hashtags)
        num_hashtags = random.randint(3, 7)
        selected_hashtags = random.sample(base_hashtags, min(num_hashtags, len(base_hashtags)))
        
        # Add niche-specific hashtags
        niche_hashtags = [f"#{request.niche}", f"#{request.niche}life", f"#{request.niche}goals"]
        selected_hashtags.extend(niche_hashtags)
        
        # Add platform-specific hashtags
        platform_hashtags = {
            "instagram": ["#instagram", "#instagood", "#instalike"],
            "twitter": ["#twitter", "#tweeting", "#twitterverse"],
            "tiktok": ["#tiktok", "#fyp", "#foryou"],
            "linkedin": ["#linkedin", "#networking", "#professional"]
        }
        
        platform_tags = platform_hashtags.get(request.platform, [])
        selected_hashtags.extend(platform_tags)
        
        return selected_hashtags[:10]  # Limit to 10 hashtags
    
    async def _calculate_engagement_score(self, content: str, hashtags: List[str], request: ContentRequest) -> float:
        """Calculate engagement score for the content."""
        score = 0.5  # Base score
        
        # Content length analysis
        if 50 <= len(content) <= 150:
            score += 0.1  # Optimal length
        elif len(content) > 150:
            score += 0.05  # Good length
        
        # Hashtag analysis
        if 3 <= len(hashtags) <= 7:
            score += 0.15  # Optimal hashtag count
        elif len(hashtags) > 7:
            score += 0.1  # Good hashtag count
        
        # Emoji analysis
        emoji_count = sum(1 for char in content if ord(char) > 127)
        if 1 <= emoji_count <= 3:
            score += 0.1  # Good emoji usage
        
        # Question marks (engagement trigger)
        if "?" in content:
            score += 0.15
        
        # Call to action
        cta_words = ["think", "share", "comment", "tag", "save"]
        if any(word in content.lower() for word in cta_words):
            score += 0.2
        
        # Tone analysis
        tone_scores = {
            ToneType.MOTIVATIONAL: 0.8,
            ToneType.INSPIRATIONAL: 0.7,
            ToneType.EDUCATIONAL: 0.6,
            ToneType.PROFESSIONAL: 0.5,
            ToneType.CASUAL: 0.6,
            ToneType.FUNNY: 0.7
        }
        score += tone_scores.get(request.tone, 0.5) * 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    async def _calculate_viral_potential(self, content: str, request: ContentRequest) -> float:
        """Calculate viral potential for the content."""
        potential = 0.5  # Base potential
        
        # Trending topic analysis
        trending_keywords = ["ai", "fitness", "tech", "business", "fashion", "lifestyle"]
        if any(keyword in content.lower() for keyword in trending_keywords):
            potential += 0.2
        
        # Emotional trigger analysis
        emotional_words = ["amazing", "incredible", "unbelievable", "shocking", "mind-blowing"]
        if any(word in content.lower() for word in emotional_words):
            potential += 0.15
        
        # Educational value
        if request.tone == ToneType.EDUCATIONAL:
            potential += 0.1
        
        # Inspirational value
        if request.tone in [ToneType.INSPIRATIONAL, ToneType.MOTIVATIONAL]:
            potential += 0.15
        
        # Relatability
        relatable_words = ["you", "your", "everyone", "we", "us"]
        if any(word in content.lower() for word in relatable_words):
            potential += 0.1
        
        # Timeliness (current trends)
        if "2024" in content or "new" in content.lower():
            potential += 0.1
        
        return min(potential, 1.0)  # Cap at 1.0
    
    async def generate_batch_content(self, requests: List[ContentRequest]) -> List[GeneratedContent]:
        """Generate multiple content pieces."""
        results = []
        for request in requests:
            content = await self.generate_content(request)
            results.append(content)
        return results
    
    async def optimize_content(self, content: GeneratedContent, target_engagement: float = 0.8) -> GeneratedContent:
        """Optimize content for better engagement."""
        if content.engagement_score >= target_engagement:
            return content
        
        # Try different variations
        variations = []
        for _ in range(5):
            request = ContentRequest(
                niche=content.niche,
                content_type=ContentType.CAPTION,
                tone=random.choice(list(ToneType)),
                platform=content.platform,
                target_audience={},
                keywords=content.hashtags[:3]  # Use hashtags as keywords
            )
            
            variation = await self.generate_content(request)
            variations.append(variation)
        
        # Return the best variation
        best_variation = max(variations, key=lambda x: x.engagement_score)
        return best_variation
    
    async def get_content_analytics(self, contents: List[GeneratedContent]) -> Dict[str, Any]:
        """Get analytics for generated content."""
        if not contents:
            return {}
        
        avg_engagement = sum(c.engagement_score for c in contents) / len(contents)
        avg_viral_potential = sum(c.viral_potential for c in contents) / len(contents)
        
        # Platform distribution
        platform_dist = {}
        for content in contents:
            platform_dist[content.platform] = platform_dist.get(content.platform, 0) + 1
        
        # Niche distribution
        niche_dist = {}
        for content in contents:
            niche_dist[content.niche] = niche_dist.get(content.niche, 0) + 1
        
        # Top performing content
        top_content = max(contents, key=lambda x: x.engagement_score)
        
        return {
            "total_content": len(contents),
            "average_engagement": avg_engagement,
            "average_viral_potential": avg_viral_potential,
            "platform_distribution": platform_dist,
            "niche_distribution": niche_dist,
            "top_performing_content": {
                "id": top_content.id,
                "content": top_content.content,
                "engagement_score": top_content.engagement_score,
                "viral_potential": top_content.viral_potential
            }
        }

# Example usage
async def test_ai_content_generator():
    """Test the AI content generator."""
    generator = AIContentGenerator()
    
    # Test different content requests
    requests = [
        ContentRequest(
            niche="fitness",
            content_type=ContentType.CAPTION,
            tone=ToneType.MOTIVATIONAL,
            platform="instagram",
            target_audience={"age": "18-35", "interests": ["fitness", "health"]},
            keywords=["workout", "gym", "fitness"]
        ),
        ContentRequest(
            niche="technology",
            content_type=ContentType.CAPTION,
            tone=ToneType.EDUCATIONAL,
            platform="twitter",
            target_audience={"age": "25-45", "interests": ["tech", "programming"]},
            keywords=["ai", "programming", "innovation"]
        ),
        ContentRequest(
            niche="fashion",
            content_type=ContentType.CAPTION,
            tone=ToneType.INSPIRATIONAL,
            platform="instagram",
            target_audience={"age": "18-30", "interests": ["fashion", "style"]},
            keywords=["style", "fashion", "outfit"]
        )
    ]
    
    print("🤖 AI CONTENT GENERATOR TEST")
    print("=" * 40)
    
    for i, request in enumerate(requests, 1):
        print(f"\n📝 Generating content {i}:")
        print(f"   Niche: {request.niche}")
        print(f"   Tone: {request.tone.value}")
        print(f"   Platform: {request.platform}")
        
        content = await generator.generate_content(request)
        
        print(f"   Content: {content.content}")
        print(f"   Hashtags: {', '.join(content.hashtags[:5])}")
        print(f"   Engagement Score: {content.engagement_score:.2f}")
        print(f"   Viral Potential: {content.viral_potential:.2f}")
    
    # Generate batch content
    print(f"\n📦 Generating batch content...")
    batch_contents = await generator.generate_batch_content(requests)
    
    # Get analytics
    analytics = await generator.get_content_analytics(batch_contents)
    
    print(f"\n📊 CONTENT ANALYTICS:")
    print(f"   Total Content: {analytics['total_content']}")
    print(f"   Average Engagement: {analytics['average_engagement']:.2f}")
    print(f"   Average Viral Potential: {analytics['average_viral_potential']:.2f}")
    print(f"   Platform Distribution: {analytics['platform_distribution']}")
    print(f"   Niche Distribution: {analytics['niche_distribution']}")
    
    return batch_contents

if __name__ == "__main__":
    asyncio.run(test_ai_content_generator()) 