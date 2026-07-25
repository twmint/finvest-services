from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from schemas.errors import ProblemDetail
from services.ai_service import AIService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class PortfolioRequest(BaseModel):
    portfolio: list[str] = Field(..., max_length=50)


@router.post("/analyze_portfolio")
@limiter.limit("5/minute")
async def analyze_portfolio(
    request: Request,
    data: PortfolioRequest,
    service: AIService = Depends(AIService),
):
    return service.analyze_portfolio(data.portfolio)


@router.get("/ai_insights")
@limiter.limit("10/minute")
async def generate_ai_insight(request: Request, service: AIService = Depends(AIService)):
    result = service.get_market_insights()
    if result is None:
        return ProblemDetail(title="Bad Gateway", status=502, detail="Failed to fetch AI insights").to_response()
    return result