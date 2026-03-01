import json
import os

CACHE_DIR = "cache"
DATA_DIR = "data"
FILINGS_DIR = "data/filings"

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

def load_permanent(ticker: str, filename: str):
    path = f"{FILINGS_DIR}/{ticker.upper()}/{filename}"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

def save_permanent(ticker: str, filename: str, data: dict):
    dir_path = f"{FILINGS_DIR}/{ticker.upper()}"
    os.makedirs(dir_path, exist_ok=True)
    path = f"{dir_path}/{filename}"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_trend(ticker: str, filename: str):
    return load_permanent(ticker, filename)

def save_trend(ticker: str, filename: str, data: dict):
    save_permanent(ticker, filename, data)

def trend_exists(ticker: str, filename: str) -> bool:
    path = f"{FILINGS_DIR}/{ticker.upper()}/{filename}"
    return os.path.exists(path)
