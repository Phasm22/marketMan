"""
ETF Analysis Engine - Core AI analysis logic for thematic ETF opportunities
"""
import os
from openai import OpenAI
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Dict, Optional, Tuple

load_dotenv()

# Set up logging
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_tactical_explanation(analysis_result, article_title):
    """Generate a tactical, conversational explanation of the trading signal"""
    try:
        signal = analysis_result.get("signal", "Neutral")
        confidence = analysis_result.get("confidence", 0)
        etfs = analysis_result.get("affected_etfs", [])
        reasoning = analysis_result.get("reasoning", "")
        sector = analysis_result.get("sector", "Mixed")

        # Only generate tactical explanations for high-confidence signals
        if confidence < 7:
            return None

        prompt = f"""
You are MarketMan's senior portfolio strategist. Generate a tactical trading brief using proper financial terminology and specific actionable recommendations.

SIGNAL DATA:
- Article: "{article_title}"
- Signal: {signal} ({confidence}/10 conviction)
- Sector: {sector}
- Target ETFs: {', '.join(etfs[:5])}
- Market Thesis: "{reasoning}"

Write a professional trading brief in this format:

"**TACTICAL BRIEF - {signal.upper()} SIGNAL**

**Market Thesis:**
[2-3 sentences explaining the fundamental catalyst and why this creates an opportunity]

**Recommended Positioning:**
That {signal.upper()} signal translates to:
• **Primary Trade**: [Specific ETF] - [Entry strategy with price levels]
• **Position Size**: [Risk-appropriate allocation %]
• **Stop Loss**: [Specific price level or %]
• **Profit Target**: [Price target with timeline]

**Risk Management:**
• **Upside Scenario**: [Best case outcome and price targets]
• **Downside Risk**: [Key risk factors and hedge strategies]  
• **Time Horizon**: [Short/medium/long-term outlook]

**Execution Notes:**
[Specific entry timing, volume considerations, or alternative plays]"

Use proper financial terminology: entry/exit levels, position sizing, risk-reward ratios, stop-losses, profit targets. Be specific with actionable price levels and percentages. Maximum 250 words.
"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Slightly higher for more personality
            max_tokens=400,
        )

        tactical_explanation = response.choices[0].message.content.strip()
        logger.info(f"💡 Generated tactical explanation ({len(tactical_explanation)} chars)")
        return tactical_explanation

    except Exception as e:
        logger.warning(f"⚠️ Failed to generate tactical explanation: {e}")
        return None


def build_analysis_prompt(headline, summary, snippet="", etf_prices=None, contextual_insight=None):
    """Build comprehensive analysis prompt for MarketMan AI"""
    # Build comprehensive ETF price context if available
    price_context = ""
    if etf_prices:
        price_context = "\n\n📊 LIVE MARKET SNAPSHOT:\n"
        for symbol, data in etf_prices.items():
            change_sign = "+" if data["change_pct"] >= 0 else ""
            trend_emoji = "📈" if data["change_pct"] > 0 else "📉" if data["change_pct"] < 0 else "➖"
            price_context += f"• {symbol} ({data.get('name', symbol)}): ${data['price']} ({change_sign}{data['change_pct']}%) {trend_emoji}\n"
        price_context += "\nUse this real-time data to inform your strategic analysis.\n"

    return f"""
You are MarketMan — a tactical ETF strategist focused on identifying high-momentum opportunities in defense, AI, energy, clean tech, and volatility hedging. Your job is to turn breaking market intelligence into ETF positioning signals.

**CRITICAL ETF SELECTION RULES:**
• Only recommend specialized thematic ETFs (BOTZ, ITA, ICLN, URA, etc.)
• AVOID broad-market funds (XLK, QQQ, VTI, SPY) unless no pure-play alternatives exist
• Focus on ETFs with <$5B AUM that offer targeted sector exposure
• Prioritize ETFs that could appear in multiple analyses today for momentum confirmation

Analyze the following news and market context to determine if there's an actionable ETF play:

🧠 PATTERN MEMORY:
{contextual_insight or 'None'}

📊 MARKET SNAPSHOT:
{price_context or 'No price data'}

📰 ARTICLE:
Title: "{headline}"
Summary: "{summary}"
Additional Context: "{snippet}"

If this content is NOT relevant to thematic ETF investing, return:
{{"relevance": "not_financial", "confidence": 0}}

Otherwise, return:
{{
  "relevance": "financial",
  "sector": "Defense|AI|CleanTech|Volatility|Uranium|Broad Market",
  "signal": "Bullish|Bearish|Neutral",
  "confidence": 1-10,
  "affected_etfs": ["ITA", "XAR", "ICLN", "BOTZ", "URA", etc],
  "reasoning": "Short rationale focusing on specialized ETF opportunity",
  "market_impact": "Brief on specialized ETF sector strategy",
  "price_action": "Expected movements in focused ETF universe",
  "strategic_advice": "Tactical recommendations for pure-play positioning",
  "coaching_tone": "Professional insight with specialized ETF momentum focus",
  "risk_factors": "Key risks specific to thematic/sector exposure",
  "opportunity_thesis": "Why specialized ETFs outperform broad market in this scenario",
  "theme_category": "AI/Robotics|Defense/Aerospace|CleanTech/Climate|Volatility/Hedge|Nuclear/Uranium"
}}

**REMEMBER:** Favor specialized, pure-play ETFs over broad market funds. Only include broad-market ETFs if truly no specialized alternatives exist for the theme.
"""


def technical_score(rsi=None, macd=None, bollinger=None):
    """
    Evaluate soft (secondary) technical indicators for a trade signal.
    Returns (score, notes) where score is the number of soft rules passed, and notes is a summary string.
    """
    score = 0
    notes = []
    if rsi is not None:
        if 45 < rsi < 60:
            score += 1
            notes.append("RSI in optimal range")
        else:
            notes.append(f"RSI out of range: {rsi}")
    else:
        notes.append("RSI data unavailable")
    if macd is not None:
        if macd > 0:
            score += 1
            notes.append("MACD positive")
        else:
            notes.append(f"MACD not positive: {macd}")
    else:
        notes.append("MACD data unavailable")
    if bollinger is not None:
        if bollinger == "tight":
            score += 1
            notes.append("Bollinger bands tight")
        else:
            notes.append(f"Bollinger bands: {bollinger}")
    else:
        notes.append("Bollinger data unavailable")
    return score, "; ".join(notes)


def analyze_thematic_etf_news(
    headline,
    summary,
    snippet="",
    etf_prices=None,
    contextual_insight=None,
    memory=None,
    rsi=None,
    macd=None,
    bollinger=None,
):
    """
    Analyze news for thematic ETF opportunities using MarketMan AI.
    Applies hard (primary) rules first, then soft (secondary) technical scoring.
    Returns analysis result with technical_score and technical_notes fields.
    """
    # Compact logging for production, detailed for debug
    if DEBUG_MODE:
        logger.debug(f"🤖 MarketMan ANALYZING:")
        logger.debug(f"   Title: '{headline}'")
        logger.debug(f"   Summary: '{summary}'")
        logger.debug(f"   Snippet: '{snippet}'")
    else:
        logger.info(f"🤖 Analyzing: {headline[:60]}...")

    prompt = build_analysis_prompt(headline, summary, snippet, etf_prices, contextual_insight)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Lower temperature for more consistent JSON
        )

        result = response.choices[0].message.content.strip()

        if DEBUG_MODE:
            logger.debug(f"🤖 MarketMan RESPONSE: {result}")
        else:
            logger.debug(f"🤖 Response received ({len(result)} chars)")

        # Clean up common JSON formatting issues
        result = result.replace("```json", "").replace("```", "")
        result = result.strip()
        try:
            json_result = json.loads(result)
            # Hard rules
            hard_rule_fail = False
            hard_rule_notes = []
            # 1. confidence >= 7
            if json_result.get("confidence", 0) < 7:
                hard_rule_fail = True
                hard_rule_notes.append(
                    f"Confidence below threshold: {json_result.get('confidence')}"
                )
            # 2. signal is Bullish or Bearish
            if json_result.get("signal", "").lower() not in ["bullish", "bearish"]:
                hard_rule_fail = True
                hard_rule_notes.append(f"Signal not actionable: {json_result.get('signal')}")
            # 3. affected_etfs contains at least one specialized ETF
            specialized_etfs = [
                "BOTZ",
                "ITA",
                "ICLN",
                "URA",
                "XAR",
                "DFEN",
                "PPA",
                "ROBO",
                "IRBO",
                "ARKQ",
                "SMH",
                "SOXX",
                "TAN",
                "QCLN",
                "PBW",
                "LIT",
                "REMX",
                "URNM",
                "NLR",
                "VIXY",
                "VXX",
                "SQQQ",
                "SPXS",
            ]
            if not any(etf in specialized_etfs for etf in json_result.get("affected_etfs", [])):
                hard_rule_fail = True
                hard_rule_notes.append("No specialized ETF in affected_etfs")
            if hard_rule_fail:
                logger.info(
                    f"🚫 Hard rule filter: {'; '.join(hard_rule_notes)} | {headline[:50]}..."
                )
                return None
            # Soft rules (technical scoring)
            score, notes = technical_score(rsi, macd, bollinger)
            json_result["technical_score"] = score
            json_result["technical_notes"] = notes
            if DEBUG_MODE:
                logger.debug(f"🧪 Technical score: {score} | Notes: {notes}")
            # Add metadata to the analysis result
            json_result["analysis_timestamp"] = datetime.now().isoformat()
            # Store the analysis in memory for contextual tracking
            if memory:
                try:
                    memory.store_signal(json_result, headline)
                    logger.debug("💾 Analysis stored in MarketMemory")
                except Exception as mem_error:
                    logger.warning(f"⚠️ Failed to store analysis in memory: {mem_error}")
            return json_result
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse MarketMan response as JSON: {e}")
            if DEBUG_MODE:
                logger.error(f"Raw response: {result}")
            if "not energy related" in result.lower() or "not_financial" in result.lower():
                logger.info(f"🚫 MarketMan detected non-ETF content: {headline[:50]}...")
                return None
            return {
                "relevance": "financial",
                "sector": "Thematic",
                "signal": "Neutral",
                "confidence": 1,
                "affected_etfs": [],
                "reasoning": "Failed to parse AI response",
                "raw_response": result,
                "technical_score": 0,
                "technical_notes": "JSON parse error; no technicals",
            }
    except Exception as e:
        logger.error(f"❌ Error calling OpenAI API: {e}")
        return None


def categorize_etfs_by_sector(etfs):
    """Group ETFs by sector and return primary sector + key ETFs"""
    sector_mapping = {
        # Defense & Aerospace
        "Defense": ["ITA", "XAR", "DFEN", "PPA"],
        # AI & Robotics
        "AI": ["BOTZ", "ROBO", "IRBO", "ARKQ", "SMH", "SOXX"],
        # Clean Energy & Climate
        "CleanTech": ["ICLN", "TAN", "QCLN", "PBW", "LIT", "REMX"],
        # Nuclear & Uranium (aligned with AI response)
        "Uranium": ["URNM", "NLR", "URA"],
        # Volatility & Inverse
        "Volatility": ["VIXY", "VXX", "SQQQ", "SPXS"],
        # Traditional Sectors
        "Energy": ["XLE"],
        "Finance": ["XLF"],
        "Tech": ["XLK", "QQQ"],
        "Market": ["SPY"],
    }

    # Find which sectors are represented
    sector_matches = {}
    for etf in etfs:
        for sector, sector_etfs in sector_mapping.items():
            if etf in sector_etfs:
                if sector not in sector_matches:
                    sector_matches[sector] = []
                sector_matches[sector].append(etf)

    # Return top 2-3 ETFs per sector, prioritizing most mentioned
    focused_etfs = []
    primary_sector = None

    if sector_matches:
        # Find primary sector (most ETFs mentioned)
        primary_sector = max(sector_matches.keys(), key=lambda s: len(sector_matches[s]))

        # Take top 2-3 ETFs from primary sector + 1-2 from others
        for sector, sector_etfs in sector_matches.items():
            if sector == primary_sector:
                focused_etfs.extend(sector_etfs[:3])  # Top 3 from primary
            else:
                focused_etfs.extend(sector_etfs[:2])  # Top 2 from others

    return focused_etfs, primary_sector


def analyze_news_batch(news_batch, etf_prices=None, contextual_insight=None, memory=None):
    """
    Analyze a batch of news items for thematic ETF opportunities.
    Processes multiple headlines together for more comprehensive analysis.
    
    Args:
        news_batch: NewsBatch object containing multiple news items
        etf_prices: Optional dict of current ETF prices
        contextual_insight: Optional contextual information from memory
        memory: Optional MarketMemory instance for storing results
    
    Returns:
        Dict containing batch analysis results
    """
    if not news_batch or not news_batch.items:
        logger.warning("⚠️ Empty news batch provided")
        return None
    
    logger.info(f"🤖 Analyzing news batch: {news_batch.get_summary()}")
    
    # Build batch analysis prompt
    prompt = build_batch_analysis_prompt(news_batch, etf_prices, contextual_insight)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Lower temperature for more consistent JSON
        )
        
        result = response.choices[0].message.content.strip()
        
        if DEBUG_MODE:
            logger.debug(f"🤖 Batch analysis response: {result}")
        else:
            logger.debug(f"🤖 Batch analysis response received ({len(result)} chars)")
        
        # Parse JSON response
        result = result.replace("```json", "").replace("```", "").strip()
        try:
            json_result = json.loads(result)
            
            # Apply hard rules to batch analysis
            if not _validate_batch_analysis(json_result):
                logger.info(f"🚫 Batch analysis failed validation: {news_batch.batch_id}")
                return None
            
            # Add metadata
            json_result["batch_id"] = news_batch.batch_id
            json_result["batch_size"] = news_batch.batch_size
            json_result["common_tickers"] = news_batch.common_tickers
            json_result["common_keywords"] = news_batch.common_keywords
            json_result["analysis_timestamp"] = datetime.now().isoformat()
            json_result["source_headlines"] = [item.title for item in news_batch.items]
            
            # Store in memory if available
            if memory:
                try:
                    memory.store_signal(json_result, f"Batch: {news_batch.batch_id}")
                    logger.debug("💾 Batch analysis stored in MarketMemory")
                except Exception as mem_error:
                    logger.warning(f"⚠️ Failed to store batch analysis in memory: {mem_error}")
            
            logger.info(f"✅ Batch analysis complete: {json_result.get('signal', 'Unknown')} signal, confidence {json_result.get('confidence', 0)}")
            return json_result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse batch analysis response as JSON: {e}")
            if DEBUG_MODE:
                logger.error(f"Raw response: {result}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error calling OpenAI API for batch analysis: {e}")
        return None


def build_batch_analysis_prompt(news_batch, etf_prices=None, contextual_insight=None):
    """Build comprehensive analysis prompt for a batch of news items with multi-source validation"""
    # Build ETF price context
    price_context = ""
    if etf_prices:
        price_context = "\n\n📊 LIVE MARKET SNAPSHOT:\n"
        for symbol, data in etf_prices.items():
            change_sign = "+" if data["change_pct"] >= 0 else ""
            trend_emoji = "📈" if data["change_pct"] > 0 else "📉" if data["change_pct"] < 0 else "➖"
            price_context += f"• {symbol} ({data.get('name', symbol)}): ${data['price']} ({change_sign}{data['change_pct']}%) {trend_emoji}\n"
        price_context += "\nUse this real-time data to inform your strategic analysis.\n"
    
    # Build news batch content
    news_content = news_batch.get_combined_text()
    
    # Multi-source validation context
    validation_context = f"""
🔍 MULTI-SOURCE VALIDATION METRICS:
• Batch Quality Score: {news_batch.batch_quality_score:.2f}/1.0
• Source Agreement: {news_batch.source_agreement_score:.2f}/1.0
• Source Diversity: {news_batch.source_diversity} unique sources
• Average Source Weight: {news_batch.avg_source_weight:.2f}/5.0
• Sentiment Consistency: {news_batch.sentiment_consistency:.2f}/1.0
• Contradiction Flag: {'⚠️ YES - Sources contradict each other' if news_batch.contradiction_flag else '✅ NO - Sources are consistent'}
• Average Relevance: {news_batch.avg_relevance_score:.2f}/1.0
• Average Sentiment: {news_batch.avg_sentiment_score:.2f} (-1 to +1)

📊 SIGNAL QUALITY ASSESSMENT:
"""
    
    # Add quality-based guidance
    if news_batch.batch_quality_score >= 0.8:
        validation_context += "• HIGH QUALITY: Strong source agreement, high relevance, consistent sentiment\n"
        validation_context += "• RECOMMENDATION: High confidence signals likely\n"
    elif news_batch.batch_quality_score >= 0.6:
        validation_context += "• MEDIUM QUALITY: Moderate source agreement, some relevance\n"
        validation_context += "• RECOMMENDATION: Moderate confidence, verify with additional context\n"
    else:
        validation_context += "• LOW QUALITY: Weak source agreement, contradictions, or low relevance\n"
        validation_context += "• RECOMMENDATION: Low confidence, consider filtering out\n"
    
    if news_batch.contradiction_flag:
        validation_context += "• ⚠️ CONTRADICTION DETECTED: Sources have opposing views - analyze carefully\n"
    
    return f"""
You are MarketMan — a tactical ETF strategist focused on identifying high-momentum opportunities in defense, AI, energy, clean tech, and volatility hedging. Your job is to analyze a BATCH of related news items and identify the strongest ETF opportunities.

**CRITICAL ETF SELECTION RULES:**
• Only recommend specialized thematic ETFs (BOTZ, ITA, ICLN, URA, etc.)
• AVOID broad-market funds (XLK, QQQ, VTI, SPY) unless no pure-play alternatives exist
• Focus on ETFs with <$5B AUM that offer targeted sector exposure
• Prioritize ETFs that could appear in multiple analyses today for momentum confirmation

**BATCH ANALYSIS APPROACH:**
• Look for CONFIRMATION across multiple headlines (stronger signal)
• Identify EMERGING TRENDS from related news items
• Focus on the MOST ACTIONABLE opportunities in the batch
• Consider the COMBINED IMPACT of all headlines on specific sectors
• Pay attention to SOURCE QUALITY and AGREEMENT

🧠 PATTERN MEMORY:
{contextual_insight or 'None'}

📊 MARKET SNAPSHOT:
{price_context or 'No price data'}

{validation_context}

📰 NEWS BATCH ({news_batch.batch_size} items):
{news_content}

**BATCH ANALYSIS TASK:**
Analyze this batch of related news items to determine if there's a STRONG, ACTIONABLE ETF opportunity. Look for:
1. **Confirmation patterns** - multiple headlines supporting the same thesis
2. **Emerging trends** - new developments that could drive sector momentum
3. **Specific catalysts** - concrete events that could move ETF prices
4. **Sector focus** - which specialized ETF sectors are most affected
5. **Source reliability** - how much to trust the signal based on source quality

**SIGNAL QUALITY CONSIDERATIONS:**
• If batch quality score < 0.5, be more conservative with confidence
• If contradictions detected, analyze both sides and explain uncertainty
• If high source agreement, you can be more confident in the signal
• If low sentiment consistency, consider the signal less reliable

If this batch does NOT contain actionable ETF opportunities, return:
{{"relevance": "not_financial", "confidence": 0}}

Otherwise, return:
{{
  "relevance": "financial",
  "sector": "Defense|AI|CleanTech|Volatility|Uranium|Broad Market",
  "signal": "Bullish|Bearish|Neutral",
  "confidence": 1-10,
  "affected_etfs": ["ITA", "XAR", "ICLN", "BOTZ", "URA", etc],
  "reasoning": "Comprehensive analysis of the news batch and its ETF implications",
  "market_impact": "Expected impact on specialized ETF sectors",
  "price_action": "Expected movements in focused ETF universe",
  "strategic_advice": "Tactical recommendations based on batch analysis",
  "coaching_tone": "Professional insight with specialized ETF momentum focus",
  "risk_factors": "Key risks specific to thematic/sector exposure",
  "opportunity_thesis": "Why this batch creates a strong ETF opportunity",
  "theme_category": "AI/Robotics|Defense/Aerospace|CleanTech/Climate|Volatility/Hedge|Nuclear/Uranium",
  "batch_insights": "Key insights from analyzing multiple headlines together",
  "confirmation_strength": "How strongly the batch confirms the signal (1-10)",
  "source_quality_assessment": "Assessment of source reliability and agreement",
  "signal_quality_score": "Overall signal quality based on batch metrics (1-10)"
}}

**REMEMBER:** This is a BATCH analysis - look for patterns and confirmation across multiple headlines. The signal should be stronger if multiple headlines support the same thesis. Consider source quality and agreement when determining confidence.
"""


def _validate_batch_analysis(analysis_result):
    """Validate batch analysis results against hard rules with quality considerations"""
    # Check confidence threshold
    if analysis_result.get("confidence", 0) < 7:
        logger.debug(f"Batch confidence below threshold: {analysis_result.get('confidence')}")
        return False
    
    # Check signal type
    signal = analysis_result.get("signal", "").lower()
    if signal not in ["bullish", "bearish"]:
        logger.debug(f"Batch signal not actionable: {signal}")
        return False
    
    # Check for specialized ETFs
    specialized_etfs = [
        "BOTZ", "ITA", "ICLN", "URA", "XAR", "DFEN", "PPA", "ROBO", "IRBO", "ARKQ",
        "SMH", "SOXX", "TAN", "QCLN", "PBW", "LIT", "REMX", "URNM", "NLR", "VIXY",
        "VXX", "SQQQ", "SPXS"
    ]
    
    affected_etfs = analysis_result.get("affected_etfs", [])
    if not any(etf in specialized_etfs for etf in affected_etfs):
        logger.debug("Batch analysis contains no specialized ETFs")
        return False
    
    # Additional quality checks (if batch metadata is available)
    if "batch_quality_score" in analysis_result:
        quality_score = analysis_result.get("batch_quality_score", 0)
        if quality_score < 0.4:  # Very low quality batches
            logger.debug(f"Batch quality score too low: {quality_score}")
            return False
    
    if "source_quality_assessment" in analysis_result:
        source_assessment = analysis_result.get("source_quality_assessment", "").lower()
        if "unreliable" in source_assessment or "contradictory" in source_assessment:
            logger.debug(f"Source quality assessment indicates unreliable sources")
            return False
    
    return True
