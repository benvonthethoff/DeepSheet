import json
import os

import requests

CACHE_DIR = "cache"


def cache_get(key: str):
    path = f"{CACHE_DIR}/{key}.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None


def cache_set(key: str, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = f"{CACHE_DIR}/{key}.json"
    with open(path, "w") as f:
        json.dump(data, f)


def resolve_cik(ticker: str) -> str:
    data = cache_get("company_tickers")

    if data is None:
        session = requests.Session()
        session.trust_env = False

        response = session.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers={"User-Agent": "DeepSheet benvonai@gmail.com"}
        )
        response.raise_for_status()
        data = response.json()
        cache_set("company_tickers", data)

    ticker_upper = ticker.upper()
    for entry in data.values():
        if entry["ticker"].upper() == ticker_upper:
            return str(entry["cik_str"]).zfill(10)

    raise ValueError("Ticker not found")
