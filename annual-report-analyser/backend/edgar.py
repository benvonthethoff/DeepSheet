from __future__ import annotations

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


def calculate_derived(financials: dict) -> list[dict]:
    def by_year(concept_key):
        return {
            entry["year"]: entry["val"]
            for entry in financials.get(concept_key, [])
            if entry["val"] is not None
        }

    revenue_by_year = by_year("RevenueFromContractWithCustomerExcludingAssessedTax")
    gross_by_year   = by_year("GrossProfit")
    cfo_by_year     = by_year("NetCashProvidedByUsedInOperatingActivities")
    capex_by_year   = by_year("PaymentsToAcquirePropertyPlantAndEquipment")

    all_years = sorted(
        set(revenue_by_year) | set(gross_by_year) | set(cfo_by_year) | set(capex_by_year)
    )

    rows = []
    prev_revenue = None

    for year in all_years:
        revenue = revenue_by_year.get(year)
        gross   = gross_by_year.get(year)
        cfo     = cfo_by_year.get(year)
        capex   = capex_by_year.get(year)

        fcf = (cfo - capex) if (cfo is not None and capex is not None) else None

        gross_margin_pct = (
            round((gross / revenue) * 100, 1)
            if (gross is not None and revenue and revenue != 0)
            else None
        )

        revenue_growth_pct = (
            round(((revenue - prev_revenue) / abs(prev_revenue)) * 100, 1)
            if (revenue is not None and prev_revenue is not None and prev_revenue != 0)
            else None
        )

        rows.append({
            "year":             year,
            "fcf":              fcf,
            "grossMarginPct":   gross_margin_pct,
            "revenueGrowthPct": revenue_growth_pct,
        })

        if revenue is not None:
            prev_revenue = revenue

    return rows


def fetch_stock_data(ticker: str) -> dict:
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "price":     info.get("currentPrice") or info.get("regularMarketPrice"),
            "marketCap": info.get("marketCap"),
            "peRatio":   info.get("trailingPE"),
            "currency":  info.get("currency", "USD"),
        }
    except Exception as e:
        print(f"[fetch_stock_data] ERROR: {type(e).__name__}: {e}")
        return {
            "price":     None,
            "marketCap": None,
            "peRatio":   None,
            "currency":  None,
        }


def calculate_valuation_ratios(stock_data: dict, derived: list[dict]) -> dict:
    try:
        market_cap = stock_data.get("marketCap")
        pe_ratio = stock_data.get("peRatio")

        # Use most recent year's FCF (last item in derived list)
        most_recent = derived[-1] if derived else {}
        fcf = most_recent.get("fcf")

        price_to_fcf = (
            round(market_cap / fcf, 1)
            if (market_cap and fcf and fcf > 0)
            else None
        )

        return {
            "peRatio":    round(pe_ratio, 1) if pe_ratio else None,
            "priceFCF":   price_to_fcf,
        }
    except Exception as e:
        print(f"[calculate_valuation_ratios] ERROR: {type(e).__name__}: {e}")
        return {
            "peRatio":  None,
            "priceFCF": None,
        }


FILINGS_DIR = "data/filings"

def fetch_filing_urls(cik: str, ticker: str) -> list[dict]:
    cache_key = f"{ticker}_filings"
    cached = cache_get(cache_key)
    if cached:
        return cached

    session = requests.Session()
    session.trust_env = False

    response = session.get(
        f"https://data.sec.gov/submissions/CIK{cik}.json",
        headers={"User-Agent": "DeepSheet benvonai@gmail.com"}
    )
    response.raise_for_status()
    data = response.json()

    filings = data.get("filings", {}).get("recent", {})
    forms        = filings.get("form", [])
    accession_nums = filings.get("accessionNumber", [])
    filing_dates = filings.get("filingDate", [])
    primary_docs = filings.get("primaryDocument", [])

    results = []
    for form, accession, date, doc in zip(forms, accession_nums, filing_dates, primary_docs):
        if form == "10-K":
            accession_clean = accession.replace("-", "")
            url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_clean}/{doc}"
            results.append({
                "year":        date[:4],
                "filingDate":  date,
                "url":         url,
                "accession":   accession,
            })
        if len(results) == 5:
            break

    cache_set(cache_key, results)
    return results
