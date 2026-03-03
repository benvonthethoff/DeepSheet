# Cursor Refactoring Instructions

Each prompt below is one atomic task. Run them one at a time. Do not combine.

---

## PROMPT 1 — Extract JSON parse helper in `ai.py`

Open `annual-report-analyser/backend/ai.py`.

Add this new function on line 13 (directly after the `load_prompt` function):

```python
def _parse_json_response(response) -> dict:
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
```

Do not change anything else in the file.

---

## PROMPT 2 — Use `_parse_json_response` in `generate_quant_narrative`

Open `annual-report-analyser/backend/ai.py`.

Inside `generate_quant_narrative`, find and replace these exact lines:

```python
        raw = response.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        result = json.loads(raw)
```

Replace with:

```python
        result = _parse_json_response(response)
```

Do not change anything else in the file.

---

## PROMPT 3 — Use `_parse_json_response` in `generate_qual_narrative`

Open `annual-report-analyser/backend/ai.py`.

Inside `generate_qual_narrative`, find and replace these exact lines:

```python
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
```

Replace with:

```python
    result = _parse_json_response(response)
```

Do not change anything else in the file.

---

## PROMPT 4 — Use `_parse_json_response` in `generate_risk_narrative`

Open `annual-report-analyser/backend/ai.py`.

Inside `generate_risk_narrative`, find and replace these exact lines:

```python
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
```

Replace with:

```python
    result = _parse_json_response(response)
```

Do not change anything else in the file.

---

## PROMPT 5 — Use `_parse_json_response` in `generate_quant_trend`

Open `annual-report-analyser/backend/ai.py`.

Inside `generate_quant_trend`, find and replace these exact lines:

```python
        raw = response.content[0].text.strip()
        print(f"[generate_quant_trend] Raw response first 300 chars: {raw[:300]}")
        print(f"[generate_quant_trend] Raw response length: {len(raw)}")
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        result = json.loads(raw)
```

Replace with:

```python
        result = _parse_json_response(response)
```

Do not change anything else in the file.

---

## PROMPT 6 — Use `_parse_json_response` in `generate_qual_trend`

Open `annual-report-analyser/backend/ai.py`.

Inside `generate_qual_trend`, find and replace these exact lines:

```python
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
```

Replace with:

```python
    result = _parse_json_response(response)
```

Do not change anything else in the file.

---

## PROMPT 7 — Use `_parse_json_response` in `generate_risk_trend`

Open `annual-report-analyser/backend/ai.py`.

Inside `generate_risk_trend`, find and replace these exact lines:

```python
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
```

Replace with:

```python
    result = _parse_json_response(response)
```

Do not change anything else in the file.

---

## PROMPT 8 — Use `_parse_json_response` in `generate_deep_value`

Open `annual-report-analyser/backend/ai.py`.

Inside `generate_deep_value`, find and replace these exact lines:

```python
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
```

Replace with:

```python
    result = _parse_json_response(response)
```

Do not change anything else in the file.

---

## PROMPT 9 — Extract session factory in `edgar.py`

Open `annual-report-analyser/backend/edgar.py`.

Add this new function on line 14 (directly after the `COMPANY_TICKERS_PATH` line):

```python
def _make_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    session.headers.update({"User-Agent": "DeepSheet benvonai@gmail.com"})
    return session
```

Do not change anything else in the file.

---

## PROMPT 10 — Use `_make_session` in `resolve_cik`

Open `annual-report-analyser/backend/edgar.py`.

Inside `resolve_cik`, find and replace these exact lines:

```python
        session = requests.Session()
        session.trust_env = False

        response = session.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers={"User-Agent": "DeepSheet benvonai@gmail.com"}
        )
```

Replace with:

```python
        session = _make_session()
        response = session.get("https://www.sec.gov/files/company_tickers.json")
```

Do not change anything else in the file.

---

## PROMPT 11 — Use `_make_session` in `fetch_concept`

Open `annual-report-analyser/backend/edgar.py`.

Inside `fetch_concept`, find and replace these exact lines:

```python
        session = requests.Session()
        session.trust_env = False

        response = session.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json",
            headers={"User-Agent": "DeepSheet benvonai@gmail.com"}
        )
```

Replace with:

```python
        session = _make_session()
        response = session.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json"
        )
```

Do not change anything else in the file.

---

## PROMPT 12 — Use `_make_session` in `fetch_filing_urls`

Open `annual-report-analyser/backend/edgar.py`.

Inside `fetch_filing_urls`, find and replace these exact lines:

```python
    session = requests.Session()
    session.trust_env = False

    response = session.get(
        f"https://data.sec.gov/submissions/CIK{cik}.json",
        headers={"User-Agent": "DeepSheet benvonai@gmail.com"}
    )
```

Replace with:

```python
    session = _make_session()
    response = session.get(f"https://data.sec.gov/submissions/CIK{cik}.json")
```

Do not change anything else in the file.

---

## PROMPT 13 — Use `_make_session` in `download_filing`

Open `annual-report-analyser/backend/edgar.py`.

Inside `download_filing`, find and replace these exact lines:

```python
        session = requests.Session()
        session.trust_env = False
        print(f"[download_filing] Downloading {ticker} {year} from {url}")
        response = session.get(
            url,
            headers={"User-Agent": "DeepSheet benvonai@gmail.com"}
        )
```

Replace with:

```python
        session = _make_session()
        print(f"[download_filing] Downloading {ticker} {year} from {url}")
        response = session.get(url)
```

Do not change anything else in the file.

---

## PROMPT 14 — Delete dead code in `storage.py`

Open `annual-report-analyser/backend/storage.py`.

Delete these exact lines at the bottom of the file (lines 36–44):

```python
def load_trend(ticker: str, filename: str):
    return load_permanent(ticker, filename)

def save_trend(ticker: str, filename: str, data: dict):
    save_permanent(ticker, filename, data)

def trend_exists(ticker: str, filename: str) -> bool:
    path = f"{FILINGS_DIR}/{ticker.upper()}/{filename}"
    return os.path.exists(path)
```

Do not change anything else in the file.
