import os
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, APIRouter, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from routers import auth, stocks, ai_analysis, ticker, orders
from utils.security import get_current_user, InvalidSessionException
from wsockets import stock_market as ws_stocks

load_dotenv()

limiter = Limiter(key_func=get_remote_address)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' https:; script-src 'self'; style-src 'self' 'unsafe-inline'"
        return response

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(InvalidSessionException)
async def invalid_session_handler(_request: Request, exc: InvalidSessionException):
    response = JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")]
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

api_router = APIRouter(prefix="/api/v1")

protected = {"dependencies": [Depends(get_current_user)]}

api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(stocks.router, prefix="/stocks", **protected)
api_router.include_router(ai_analysis.router, prefix="/ai", **protected)
api_router.include_router(ticker.router, prefix="/ticker", **protected)
api_router.include_router(orders.router, prefix="/orders", **protected)

ws_router = APIRouter()
ws_router.include_router(ws_stocks.router)

app.include_router(api_router)
app.include_router(ws_router)
