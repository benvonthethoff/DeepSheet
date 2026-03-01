import os
os.environ["no_proxy"] = "*"

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from edgar import resolve_cik, fetch_financials, calculate_derived, fetch_stock_data, calculate_valuation_ratios, fetch_filing_urls, download_all_filings, extract_all_sections

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "running"}


@app.get("/resolve-cik")
async def get_cik(ticker: str):
    try:
        cik = resolve_cik(ticker)
        return {"ticker": ticker, "cik": cik}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/financials")
async def get_financials(ticker: str):
    try:
        cik = resolve_cik(ticker)
        data = fetch_financials(cik, ticker)
        data["derived"] = calculate_derived(data)
        data["stockData"] = fetch_stock_data(ticker)
        data["valuationRatios"] = calculate_valuation_ratios(data["stockData"], data["derived"])
        data["filings"] = fetch_filing_urls(cik, ticker)
        data["filings"] = download_all_filings(ticker, data["filings"])
        data["filings"] = extract_all_sections(data["filings"])
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
