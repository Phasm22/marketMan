"""
Alternative AI Provider: DeepSeek Integration
Replace the analyze_energy_news function with this version to use DeepSeek instead of OpenAI
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def analyze_energy_news_deepseek(headline, summary, snippet=""):
    """
    Analyze energy news using DeepSeek API instead of OpenAI
    """
    prompt = f"""
You're a financial AI assistant for energy sector signals.

Article Title: "{headline}"
Summary: "{summary}"
Snippet: "{snippet}"

Analyze this news for energy sector trading signals and respond in JSON format:

{{
    "signal": "Bullish|Bearish|Neutral",
    "confidence": 1-10,
    "affected_etfs": ["XLE", "ICLN", "TAN"] (choose relevant ones),
    "reasoning": "One-sentence explanation of your analysis",
    "market_impact": "Short description of potential market impact"
}}

Focus on energy companies, renewable energy, oil & gas, solar, wind, and related infrastructure.
"""

    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
        
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 500
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"DeepSeek API error: {response.status_code} - {response.text}")
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Try to parse as JSON
        try:
            json_result = json.loads(content)
            return json_result
        except json.JSONDecodeError:
            # Fallback: return raw text if JSON parsing fails
            logger.warning("Failed to parse DeepSeek response as JSON, returning raw text")
            return {"raw_response": content}
            
    except Exception as e:
        logger.error(f"Error calling DeepSeek API: {e}")
        return None

# To use DeepSeek instead of OpenAI:
# 1. Add these to your .env file:
#    DEEPSEEK_API_KEY=your-deepseek-api-key
#    DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
#
# 2. Replace the analyze_energy_news function call in news_gpt_analyzer.py:
#    analysis = analyze_energy_news_deepseek(
#        article['title'], 
#        article['snippet'], 
#        article['snippet']
#    )
