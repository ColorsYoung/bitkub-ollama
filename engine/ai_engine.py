import requests
import json
import logging

class AIEngine:
    def __init__(self, ollama_url, model="llama3.1:8b"):
        self.url = f"{ollama_url}/api/generate"
        self.model = model
        self.logger = logging.getLogger(__name__)

    def get_decision(self, market_summary):
        prompt = f"""
        System: You are a Senior Quantitative Crypto Trader. Analyze the market data for BTC/THB and provide a high-probability trade signal.

        Market Data Input:
        {market_summary}

        Analysis Strategy:
        1. Trend Analysis: Check if Current Price > EMA 9 > EMA 21 (Strong Uptrend) or Price < EMA 9 < EMA 21 (Strong Downtrend).
        2. Momentum: RSI < 30 is deep oversold (Buy potential), RSI > 70 is overbought (Sell potential). RSI crossing 50 indicates momentum shift.
        3. Convergence: Look for MACD crossing the Signal line. A positive histogram growth confirms bullish strength.
        4. Volatility: Compare Price Change with EMAs to see if the move is a breakout or just noise.

        Decision Rules:
        - BUY: Only if at least 2 indicators show bullish reversal (e.g., RSI rising from 30 + MACD Bullish Cross).
        - SELL: Only if trend breaks (Price below EMA 21) or RSI is exhausted (>75).
        - HOLD: If signals are conflicting or momentum is neutral (RSI between 40-60).

        Requirement:
        - Respond ONLY in valid JSON.
        - confidence_score must be 0-100.
        - reasoning must explain the 'Why' based on the indicators above.

        Response Format:
        {{
            "action": "BUY/SELL/HOLD",
            "confidence_score": integer,
            "reasoning": "string"
        }}
        """

        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.2,  # ลดความเพ้อ ให้ AI ตัดสินใจบนพื้นฐานข้อมูลจริงมากขึ้น
                    "top_p": 0.9,
                    "num_predict": 256    # จำกัดความยาวการตอบเพื่อความเร็ว
                }
            }
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            decision_text = result.get("response", "")
            decision = json.loads(decision_text)
            
            return decision
        except Exception as e:
            self.logger.error(f"Error calling Ollama: {e}")
            return {"action": "HOLD", "confidence_score": 0, "reasoning": f"AI Engine Error: {str(e)}"}