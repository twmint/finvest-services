import os
import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

load_dotenv()
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

class PortfolioRequest(BaseModel):
    portfolio: list[str] = Field(..., max_length=50)

@router.post("/analyze_portfolio")
@limiter.limit("5/minute")
async def analyze_portfolio(request: Request, data: PortfolioRequest):
    sanitized = [ticker.strip()[:10] for ticker in data.portfolio]
    prompt = f"Analyze this portfolio and suggest diversification: {', '.join(sanitized)}"
    #response = call_openai_api(prompt)
    return {"analysis": 'hi'}


@router.get("/ai_insights")
@limiter.limit("10/minute")
async def generate_ai_insight(request: Request):
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You are a financial analyst."},
            {
                "role": "user",
                "content": "Give me a short professional insight on the current market sentiment for the top 3 stocks from NASDAQ."
            },
        ],
    }
    try:
        response = requests.post(GROQ_URL, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=502, detail="Failed to fetch AI insights")
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail="Unexpected response from AI service")
