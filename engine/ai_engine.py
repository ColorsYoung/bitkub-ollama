import requests
import json
import logging
import os

class AIEngine:
    def __init__(self, ollama_url, model=None, timeout=30, temperature=0.2, top_p=0.9, num_predict=256):
        self.url = f"{ollama_url}/api/generate"
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
        self.timeout = timeout
        self.temperature = temperature
        self.top_p = top_p
        self.num_predict = num_predict
        self.logger = logging.getLogger(__name__)

    def get_decision(self, market_summary: str) -> dict:
        if not market_summary:
            raise ValueError("market_summary is empty or None")
            
        prompt = f"""
        Market Data Input:
        {market_summary}

        Analysis Strategy:
        1. Trend Analysis: Check if Current Price > EMA 9 > EMA 21 (Strong Uptrend) or Price < EMA 9 < EMA 21 (Strong Downtrend).
        2. Momentum: RSI < 30 is deep oversold (Buy potential), RSI > 70 is overbought (Sell potential). RSI crossing 50 indicates momentum shift.
        3. Convergence: Look for MACD crossing the Signal line. A positive histogram growth confirms bullish strength.
        4. Volatility: Compare Price Change with EMAs to see if the move is a breakout or just noise.

        Decision Rules:
        - BUY: Only if at least 2 indicators show bullish reversal (e.g., RSI rising from 30 + MACD Bullish Cross).
        - SELL: Only if trend breaks (Price below EMA 21) or RSI is exhausted (>70).
        - HOLD: If signals are conflicting or momentum is neutral (RSI between 40-60).
        - If any indicator value is missing, unavailable, or cannot be calculated, default action must be HOLD with a confidence_score below 30.

        Requirement:
        - Respond ONLY in valid JSON.
        - confidence_score must be 0-100.
        - reasoning must explain the 'Why' based on the indicators above.
        - reasoning must be a single concise sentence, no longer than 50 words.

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
                "system": "You are a Senior Quantitative Crypto Trader. Analyze the market data for BTC/THB and provide a high-probability trade signal.",
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "num_predict": self.num_predict
                }
            }
            response = requests.post(self.url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            decision_text = result.get("response", "")
            
            try:
                decision = json.loads(decision_text)
            except json.JSONDecodeError:
                self.logger.error(f"Failed to parse JSON decision. Raw text: {decision_text}")
                return {"action": "HOLD", "confidence_score": 0, "reasoning": "Failed to parse AI response."}

            # Validation
            action = str(decision.get("action", "")).upper()
            confidence = decision.get("confidence_score")
            reasoning = decision.get("reasoning", "")

            if action not in ["BUY", "SELL", "HOLD"] or not isinstance(confidence, int) or not (0 <= confidence <= 100):
                self.logger.warning(f"Invalid AI response format: {decision}")
                return {"action": "HOLD", "confidence_score": 0, "reasoning": "AI returned invalid response format or values."}

            self.logger.info(f"AI Decision: {action} (Confidence: {confidence}%) - Reasoning: {reasoning}")
            return decision

        except Exception as e:
            self.logger.error(f"Error calling Ollama: {e}")
            return {"action": "HOLD", "confidence_score": 0, "reasoning": f"AI Engine Error: {str(e)}"}