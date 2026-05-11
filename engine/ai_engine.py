import requests
import json
import logging
import os

class AIEngine:
    def __init__(self, ollama_url, model=None, timeout=30, temperature=0.6, top_p=0.9, num_predict=256):
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
        Market Data Input (1-HOUR TIMEFRAME):
        {market_summary}

        Active Trading Strategy for 1h Timeframe:
        1. Trend Following: If Trend Status is UP, prioritize BUY entries.
        2. Momentum: If MACD is above Signal and Histogram is increasing, momentum is strong.
        3. Price Action: If Current Price > EMA 9 and Trend is UP, the trend is aggressive.
        4. RSI Context: Use RSI only as a warning. RSI > 75 is overbought (risk), but RSI 50-65 is normal in a strong trend.

        Decision Rules:
        - BUY: 
            a) Trend is UP + MACD is Bullish + Current Price > EMA 9 (Ride the wave).
            b) Trend is UP + RSI is 40-55 (Buy the dip).
            c) Trend is DOWN -> UP reversal confirmed by MACD Cross + Volume.
        - SELL:
            a) Trend is UP -> DOWN shift (Trend break).
            b) Trend is UP + RSI > 75 + MACD Bearish Cross (Take profit).
            c) Current Price < EMA 21 in any trend (Risk management).
        - HOLD: 
            - Sideways movement (Price between EMA 9 and EMA 21).
            - Very low Volume and no MACD direction.

        Requirement:
        - Respond ONLY in valid JSON.
        - confidence_score must be 0-100.
        - reasoning must be a single concise sentence.

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
                "system": "You are a Momentum-focused 1-hour Swing Trader. Your goal is to capture trends and ride momentum. You prioritize MACD and Price relative to EMAs. You are decisive and less conservative than a daily trader.",
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