import os
import json
from anthropic import Anthropic
from storage import load_permanent, save_permanent

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def load_prompt(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "prompts", filename)
    with open(path, "r") as f:
        return f.read()

def generate_quant_narrative(ticker: str, year: int, year_data: dict, signals: dict) -> dict:
    filename = f"{year}_quant.json"
    existing = load_permanent(ticker, filename)
    if existing:
        print(f"[generate_quant_narrative] Using saved file for {ticker} {year}")
        return existing

    print(f"[generate_quant_narrative] Calling Claude for {ticker} {year}")

    year_signals = {
        "revenueSignals": next((s for s in signals["revenueSignals"] if s["year"] == year), {}),
        "marginSignals": next((s for s in signals["marginSignals"] if s["year"] == year), {}),
        "fcfSignals": next((s for s in signals["fcfSignals"] if s["year"] == year), {}),
        "earningsQualitySignals": next((s for s in signals["earningsQualitySignals"] if s["year"] == year), {}),
    }

    fcf_billions = round(year_data.get("fcf", 0) / 1e9, 1) if year_data.get("fcf") else None
    net_income_billions = round(year_data.get("netIncome", 0) / 1e9, 1) if year_data.get("netIncome") else None

    system_prompt = load_prompt("quant_system.txt")
    user_prompt = load_prompt("quant_user.txt").format(
        ticker=ticker,
        year=year,
        revenue_growth=year_data.get("revenueGrowthPct", "N/A"),
        gross_margin=year_data.get("grossMarginPct", "N/A"),
        fcf_billions=fcf_billions,
        net_income_billions=net_income_billions,
        signals_json=json.dumps(year_signals, indent=2),
        five_year_json=json.dumps(signals.get("fiveYearTrend", {}), indent=2)
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        raw = response.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        result = json.loads(raw)
        save_permanent(ticker, filename, result)
        return result
    except Exception as e:
        print(f"[generate_quant_narrative] ERROR: {type(e).__name__}: {e}")
        print(f"[generate_quant_narrative] Prompt length: {len(user_prompt)} chars")
        print(f"[generate_quant_narrative] System length: {len(system_prompt)} chars")
        raise


def generate_all_quant_narratives(ticker: str, derived: list[dict], signals: dict) -> list[dict]:
    results = []
    for year_data in derived:
        year = year_data["year"]
        result = generate_quant_narrative(ticker, year, year_data, signals)
        results.append(result)
    return results


def generate_qual_narrative(ticker: str, year: int, item7_text: str) -> dict:
    filename = f"{year}_qual.json"
    existing = load_permanent(ticker, filename)
    if existing:
        print(f"[generate_qual_narrative] Using saved file for {ticker} {year}")
        return existing

    if not item7_text:
        print(f"[generate_qual_narrative] No Item 7 text for {ticker} {year}")
        return {"year": year, "ticker": ticker, "error": "No Item 7 text available"}

    print(f"[generate_qual_narrative] Calling Claude for {ticker} {year}")

    system_prompt = load_prompt("qual_system.txt")
    user_prompt = load_prompt("qual_user.txt").format(
        ticker=ticker,
        year=year,
        item7_text=item7_text
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
    save_permanent(ticker, filename, result)
    return result


def generate_all_qual_narratives(ticker: str, filings: list[dict]) -> list[dict]:
    results = []
    for filing in filings:
        year = filing["year"]
        item7 = filing.get("sections", {}).get("item7")
        result = generate_qual_narrative(ticker, int(year), item7)
        results.append(result)
    return results


def generate_risk_narrative(ticker: str, year: int, item1a_text: str) -> dict:
    filename = f"{year}_risk.json"
    existing = load_permanent(ticker, filename)
    if existing:
        print(f"[generate_risk_narrative] Using saved file for {ticker} {year}")
        return existing

    if not item1a_text:
        print(f"[generate_risk_narrative] No Item 1A text for {ticker} {year}")
        return {"year": year, "ticker": ticker, "error": "No Item 1A text available"}

    print(f"[generate_risk_narrative] Calling Claude for {ticker} {year}")

    system_prompt = load_prompt("risk_system.txt")
    user_prompt = load_prompt("risk_user.txt").format(
        ticker=ticker,
        year=year,
        item1a_text=item1a_text
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
    save_permanent(ticker, filename, result)
    return result


def generate_all_risk_narratives(ticker: str, filings: list[dict]) -> list[dict]:
    results = []
    for filing in filings:
        year = filing["year"]
        item1a = filing.get("sections", {}).get("item1a")
        result = generate_risk_narrative(ticker, int(year), item1a)
        results.append(result)
    return results


def generate_quant_trend(ticker: str, quant_years: list[dict], signals: dict) -> dict:
    filename = "quant_trend.json"
    existing = load_permanent(ticker, filename)
    if existing:
        print(f"[generate_quant_trend] Using saved file for {ticker}")
        return existing

    print(f"[generate_quant_trend] Calling Claude for {ticker}")

    system_prompt = load_prompt("quant_trend_system.txt")
    user_prompt = load_prompt("quant_trend_user.txt").format(
        ticker=ticker,
        quant_years_json=json.dumps(quant_years, indent=2),
        five_year_signals_json=json.dumps(signals.get("fiveYearTrend", {}), indent=2)
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        raw = response.content[0].text.strip()
        print(f"[generate_quant_trend] Raw response first 300 chars: {raw[:300]}")
        print(f"[generate_quant_trend] Raw response length: {len(raw)}")
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        result = json.loads(raw)
        save_permanent(ticker, filename, result)
        return result
    except Exception as e:
        print(f"[generate_quant_trend] ERROR: {type(e).__name__}: {e}")
        print(f"[generate_quant_trend] User prompt length: {len(user_prompt)} chars")
        raise


def generate_qual_trend(ticker: str, qual_years: list[dict]) -> dict:
    filename = "qual_trend.json"
    existing = load_permanent(ticker, filename)
    if existing:
        print(f"[generate_qual_trend] Using saved file for {ticker}")
        return existing

    print(f"[generate_qual_trend] Calling Claude for {ticker}")

    system_prompt = load_prompt("qual_trend_system.txt")
    user_prompt = load_prompt("qual_trend_user.txt").format(
        ticker=ticker,
        qual_years_json=json.dumps(qual_years, indent=2)
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
    save_permanent(ticker, filename, result)
    return result


def generate_risk_trend(ticker: str, risk_years: list[dict]) -> dict:
    filename = "risk_trend.json"
    existing = load_permanent(ticker, filename)
    if existing:
        print(f"[generate_risk_trend] Using saved file for {ticker}")
        return existing

    print(f"[generate_risk_trend] Calling Claude for {ticker}")

    # Only use 2022-2025 for risk trend
    risk_years_filtered = [r for r in risk_years if r.get("year") and int(r["year"]) >= 2022]

    system_prompt = load_prompt("risk_trend_system.txt")
    user_prompt = load_prompt("risk_trend_user.txt").format(
        ticker=ticker,
        risk_years_json=json.dumps(risk_years_filtered, indent=2)
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
    save_permanent(ticker, filename, result)
    return result


def generate_deep_value(ticker: str, quant_trend: dict, qual_trend: dict, risk_trend: dict, valuation: dict, stock_data: dict) -> dict:
    filename = "trend_deepvalue.json"
    existing = load_permanent(ticker, filename)
    if existing:
        print(f"[generate_deep_value] Using saved file for {ticker}")
        return existing

    print(f"[generate_deep_value] Calling Claude for {ticker}")

    market_cap_billions = round(stock_data.get("marketCap", 0) / 1e9, 1) if stock_data.get("marketCap") else None

    system_prompt = load_prompt("deepvalue_system.txt")
    user_prompt = load_prompt("deepvalue_user.txt").format(
        ticker=ticker,
        price=stock_data.get("price"),
        pe_ratio=valuation.get("peRatio"),
        price_fcf=valuation.get("priceFCF"),
        market_cap_billions=market_cap_billions,
        quant_trend_json=json.dumps(quant_trend, indent=2),
        qual_trend_json=json.dumps(qual_trend, indent=2),
        risk_trend_json=json.dumps(risk_trend, indent=2)
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
    save_permanent(ticker, filename, result)
    return result
