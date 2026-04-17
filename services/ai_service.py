import os

import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class AIService:
    def get_market_insights(self) -> str | None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None

        headers = {"Authorization": f"Bearer {api_key}"}
        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "You are a financial analyst."},
                {
                    "role": "user",
                    "content": "Give me a short professional insight on the current market sentiment for the top 3 stocks from NASDAQ.",
                },
            ],
        }

        try:
            response = requests.post(GROQ_URL, headers=headers, json=data, timeout=15)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except (requests.exceptions.RequestException, KeyError, IndexError):
            return None

    def analyze_portfolio(self, tickers: list[str]) -> dict:
        sanitized = [t.strip()[:10] for t in tickers]
        # TODO: implement real portfolio analysis via Groq
        return {"analysis": "stub", "tickers": sanitized}