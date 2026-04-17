import random
import re
from datetime import datetime, timedelta, timezone

from yahooquery import Ticker, Screener

from constants import NEWS_PUBLISHERS, WATCHLIST_TICKERS
from scrapers.base import Scraper
from utils.quotes import normalize_quotes, safe_quotes


class MarketDataService:
    def get_favourites(self) -> dict[str, dict]:
        try:
            all_symbols = " ".join(WATCHLIST_TICKERS)
            info = Ticker(all_symbols, asynchronous=True, progress=True).price
            return {
                str(ticker): {
                    "price": info.get(str(ticker), {}).get("regularMarketPrice"),
                    "marketCap": info.get(str(ticker), {}).get("marketCap")
                }
                for ticker in WATCHLIST_TICKERS
            }
        except Exception as e:
            print(f"Error fetching favourites: {e}")
            return {}

    def get_market_movers(self) -> dict[str, list[dict]]:
        try:
            s = Screener()
            data = s.get_screeners(["day_gainers", "day_losers", "most_actives"], 5)
            return {
                "gainers": normalize_quotes(safe_quotes(data, "day_gainers")),
                "losers": normalize_quotes(safe_quotes(data, "day_losers")),
                "actives": normalize_quotes(safe_quotes(data, "most_actives"), include_volume=True)
            }
        except Exception as e:
            print(f"Error fetching market movers: {e}")
            return {}

    def get_indices(self, regions: list[str] | None = None) -> dict[str, dict]:
        data = {}
        regions = regions or ["Americas", "Europe", "Asia"]
        scraper = Scraper()
        soup = scraper.get_soup("https://finance.yahoo.com/markets/")
        if soup is None:
            return data

        for region in regions:
            region_section = soup.find("h3", string=lambda text: text and text.casefold() == region.casefold())
            if not region_section:
                continue
            table = region_section.find_next("table")
            if not table:
                continue
            region_data = {}
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
            data[region] = region_data
        return data

    def get_news(self) -> dict[int, dict]:
        data = {}
        scraper = Scraper()
        soup = scraper.get_soup("https://finance.yahoo.com/topic/economic-news/")
        if soup is None:
            return data
        featured = soup.find("section", {"class": "topic-featured"})
        if not featured:
            return data
        news_list = featured.find("div", {"class": "story-list"})
        if not news_list:
            return data

        now = int(datetime.now(timezone.utc).timestamp())
        yesterday = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp())

        for idx, news in enumerate(news_list, start=1):
            try:
                link = news.find("a", {"class": "subtle-link"})
                if not link:
                    continue
                title_elem = news.find("h3", {"class": "clamp"})
                summary_elem = news.find("p", {"class": "clamp"})
                img = news.find("img")
                data[idx] = {
                    "id": idx,
                    "title": title_elem.get_text(strip=True) if title_elem else "No title",
                    "summary": summary_elem.get_text(strip=True) if summary_elem else "",
                    "url": link.get("href", ""),
                    "provider": NEWS_PUBLISHERS[idx % len(NEWS_PUBLISHERS)],
                    "time": random.randint(yesterday, now),
                    "image": img.get("src", "") if img else ""
                }
            except Exception as e:
                print(f"Error parsing news item {idx}: {e}")
                continue
        return data