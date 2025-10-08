# pip install supabase>=2.5,<3.0 pandas
import os
import sys
from datetime import datetime
from typing import Iterable, List, Dict, Any

import pandas as pd
from supabase import create_client, Client

# Allow "from download.get_currency import get_nbp_rates"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from download.get_currency import get_nbp_rates  # noqa: E402

SUPABASE_URL = "https://ybdhjrrndwvoudrkvyjm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InliZGhqcnJuZHd2b3Vkcmt2eWptIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODczNTg5MywiZXhwIjoyMDc0MzExODkzfQ.g4bsLdoWrkhrYK45QK-ldhkU3S_nwIc2eew-iKdp6Tw"   # cannot be derived from the DSN
TABLE_NAME = "currency"
BATCH_SIZE = 1000


def chunked(seq: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Make sure types serialize cleanly to JSON and match your table schema.
    - as_of_date: date (YYYY-MM-DD)
    - currency_ticker: string
    - replace NaNs with None (null)
    """
    if "as_of_date" in df.columns:
        df["as_of_date"] = pd.to_datetime(df["as_of_date"]).dt.strftime("%Y-%m-%d")
    if "currency_ticker" in df.columns:
        df["currency_ticker"] = df["currency_ticker"].astype(str)

    # Replace NaNs for JSON
    df = df.where(~df.isna(), None)
    return df


def upsert_currency_rows(client: Client, df: pd.DataFrame) -> int:
    """
    Upsert all rows (idempotent) using the unique constraint on
    (as_of_date, currency_ticker). Returns number of rows affected
    (as reported back by PostgREST).
    """
    records = df.to_dict(orient="records")
    total_returned = 0

    for batch in chunked(records, BATCH_SIZE):
        res = client.table(TABLE_NAME).upsert(
            batch,
            #on_conflict="as_of_date,currency_ticker",
        ).execute()

        # supabase-py v2 returns a dict-like object with "data"
        data = getattr(res, "data", None) if hasattr(res, "data") else res.get("data")  # type: ignore[attr-defined]
        if data is not None:
            total_returned += len(data)

    return total_returned


def main() -> None:
    client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # 1) Fetch your source data
    df_nbp = get_nbp_rates()
    if df_nbp is None or df_nbp.empty:
        print("No data from get_nbp_rates(); nothing to do.")
        sys.exit(0)

    # 2) Normalize types for JSON/Postgres
    df_nbp = normalize_df(df_nbp)

    # 3) Idempotent write (let the DB dedupe)
    affected = upsert_currency_rows(client, df_nbp)

    print(
        f"✅ Upserted {len(df_nbp)} records to '{TABLE_NAME}' "
        f"(unique on as_of_date,currency_ticker). Server returned {affected} rows."
    )


if __name__ == "__main__":
    main()

