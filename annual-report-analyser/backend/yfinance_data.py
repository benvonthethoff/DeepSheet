from datetime import datetime
from storage import load_permanent, save_permanent


def fetch_stock_data(ticker: str) -> dict:
    print(f"[fetch_stock_data] called for {ticker}")

    cached = load_permanent(ticker, "stock_data.json")
    print(f"[fetch_stock_data] cache result: {cached}")

    if cached:
        print(f"[fetch_stock_data] returning cached data")
        return cached

    print(f"[fetch_stock_data] fetching live from yfinance")
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        result = {
            "price":       info.get("last_price"),
            "marketCap":   info.get("market_cap"),
            "peRatio":     None,
            "currency":    info.get("currency", "USD"),
            "lastUpdated": datetime.utcnow().isoformat(),
        }
        print(f"[fetch_stock_data] yfinance result: {result}")
        save_permanent(ticker, "stock_data.json", result)
        print(f"[fetch_stock_data] saved to disk")
        return result
    except Exception as e:
        print(f"[fetch_stock_data] ERROR: {type(e).__name__}: {e}")
        return {
            "price":     None,
            "marketCap": None,
            "peRatio":   None,
            "currency":  None,
        }
