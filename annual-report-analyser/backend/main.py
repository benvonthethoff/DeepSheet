import os
os.environ["no_proxy"] = "*"

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from edgar import resolve_cik

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
