import os
import requests
from dotenv import load_dotenv
from fastapi import APIRouter

load_dotenv()
router = APIRouter()

@router.post("/analyze_portfolio")
async def analyze_portfolio(data: dict):
    portfolio = data.get("portfolio")
    prompt = f"Analyze this portfolio and suggest diversification: {portfolio}"
    #response = call_openai_api(prompt)
    return {"analysis": 'hi'}


@router.get("/ai_insights")
async def generate_ai_insight():
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You are a financial analyst."},
            {
                "role": "user",
                "content": f"Give me a short professional insight on the current market sentiment for the top 3 stocks from NASDAQ."
            },
        ],
    }
    response = requests.post(GROQ_URL, headers=headers, json=data)
    result = response.json()
    print(result)
    return result["choices"][0]["message"]["content"]

