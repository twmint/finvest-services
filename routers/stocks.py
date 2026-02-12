import re
import requests
import numpy as np
import pandas as pd
from fastapi import APIRouter
from bs4 import BeautifulSoup
from yahooquery import Ticker

router = APIRouter()

tickers = ["A", "AL", "AAP", "AAPL", "GOOGL", "ZBRA", "ZION", "ZTS"]

@router.get("/favourites")
def get_stock():
    ticker_info = {}
    all_symbols = " ".join(tickers)
    myInfo = Ticker(all_symbols, asynchronous=True, progress=True)
    myDict = myInfo.price

    for ticker in tickers:
        ticker = str(ticker)
        price = myDict[ticker]['regularMarketPrice']
        market_cap = myDict[ticker]['marketCap']
        ticker_info[ticker] = {
            "price": price,
            "marketCap": market_cap
        }
    return(ticker_info)

@router.get("/history")
def get_stock_history():
    ticker = Ticker(tickers, asynchronous=True, progress=True)
    hist = ticker.history(period="1mo", interval="1wk").reset_index()
    hist['date'] = pd.to_datetime(hist['date'], utc=True).dt.tz_localize(None)
    hist['date'] = hist['date'].dt.date
    hist["close"] = np.round(hist["close"], 2)
    hist = hist.pivot(index="date", columns="symbol", values="close").fillna(0.00).reset_index()
    result = hist.to_dict(orient="records")
    return result

@router.get("/gainers")
def get_gainers():
    url = "https://finance.yahoo.com/gainers"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    assets = soup.find_all('a', attrs={"class":"Fw(600)"})
    gainers = []

    # for asset in assets[:10]:
    #     symbol = asset.text
    #     link = "https://finance.yahoo.com" + asset['href']
    #     gainers.append({"symbol": symbol, "link": link})
    #     print(symbol, link)
    print(assets)
    return gainers

@router.get("/indices/{region}")
def extract_indices(region: str):
    url = "https://finance.yahoo.com/markets/"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, "html.parser")
    region_data = {}
    region_section = soup.find("h3", string=lambda text: text and text.casefold() == region.casefold())
    if region_section:
        table = region_section.find_next("table")
        for row in table.find_all("tr")[1:]:
            columns = row.find_all("td")
            if len(columns) >= 3:
                symbol = columns[0].get_text(strip=True)
                price = columns[2].get_text(strip=True)
                change = columns[3].get_text(strip=True)

                formatted_price = re.sub(r'\([^)]*\)', '', price)
                match = re.match(r'([\d,\.]+)([+-])([\d,\.]+)', formatted_price)
                if match:
                    base_price, operator, change_amount = match.groups()
                    region_data[symbol] = {
                        "price": base_price,
                        "trend": operator,
                        "priceChange": change_amount,
                        "percentChange": change
                    }
    return region_data