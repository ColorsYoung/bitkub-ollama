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
        [CONTEXT: QUANTITATIVE TRADING ANALYSIS]
        TIME INTERVAL: 5-MINUTE (M5)
        STRATEGY: SCALPING & QUICK MOMENTUM
        
        [MARKET DATA INPUT]
        {market_summary}

        [ANALYSIS PROTOCOL]
        1. TREND IDENTIFICATION:
           - BULLISH: Price > EMA 9 > EMA 21.
           - BEARISH: Price < EMA 9 < EMA 21.
           - CONSOLIDATION: Price oscillating between EMA 9 and EMA 21.

        2. MOMENTUM VERIFICATION (MACD):
           - STRONG BULLISH: MACD > Signal AND Histogram is positive and expanding.
           - BULLISH EXHAUSTION: MACD > Signal BUT Histogram is shrinking.
           - BEARISH REVERSAL: MACD crosses below Signal.

        3. VOLUME & PRICE ACTION:
           - VALIDATION: Price moves must be backed by 'High' Volume Status.
           - DIVERGENCE: Check if RSI is making lower highs while Price makes higher highs (Warning).

        4. RISK ASSESSMENT:
           - OVERBOUGHT: RSI > 70 (Exercise caution for BUY).
           - OVERSOLD: RSI < 30 (Exercise caution for SELL).
           - OVEREXTENDED: Price is > 1% away from EMA 21 (Reversion risk for M5).

        [DECISION MATRIX]
        - ACTION "BUY": 
            - Trend Status is UP + MACD Bullish Crossover + Current Price > EMA 9.
            - OR: Quick reversal confirmed by High Volume and positive Histogram.
        - ACTION "SELL":
            - Trend Status is DOWN + MACD Bearish Crossover + Current Price < EMA 9.
            - EMERGENCY EXIT: Price breaks below EMA 21 or MACD Bearish Cross happens while Trend is UP (Lock profits/Minimize loss).
            - OR: RSI > 75 with shrinking Histogram.
        - ACTION "HOLD":
            - Low Volume + Neutral MACD.
            - Price is overlapping EMA 9 and 21.

        [OUTPUT SPECIFICATION]
        - You must output ONLY a valid JSON object.
        - confidence_score: (0-100). Assign >= 80 ONLY if multiple factors (Trend + Momentum + Volume) align perfectly.
        - reasoning: Concise technical justification (max 12 words).

        {{
            "action": "BUY/SELL/HOLD",
            "confidence_score": integer,
            "reasoning": "string"
        }}
        """

        try:
            payload = {
                "model": self.model,
                "system": "You are a highly conservative Scalping Specialist. You only take high-probability trades where at least 3 indicators align. You are precise and refuse to guess. If signals are mixed, assign a low confidence score and recommend HOLD.",
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