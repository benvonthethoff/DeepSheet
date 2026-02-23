import json
import os

import requests

CACHE_DIR = "cache"
DATA_DIR = "data"
COMPANY_TICKERS_PATH = f"{DATA_DIR}/company_tickers.json"


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
    data = None
    if os.path.exists(COMPANY_TICKERS_PATH):
        with open(COMPANY_TICKERS_PATH, "r") as f:
            data = json.load(f)

    if data is None:
        session = requests.Session()
        session.trust_env = False

        response = session.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers={"User-Agent": "DeepSheet benvonai@gmail.com"}
        )
        response.raise_for_status()
        data = response.json()

        os.makedirs(DATA_DIR, exist_ok=True)
        with open(COMPANY_TICKERS_PATH, "w") as f:
            json.dump(data, f)

    ticker_upper = ticker.upper()
    for entry in data.values():
        if entry["ticker"].upper() == ticker_upper:
            return str(entry["cik_str"]).zfill(10)

    raise ValueError("Ticker not found")


def fetch_concept(cik: str, ticker: str, concept: str) -> dict:
    cache_key = f"{ticker}_concept_{concept}"
    data = cache_get(cache_key)

    if data is None:
        session = requests.Session()
        session.trust_env = False

        response = session.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json",
            headers={"User-Agent": "DeepSheet benvonai@gmail.com"}
        )
        response.raise_for_status()
        data = response.json()
        cache_set(cache_key, data)

    return data


FINANCIAL_CONCEPTS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "GrossProfit",
    "NetIncomeLoss",
    "NetCashProvidedByUsedInOperatingActivities",
    "PaymentsToAcquirePropertyPlantAndEquipment",
]


def fetch_financials(cik: str, ticker: str) -> dict:
    results = {}

    for concept in FINANCIAL_CONCEPTS:
        try:
            data = fetch_concept(cik, ticker, concept)
            units = data.get("units", {})
            values = units.get("USD", [])

            annual_values = [
                v for v in values
                if v.get("form") == "10-K" and v.get("fp") == "FY"
            ]

            by_year = {}
            for v in annual_values:
                end_date = v.get("end", "")
                if not end_date:
                    continue
                year = int(end_date[:4])
                filed = v.get("filed", "")
                if year not in by_year or filed > by_year[year]["filed"]:
                    by_year[year] = {"year": year, "val": v.get("val"), "filed": filed}

            sorted_years = sorted(by_year.keys(), reverse=True)[:5]
            results[concept] = [
                {"year": by_year[y]["year"], "val": by_year[y]["val"]}
                for y in sorted(sorted_years)
            ]
        except Exception:
            results[concept] = []

    return results
