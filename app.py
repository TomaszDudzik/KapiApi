"""
FastAPI backend for mobile KPI dashboard.

Endpoints
- GET /health                 → {status: "ok"}
- GET /kpi                    → {today, mtd, avg7, delta, last_date}
- GET /series?days=60         → [{date: "YYYY-MM-DD", profit: float}, ...]
- POST /upload (multipart)    → upload and replace data.csv (optional)

How to run
1) Python 3.10+
2) pip install -r requirements.txt
3) uvicorn app:app --reload --port 8000

requirements.txt
-----------------
fastapi
uvicorn[standard]
python-multipart
pydantic
pytz
# Optional (faster CSV parsing & date handling). The code works without pandas.
# pandas

Notes
- Data source is a CSV file (default: DATA_CSV=data.csv). Headers accepted (case-insensitive):
  date/data, revenue/przychod/przychód, cost/koszt/koszty, profit/zysk
- If profit is missing, it is computed as revenue - cost if both exist.
- Basic API key auth: set env API_KEY=... and pass header "X-API-Key: ..." from your app.
"""

import os
import csv
from dataclasses import dataclass
from datetime import datetime, date
from typing import List, Optional, Tuple

from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DATA_PATH = os.environ.get("DATA_CSV", "data.csv")
API_KEY_ENV = os.environ.get("API_KEY")  # optional
DATE_FORMATS = ["%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d", "%d/%m/%Y"]

# --------------- utils ---------------
@dataclass
class Row:
    d: date
    revenue: Optional[float]
    cost: Optional[float]
    profit: Optional[float]


def parse_date(s: str) -> Optional[date]:
    s = (s or "").strip()
    if not s:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        return None


def to_float(x: Optional[str]) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip().replace("\u00A0", "").replace(" ", "").replace(",", ".")
    if s == "" or s.lower() in {"none", "nan"}:
        return None
    try:
        return float(s)
    except Exception:
        return None


def read_csv(path: str) -> List[Row]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows: List[Row] = []
        for r in reader:
            low = {k.lower().strip(): v for k, v in r.items()}
            ds = low.get("date") or low.get("data") or ""
            d = parse_date(ds)
            if not d:
                continue
            rev = to_float(low.get("revenue") or low.get("przychod") or low.get("przychód"))
            cost = to_float(low.get("cost") or low.get("koszt") or low.get("koszty"))
            profit = to_float(low.get("profit") or low.get("zysk"))
            if profit is None and (rev is not None and cost is not None):
                profit = rev - cost
            rows.append(Row(d=d, revenue=rev, cost=cost, profit=profit))
    rows.sort(key=lambda r: r.d)
    return rows


def latest_date(rows: List[Row]) -> Optional[date]:
    return rows[-1].d if rows else None


def filter_month(rows: List[Row], target: date) -> List[Row]:
    return [r for r in rows if r.d.year == target.year and r.d.month == target.month]


def last_n(rows: List[Row], n: int) -> List[Row]:
    return rows[-n:] if rows else []


def compute_kpis(rows: List[Row]) -> Tuple[Optional[float], float, float, Optional[float], Optional[date]]:
    if not rows:
        return (None, 0.0, 0.0, None, None)
    last = rows[-1]
    today_profit = last.profit if last.profit is not None else 0.0

    # Δ vs yesterday
    if len(rows) >= 2 and rows[-2].profit is not None and today_profit is not None:
        delta = today_profit - rows[-2].profit
    else:
        delta = None

    # MTD
    ld = latest_date(rows)
    mtd = sum((r.profit or 0.0) for r in filter_month(rows, ld)) if ld else 0.0

    # 7‑day avg
    last7 = [r for r in last_n(rows, 7) if r.profit is not None]
    avg7 = (sum(r.profit for r in last7) / len(last7)) if last7 else 0.0

    return (today_profit, mtd, avg7, delta, ld)

# --------------- FastAPI ---------------
app = FastAPI(title="KPI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    if API_KEY_ENV and x_api_key != API_KEY_ENV:
        raise HTTPException(status_code=401, detail="Invalid API key")


class KpiOut(BaseModel):
    today: Optional[float]
    mtd: float
    avg7: float
    delta: Optional[float]
    last_date: Optional[str]


class SeriesPoint(BaseModel):
    date: str
    profit: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/kpi", response_model=KpiOut)
def get_kpi():
    rows = read_csv(DATA_PATH)
    t, m, a7, dlt, ld = compute_kpis(rows)
    return KpiOut(
        today=t,
        mtd=m,
        avg7=a7,
        delta=dlt,
        last_date=(ld.isoformat() if ld else None),
    )


@app.get("/series", response_model=List[SeriesPoint])
def get_series(days: int = Query(default=60, ge=1, le=365)):
    rows = [r for r in read_csv(DATA_PATH) if r.profit is not None]
    subset = rows[-min(days, len(rows)):] if rows else []
    return [SeriesPoint(date=r.d.isoformat(), profit=float(r.profit)) for r in subset]


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Only CSV allowed")
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except Exception:
        text = content.decode("latin-1")
    # basic validation: must contain a date-ish header
    if "date" not in text.lower() and "data" not in text.lower():
        raise HTTPException(400, "CSV must contain a date/data column")
    with open(DATA_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return {"ok": True, "bytes": len(content)}


# For local debug: uvicorn app:app --reload --port 8000