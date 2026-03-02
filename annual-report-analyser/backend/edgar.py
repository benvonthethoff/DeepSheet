from __future__ import annotations

import json
import os
import re
import requests
import time

from bs4 import BeautifulSoup

from storage import cache_get, cache_set, CACHE_DIR, DATA_DIR, FILINGS_DIR

COMPANY_TICKERS_PATH = f"{DATA_DIR}/company_tickers.json"


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
    print(f"[fetch_concept] checking cache for {cache_key}")
    data = cache_get(cache_key)
    print(f"[fetch_concept] cache hit: {data is not None}")

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


def download_filing(ticker: str, year: str, url: str) -> str | None:
    save_dir = f"{FILINGS_DIR}/{ticker.upper()}"
    save_path = f"{save_dir}/{year}_10k.html"

    if os.path.exists(save_path):
        print(f"[download_filing] Already exists, skipping: {save_path}")
        return save_path

    os.makedirs(save_dir, exist_ok=True)

    try:
        session = requests.Session()
        session.trust_env = False
        print(f"[download_filing] Downloading {ticker} {year} from {url}")
        response = session.get(
            url,
            headers={"User-Agent": "DeepSheet benvonai@gmail.com"}
        )
        response.raise_for_status()

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(response.text)

        print(f"[download_filing] Saved to {save_path}")
        time.sleep(0.5)
        return save_path

    except Exception as e:
        print(f"[download_filing] ERROR {ticker} {year}: {type(e).__name__}: {e}")
        return None


def download_all_filings(ticker: str, filings: list[dict]) -> list[dict]:
    results = []
    for filing in filings:
        path = download_filing(ticker, filing["year"], filing["url"])
        results.append({**filing, "localPath": path})
    return results


TOKEN_LIMITS = {
    "item1":  2000,
    "item1a": 3000,
    "item7":  8000,
}
AVG_CHARS_PER_TOKEN = 4

def extract_sections(local_path: str) -> dict:
    """
    Opens a saved 10-K HTML file and extracts text from
    Item 1, Item 1A, and Item 7. Trims each to its token limit.
    """
    try:
        with open(local_path, "r", encoding="utf-8") as f:
            html = f.read()

        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ")
        text = re.sub(r'\s+', ' ', text).strip()

        def extract_between(text: str, start_pattern: str, end_pattern: str, max_tokens: int) -> str | None:
            # Find all matches — first is TOC, second is actual content
            matches = list(re.finditer(start_pattern, text, re.IGNORECASE))
            if len(matches) < 2:
                # Fallback to first match if no TOC present
                match = matches[0] if matches else None
            else:
                match = matches[1]

            if not match:
                return None

            start_pos = match.end()
            end_match = re.search(end_pattern, text[start_pos:], re.IGNORECASE)

            if not end_match:
                section = text[start_pos:start_pos + max_tokens * AVG_CHARS_PER_TOKEN]
            else:
                section = text[start_pos:start_pos + end_match.start()]

            max_chars = max_tokens * AVG_CHARS_PER_TOKEN
            return section[:max_chars].strip()

        item1 = extract_between(
            text,
            r'Item\s+1[\.\s]+Business',
            r'Item\s+1A[\.\s]+Risk Factors',
            TOKEN_LIMITS["item1"]
        )
        item1a = extract_between(
            text,
            r'Item\s+1A[\.\s]+Risk Factors',
            r'Item\s+1B[\.\s]+',
            TOKEN_LIMITS["item1a"]
        )
        item7 = extract_between(
            text,
            r'Item\s+7[\.\s]+Management',
            r'Item\s+7A[\.\s]+',
            TOKEN_LIMITS["item7"]
        )

        return {
            "item1":  item1,
            "item1a": item1a,
            "item7":  item7,
        }

    except Exception as e:
        print(f"[extract_sections] ERROR {local_path}: {type(e).__name__}: {e}")
        return {
            "item1":  None,
            "item1a": None,
            "item7":  None,
        }


def extract_all_sections(filings: list[dict]) -> list[dict]:
    """
    Runs extract_sections on each filing that has a valid localPath.
    Returns the filings list with a 'sections' field added to each.
    """
    results = []
    for filing in filings:
        local_path = filing.get("localPath")
        if local_path and os.path.exists(local_path):
            sections = extract_sections(local_path)
        else:
            sections = {"item1": None, "item1a": None, "item7": None}
        results.append({**filing, "sections": sections})
    return results
