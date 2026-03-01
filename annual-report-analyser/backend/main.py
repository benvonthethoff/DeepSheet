import dotenv
dotenv.load_dotenv()

import os
os.environ["no_proxy"] = "*"

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from edgar import resolve_cik, fetch_financials, calculate_derived, fetch_stock_data, calculate_valuation_ratios, fetch_filing_urls, download_all_filings, extract_all_sections
from financials import run_rules_engine
from ai import generate_all_quant_narratives, generate_all_qual_narratives, generate_all_risk_narratives, generate_quant_trend, generate_qual_trend, generate_risk_trend, generate_deep_value

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
        data["signals"] = run_rules_engine(data["derived"], data)
        data["quantAnalysis"] = generate_all_quant_narratives(ticker, data["derived"], data["signals"])
        data["qualAnalysis"] = generate_all_qual_narratives(ticker, data["filings"])
        data["riskAnalysis"] = generate_all_risk_narratives(ticker, data["filings"])
        data["quantTrend"] = generate_quant_trend(ticker, data["quantAnalysis"], data["signals"])
        data["qualTrend"] = generate_qual_trend(ticker, data["qualAnalysis"])
        data["riskTrend"] = generate_risk_trend(ticker, data["riskAnalysis"])
        data["deepValue"] = generate_deep_value(
            ticker,
            data["quantTrend"],
            data["qualTrend"],
            data["riskTrend"],
            data["valuationRatios"],
            data["stockData"]
        )
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
