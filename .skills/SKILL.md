# Bitkub Trading Bot Skills 🤖

In addition to the custom skills folder, Antigravity will search the following paths in order to find skills for the agent:
- `/Users/num/Documents/trading-ollama/.skills`
- `/Users/num/.gemini/antigravity/custom_skills`

---

## 🛠️ Project Development Rules

### 1. Technology Stack
- **Language**: Python 3.10+
- **API**: Bitkub API v3 (Signature SHA256)
- **AI Engine**: Local Ollama (Llama 3.1/3.2)
- **Indicators**: `pandas_ta` (RSI, EMA, MACD)

### 2. Coding Standards
- Use Type Hinting in Python.
- Log all API calls and decision outcomes to `bot.log`.
- Keep API Keys in `.env` only.

### 3. Trading Strategy Focus
- Prioritize Momentum and MACD trend indicators for 1-hour timeframe.
- Ensure all trade executions check for sufficient balance first.
- Handle API errors gracefully with retries or error logging.

---

## 📋 Instruction Manual
This file serves as a guide for the Antigravity agent to understand the project structure and best practices. Always refer to this file when making architectural decisions or adding new features.
