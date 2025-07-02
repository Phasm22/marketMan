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
import copy

from ..utils import get_config

load_dotenv()

# Set up logging
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize config
config_loader = get_config()

# Robust defaults for custom_rules
DEFAULT_CUSTOM_RULES = {
    'rsi_neutral_range': [45, 55],
    'macd_mild_threshold': 0.5,
    'climate_policy_keywords': ['policy', 'funding', 'ETF flow'],
    'volatility_etfs': ['VIXY', 'VXX', 'UVXY'],
    'indirect_news_confidence_penalty': 1,
}

def get_custom_rules(config):
    custom_rules = copy.deepcopy(DEFAULT_CUSTOM_RULES)
    user_rules = config.get('custom_rules', {})
    if not isinstance(user_rules, dict):
        logger.error('custom_rules in config is malformed, using defaults.')
        return custom_rules
    for k, v in user_rules.items():
        custom_rules[k] = v
    return custom_rules

# Helper: context fallback
class ContextWrapper(dict):
    def get_stale(self, key, max_age_seconds=600):
        val = self.get(key)
        if not val or not hasattr(val, 'timestamp'):
            logger.warning(f"Context missing or no timestamp for {key}")
            return None
        age = (datetime.now() - val.timestamp).total_seconds()
        if age > max_age_seconds:
            logger.warning(f"Context for {key} is stale ({age:.0f}s old)")
            return None
        return val

# Main custom rule application

def apply_custom_signal_rules(analysis_result, news_batch, technicals, pattern_results, config, context):
    """
    Applies custom signal rules and annotates the analysis_result with actionable v3 fields only.
    """
    custom_rules = get_custom_rules(config)
    reasoning_notes = []
    # Rule 1: Neutral RSI + mild MACD + vague news
    def is_neutral_rsi(tech):
        rsi = tech.get('rsi')
        rng = custom_rules['rsi_neutral_range']
        return rsi is not None and rng[0] <= rsi <= rng[1]
    def is_mild_macd(tech):
        macd = tech.get('macd')
        return macd is not None and abs(macd) <= custom_rules['macd_mild_threshold']
    def is_vague_news(analysis):
        reasoning = analysis.get('reasoning', '')
        return len(reasoning) < 60 or 'uncertain' in reasoning.lower() or 'may' in reasoning.lower()
    def has_price_or_volume_confirmation(tech):
        return tech.get('price_move', 0) > 1 or tech.get('volume_spike', False)
    def is_thematic_but_indirect(batch, analysis):
        return analysis.get('theme_category', '').lower() == 'ai/robotics' and 'meta' in batch.get_combined_text().lower() and not any('meta' in etf.lower() for etf in analysis.get('affected_etfs', []))
    def is_volatility_etf(analysis):
        return any(etf in custom_rules['volatility_etfs'] for etf in analysis.get('affected_etfs', []))
    def is_single_bearish_news(batch):
        return batch.batch_size == 1 and 'bearish' in batch.get_combined_text().lower()
    def has_implied_vol_confirmation(tech, patterns):
        return context.get('implied_vol_confirmed', False)
    def is_climate_etf(analysis):
        return 'climate' in analysis.get('theme_category', '').lower() or 'clean' in analysis.get('theme_category', '').lower()
    def has_concrete_policy_or_funding(batch):
        text = batch.get_combined_text().lower()
        return any(kw in text for kw in custom_rules['climate_policy_keywords'])
    def is_treasury_volatility_signal(batch, analysis):
        return 'treasury' in batch.get_combined_text().lower() and is_volatility_etf(analysis)
    def has_options_or_futures_confirmation(tech, patterns):
        return context.get('options_flow_confirmed', False)
    # Rule 1
    for ticker, tech in (technicals or {}).items():
        if is_neutral_rsi(tech) and is_mild_macd(tech) and is_vague_news(analysis_result):
            if not has_price_or_volume_confirmation(tech):
                if analysis_result['signal'] == 'bullish':
                    analysis_result['custom_validated'] = True
                    analysis_result['signal'] = 'neutral'
                    note = "Downgraded to neutral due to lack of confirmation (neutral RSI, mild MACD, vague news)"
                    reasoning_notes.append(note)
                    logger.info(f"[SignalRule] {note}")
    # Rule 2
    if is_thematic_but_indirect(news_batch, analysis_result):
        penalty = custom_rules.get('indirect_news_confidence_penalty', 2)
        old_conf = analysis_result['confidence']
        analysis_result['confidence'] = max(1, analysis_result['confidence'] - penalty)
        note = f"Speculative: AI news is outside ETF scope (penalty -{penalty}, {old_conf}->{analysis_result['confidence']})"
        reasoning_notes.append(note)
        logger.info(f"[SignalRule] {note}")
    # Rule 3 & 5
    if is_volatility_etf(analysis_result):
        if not (has_implied_vol_confirmation(technicals, pattern_results) or has_options_or_futures_confirmation(technicals, pattern_results)):
            analysis_result['custom_validated'] = True
            analysis_result['signal'] = 'neutral'
            note = "Neutralized due to lack of volatility confirmation."
            reasoning_notes.append(note)
            logger.info(f"[SignalRule] {note}")
    # Rule 4
    if is_climate_etf(analysis_result) and not has_concrete_policy_or_funding(news_batch):
        if analysis_result['signal'] == 'bullish':
            analysis_result['custom_validated'] = True
            analysis_result['signal'] = 'neutral'
            note = "Downgraded to neutral: climate news lacks concrete policy/funding."
            reasoning_notes.append(note)
            logger.info(f"[SignalRule] {note}")
    return analysis_result

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


def build_analysis_prompt(headline, summary, snippet="", etf_prices=None, contextual_insight=None, technicals=None, pattern_results=None, risk_config=None):
    """Build actionable analysis prompt for a single news item, with price anchors, technicals, and new output fields."""
    price_context = ""
    if etf_prices:
        price_context = "\n\n📊 LIVE MARKET SNAPSHOT:\n"
        for symbol, data in etf_prices.items():
            change_sign = "+" if data["change_pct"] >= 0 else ""
            trend_emoji = "📈" if data["change_pct"] > 0 else "📉" if data["change_pct"] < 0 else "➖"
            price_context += f"• {symbol} ({data.get('name', symbol)}): ${data['price']} ({change_sign}{data['change_pct']}%) {trend_emoji}\n"
        price_context += "\nUse this real-time data to inform your strategic analysis.\n"
    technical_context = ""
    if technicals:
        technical_context = "\n📈 TECHNICAL INDICATORS:\n"
        for ticker, tech_data in technicals.items():
            technical_context += f"• {ticker}: RSI={tech_data.get('rsi', 'N/A')}, MACD={tech_data.get('macd', 'N/A')}, BB={tech_data.get('bollinger', 'N/A')}\n"
        technical_context += "\nUse these technical indicators to assess momentum and support/resistance levels.\n"
    pattern_context = ""
    if pattern_results:
        pattern_context = f"\n🔎 PATTERN RECOGNITION:\n• Patterns Detected: {pattern_results.get('patterns_detected', 0)}\n"
        if pattern_results.get('patterns'):
            for p in pattern_results['patterns']:
                pattern_context += f"  - {p}\n"
        else:
            pattern_context += "  (No patterns detected)\n"
    if risk_config is None:
        risk_config = {}
    max_position_size_percent = risk_config.get('max_position_size_percent', 2.0)
    max_kelly_fraction = risk_config.get('max_kelly_fraction', 0.25)
    return f"""
You are MarketMan — a tactical ETF strategist focused on identifying high-momentum opportunities in defense, AI, energy, clean tech, and volatility hedging. Your job is to analyze a SINGLE news item and identify the most actionable ETF opportunity.

**CRITICAL OUTPUT FIELDS:**
Return a JSON object with the following fields:
- reasoning: Bullet-pointed, data-driven justification for the signal (no narrative). Format as:
  • [Key data point or insight]
  • [Supporting evidence or flow]
  • [Market context or catalyst]
- if_then_scenario: "If [market/volume/price/flow], then [confirm/refute signal]" logic
- contradictory_signals: Risks, opposing news, or macro factors that could flip the thesis
- uncertainty_metric: "Confidence: X, but…" phrasing, including source/quality/volatility context
- price_anchors: Dict with ETF price context: {{"prev_close": X, "pre_market": Y, "5d_trend": "Z%", "volume": "N"}}
- position_risk_bracket: "Position sizing: conservative / aggressive" based on volatility and risk config
- signal: "Bullish", "Bearish", or "Neutral"
- confidence: 1-10 scale
- affected_etfs: List of relevant ETF tickers
- sector: Primary market sector
- market_impact: Expected market reaction
- risk_factors: Key risks to monitor
- technical_notes: Technical analysis insights
- pattern_notes: Pattern recognition insights

**CONTEXT:**
- ETF price anchors: {price_context}
- Technical indicators: {technical_context}
- Pattern recognition: {pattern_context}
- News headline: {headline}
- News summary: {summary}
- News snippet: {snippet}
- Contextual insight: {contextual_insight or 'None'}
- Risk config: max_position_size_percent={max_position_size_percent}, max_kelly_fraction={max_kelly_fraction}

**SINGLE NEWS ANALYSIS TASK:**
Analyze this news item to determine if there's a STRONG, ACTIONABLE ETF opportunity. Output the JSON object as described above.

**EXAMPLE:**
{{
  "relevance": "financial",
  "sector": "AI/Robotics",
  "signal": "Bullish",
  "confidence": 8,
  "affected_etfs": ["BOTZ"],
  "reasoning": [
    "Nvidia earnings beat, AI chip demand surging",
    "BOTZ ETF holdings: Nvidia top 3 weight",
    "Volume spike: BOTZ 2.2x 5-day average"
  ],
  "if_then_scenario": "If BOTZ closes above $30 with >2x average volume, confirm bullish thesis.",
  "contradictory_signals": "If chip export restrictions increase, AI sector could face headwinds.",
  "uncertainty_metric": "Confidence 8, but headline-driven and high volatility week.",
  "price_anchors": {{
    "BOTZ": {{
      "prev_close": 29.80,
      "pre_market": 30.40,
      "5d_trend": "+3.2%",
      "volume": "2.2M (2.2x avg)"
    }}
  }},
  "position_risk_bracket": "Position sizing: moderate (sector volatility, strong catalyst)",
  "risk_factors": "AI chip supply chain risk, regulatory uncertainty",
  "market_impact": "High-conviction AI ETF setup",
  "theme_category": "AI/Robotics"
}}

**REMEMBER:** 
- Use only bullet points for reasoning.
- Always provide an if/then scenario and contradictory signals.
- Always output the position risk bracket based on volatility and config.
- Always surface the uncertainty metric in trader-friendly language.
- Price anchors must be present for each ETF.
- If any field is not applicable, use an empty string or array, but do not omit it.

Return ONLY the JSON object, nothing else.
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
    technicals=None,
    pattern_results=None,
    risk_config=None,
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

    prompt = build_analysis_prompt(
        headline,
        summary,
        snippet,
        etf_prices,
        contextual_insight,
        technicals,
        pattern_results,
        risk_config
    )

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

        # Parse JSON response
        result = result.replace("```json", "").replace("```", "").strip()
        
        # Try to extract JSON from the response (handle extra text)
        try:
            start = result.find('{')
            end = result.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = result[start:end]
                json_result = json.loads(json_str)
            else:
                json_result = json.loads(result)
            # (Optionally) apply custom rules, validation, etc. here
            return json_result
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse analysis response as JSON: {e}")
            if DEBUG_MODE:
                logger.error(f"Raw response: {result}")
            return None
    except Exception as e:
        logger.error(f"❌ Error calling OpenAI API for single news analysis: {e}")
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


def analyze_news_batch(news_batch, etf_prices=None, contextual_insight=None, memory=None, technicals=None, pattern_results=None, context=None, risk_config=None):
    if not news_batch or not news_batch.items:
        logger.warning("⚠️ Empty news batch provided")
        return None
    logger.info(f"🤖 Analyzing news batch: {news_batch.get_summary()}")
    prompt = build_batch_analysis_prompt(news_batch, etf_prices, contextual_insight, technicals, pattern_results, risk_config)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        result = response.choices[0].message.content.strip()
        if DEBUG_MODE:
            logger.debug(f"🤖 Batch analysis response: {result}")
        else:
            logger.debug(f"🤖 Batch analysis response received ({len(result)} chars)")
        result = result.replace("```json", "").replace("```", "").strip()
        try:
            start = result.find('{')
            end = result.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = result[start:end]
                json_result = json.loads(json_str)
            else:
                json_result = json.loads(result)
            # Apply custom rules (with context fallback)
            config = config_loader.load_settings()
            if context is None:
                context = ContextWrapper()
            json_result = apply_custom_signal_rules(json_result, news_batch, technicals, pattern_results, config, context)
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
            json_result["technicals_included"] = len(technicals) if technicals else 0
            json_result["patterns_detected"] = pattern_results.get("patterns_detected", 0) if pattern_results else 0
            json_result["patterns"] = pattern_results.get("patterns", []) if pattern_results else []
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
        if news_batch is not None and hasattr(news_batch, 'batch_id'):
            logger.error(f"❌ Error calling OpenAI API for batch analysis (batch_id={news_batch.batch_id}): {e}")
        else:
            logger.error(f"❌ Error calling OpenAI API for batch analysis: {e}")
        return None


def build_batch_analysis_prompt(news_batch, etf_prices=None, contextual_insight=None, technicals=None, pattern_results=None, risk_config=None):
    """Build comprehensive analysis prompt for a batch of news items with multi-source validation, technical analysis, and pattern recognition, using the new actionable output schema."""
    # Build ETF price context
    price_context = ""
    if etf_prices:
        price_context = "\n\n📊 LIVE MARKET SNAPSHOT:\n"
        for symbol, data in etf_prices.items():
            change_sign = "+" if data["change_pct"] >= 0 else ""
            trend_emoji = "📈" if data["change_pct"] > 0 else "📉" if data["change_pct"] < 0 else "➖"
            price_context += f"• {symbol} ({data.get('name', symbol)}): ${data['price']} ({change_sign}{data['change_pct']}%) {trend_emoji}\n"
        price_context += "\nUse this real-time data to inform your strategic analysis.\n"
    
    # Build technical indicators context
    technical_context = ""
    if technicals:
        technical_context = "\n📈 TECHNICAL INDICATORS:\n"
        for ticker, tech_data in technicals.items():
            technical_context += f"• {ticker}: RSI={tech_data.get('rsi', 'N/A')}, MACD={tech_data.get('macd', 'N/A')}, BB={tech_data.get('bollinger', 'N/A')}\n"
        technical_context += "\nUse these technical indicators to assess momentum and support/resistance levels.\n"
    
    # Build pattern recognition context
    pattern_context = ""
    if pattern_results:
        pattern_context = f"\n🔎 PATTERN RECOGNITION:\n• Patterns Detected: {pattern_results.get('patterns_detected', 0)}\n"
        if pattern_results.get('patterns'):
            for p in pattern_results['patterns']:
                pattern_context += f"  - {p}\n"
        else:
            pattern_context += "  (No patterns detected)\n"
    
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

    # Risk config context
    if risk_config is None:
        risk_config = {}
    max_position_size_percent = risk_config.get('max_position_size_percent', 2.0)
    max_kelly_fraction = risk_config.get('max_kelly_fraction', 0.25)

    return f"""
You are MarketMan — a tactical ETF strategist focused on identifying high-momentum opportunities in defense, AI, energy, clean tech, and volatility hedging. Your job is to analyze a BATCH of related news items and identify the strongest ETF opportunities.

**CRITICAL OUTPUT FIELDS:**
Return a JSON object with the following fields:
- reasoning: Bullet-pointed, data-driven justification for the signal (no narrative). Format as:
  • [Key data point or insight]
  • [Supporting evidence or flow]
  • [Market context or catalyst]
- if_then_scenario: "If [market/volume/price/flow], then [confirm/refute signal]" logic
- contradictory_signals: Risks, opposing news, or macro factors that could flip the thesis
- uncertainty_metric: "Confidence: X, but…" phrasing, including source/quality/volatility context
- price_anchors: Dict with ETF price context: {{"prev_close": X, "pre_market": Y, "5d_trend": "Z%", "volume": "N"}}
- position_risk_bracket: "Position sizing: conservative / aggressive" based on volatility and risk config
- signal: "Bullish", "Bearish", or "Neutral"
- confidence: 1-10 scale
- affected_etfs: List of relevant ETF tickers
- sector: Primary market sector
- market_impact: Expected market reaction
- risk_factors: Key risks to monitor
- technical_notes: Technical analysis insights
- pattern_notes: Pattern recognition insights

**CONTEXT:**
- ETF price anchors: {price_context}
- Technical indicators: {technical_context}
- Pattern recognition: {pattern_context}
- Multi-source validation: {validation_context}
- News batch: {news_content}
- Risk config: max_position_size_percent={max_position_size_percent}, max_kelly_fraction={max_kelly_fraction}

**BATCH ANALYSIS TASK:**
Analyze this batch of related news items to determine if there's a STRONG, ACTIONABLE ETF opportunity. Output the JSON object as described above.

**EXAMPLES:**
{{
  "relevance": "financial",
  "sector": "Defense",
  "signal": "Bullish",
  "confidence": 7,
  "affected_etfs": ["ITA", "XAR"],
  "reasoning": [
    "Geopolitical tensions driving defense sector flows",
    "Institutional volume in ITA/XAR > 2x average",
    "Reuters, Bloomberg coverage aligns"
  ],
  "if_then_scenario": "If ITA volume > 2x 5-day average this week, confirm bullish thesis; if ceasefire headlines increase, reduce exposure.",
  "contradictory_signals": "Ceasefire progress or defense budget cuts could reverse momentum.",
  "uncertainty_metric": "Confidence 7, but headline-driven and source agreement only moderate.",
  "price_anchors": {{
    "ITA": {{
      "prev_close": 125.80,
      "pre_market": 126.40,
      "5d_trend": "+2.1%",
      "volume": "2.1M (1.8x avg)"
    }},
    "XAR": {{
      "prev_close": 95.30,
      "pre_market": 95.80,
      "5d_trend": "+1.7%",
      "volume": "1.2M (1.5x avg)"
    }}
  }},
  "position_risk_bracket": "Position sizing: conservative (high volatility, sector headline risk)",
  "risk_factors": "...",
  "market_impact": "...",
  "theme_category": "Defense/Aerospace"
}}

**REMEMBER:** 
- Use only bullet points for reasoning.
- Always provide an if/then scenario and contradictory signals.
- Always output the position risk bracket based on volatility and config.
- Always surface the uncertainty metric in trader-friendly language.
- Price anchors must be present for each ETF.
- If any field is not applicable, use an empty string or array, but do not omit it.

Return ONLY the JSON object, nothing else.
"""


def _validate_batch_analysis(analysis_result):
    min_confidence = config_loader.get_setting("min_confidence_threshold", 5)
    min_mentions_for_etf = config_loader.get_setting("min_mentions_for_etf", 2)
    logger.debug(f"🔍 Validating batch analysis: {analysis_result}")
    # If custom_validated, log if we overrule
    if analysis_result.get('custom_validated'):
        # Check if we would reject
        confidence = analysis_result.get("confidence", 0)
        signal = analysis_result.get("signal", "").lower()
        affected_etfs = analysis_result.get("affected_etfs", [])
        tracked_tickers = set(config_loader.get_setting("news_ingestion.tracked_tickers", []))
        if not tracked_tickers:
            specialized_etfs = {
                "BOTZ", "ITA", "ICLN", "URA", "XAR", "DFEN", "PPA", "ROBO", "IRBO", "ARKQ",
                "SMH", "SOXX", "TAN", "QCLN", "PBW", "LIT", "REMX", "URNM", "NLR", "VIXY",
                "VXX", "SQQQ", "SPXS"
            }
        else:
            specialized_etfs = tracked_tickers
        overruling = False
        if confidence < min_confidence:
            overruling = True
        if signal not in ["bullish", "bearish"]:
            overruling = True
        if not any(etf in specialized_etfs for etf in affected_etfs):
            overruling = True
        if overruling:
            logger.warning(f"_validate_batch_analysis is overruling custom rule: {analysis_result.get('custom_reasoning', '')} | signal={signal}, confidence={confidence}, batch_id={analysis_result.get('batch_id', 'N/A')}")
    # Proceed with normal validation
    confidence = analysis_result.get("confidence", 0)
    if confidence < min_confidence:
        logger.info(f"❌ Batch rejected: confidence {confidence} < threshold {min_confidence} (batch_id={analysis_result.get('batch_id', 'N/A')})")
        return False
    signal = analysis_result.get("signal", "").lower()
    if signal not in ["bullish", "bearish"]:
        logger.info(f"❌ Batch rejected: signal type '{signal}' not actionable (batch_id={analysis_result.get('batch_id', 'N/A')})")
        return False
    tracked_tickers = set(config_loader.get_setting("news_ingestion.tracked_tickers", []))
    affected_etfs = analysis_result.get("affected_etfs", [])
    if not tracked_tickers:
        specialized_etfs = {
            "BOTZ", "ITA", "ICLN", "URA", "XAR", "DFEN", "PPA", "ROBO", "IRBO", "ARKQ",
            "SMH", "SOXX", "TAN", "QCLN", "PBW", "LIT", "REMX", "URNM", "NLR", "VIXY",
            "VXX", "SQQQ", "SPXS"
        }
    else:
        specialized_etfs = tracked_tickers
    if not any(etf in specialized_etfs for etf in affected_etfs):
        logger.info(f"❌ Batch rejected: no specialized ETFs in affected_etfs {affected_etfs} (batch_id={analysis_result.get('batch_id', 'N/A')})")
        return False
    if "batch_quality_score" in analysis_result:
        quality_score = analysis_result.get("batch_quality_score", 0)
        min_quality = config_loader.get_setting("news_ingestion.advanced_filtering.min_relevance_score", 0.4)
        if quality_score < min_quality:
            logger.info(f"❌ Batch rejected: quality score {quality_score} < min_quality {min_quality} (batch_id={analysis_result.get('batch_id', 'N/A')})")
            return False
    if "source_quality_assessment" in analysis_result:
        source_assessment = analysis_result.get("source_quality_assessment", "").lower()
        if "unreliable" in source_assessment or "contradictory" in source_assessment:
            logger.info(f"❌ Batch rejected: source quality assessment '{source_assessment}' (batch_id={analysis_result.get('batch_id', 'N/A')})")
            return False
    logger.debug(f"✅ Batch analysis passed all validation checks")
    return True


def _validate_individual_analysis(analysis_result):
    """Validate individual analysis results against configurable rules with quality considerations"""
    # Get configurable thresholds from settings
    min_confidence = config_loader.get_setting("min_confidence_threshold", 7)
    
    # Check confidence threshold (now configurable)
    if analysis_result.get("confidence", 0) < min_confidence:
        logger.debug(f"Individual confidence below threshold: {analysis_result.get('confidence')} < {min_confidence}")
        return False
    
    # Check signal type
    signal = analysis_result.get("signal", "").lower()
    if signal not in ["bullish", "bearish"]:
        logger.debug(f"Individual signal not actionable: {signal}")
        return False
    
    # Check for specialized ETFs (configurable list from tracked_tickers)
    tracked_tickers = set(config_loader.get_setting("news_ingestion.tracked_tickers", []))
    affected_etfs = analysis_result.get("affected_etfs", [])
    
    # If no tracked tickers configured, use default specialized list
    if not tracked_tickers:
        specialized_etfs = {
            "BOTZ", "ITA", "ICLN", "URA", "XAR", "DFEN", "PPA", "ROBO", "IRBO", "ARKQ",
            "SMH", "SOXX", "TAN", "QCLN", "PBW", "LIT", "REMX", "URNM", "NLR", "VIXY",
            "VXX", "SQQQ", "SPXS"
        }
    else:
        specialized_etfs = tracked_tickers
    
    if not any(etf in specialized_etfs for etf in affected_etfs):
        logger.debug(f"Individual analysis contains no specialized ETFs. Affected: {affected_etfs}, Specialized: {specialized_etfs}")
        return False
    
    # Additional quality checks (if individual metadata is available)
    if "analysis_timestamp" in analysis_result:
        analysis_age = (datetime.now() - datetime.fromisoformat(analysis_result["analysis_timestamp"])).days
        if analysis_age > 30:  # Very old analysis
            logger.debug(f"Individual analysis is older than 30 days: {analysis_age} days")
            return False
    
    if "source_headline" in analysis_result:
        headline_length = len(analysis_result["source_headline"])
        if headline_length < 10 or headline_length > 200:  # Very short or very long headline
            logger.debug(f"Individual headline length out of range: {headline_length} characters")
            return False
    
    if "source_summary" in analysis_result:
        summary_length = len(analysis_result["source_summary"])
        if summary_length < 10 or summary_length > 500:  # Very short or very long summary
            logger.debug(f"Individual summary length out of range: {summary_length} characters")
            return False
    
    return True
