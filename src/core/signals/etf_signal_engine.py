"""
ETF Analysis Engine - Core AI analysis logic for thematic ETF opportunities
"""
import os
import openai
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up logging
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
logger = logging.getLogger(__name__)


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

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Slightly higher for more personality
            max_tokens=400,
        )

        tactical_explanation = response["choices"][0]["message"]["content"].strip()
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
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Lower temperature for more consistent JSON
        )

        result = response["choices"][0]["message"]["content"].strip()

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
