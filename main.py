from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from routers import stocks
from routers import ai_analysis
from wsockets import stock_market as ws_stocks

app = FastAPI()

origins = ["http://localhost:3000",
           "http://192.168.100.5:3000"
          ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(stocks.router, prefix="/stocks")
api_router.include_router(ai_analysis.router, prefix="/ai")

ws_router = APIRouter()
ws_router.include_router(ws_stocks.router)

app.include_router(api_router)
app.include_router(ws_router)
