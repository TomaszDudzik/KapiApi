# pip install sqlalchemy psycopg2-binary pandas
import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from download.get_currency import get_nbp_rates

# Your values (see Supabase "Connect" panel)
DB_USER = "postgres"
PROJECT_REF = "ybdhjrrndwvoudrkvyjm"
DB_PASS = "kkB8K64!r-.bGm6"
REGION = "eu-north-1"

POOLER_TXN_DSN = (
    f"postgresql+psycopg2://{DB_USER}.{PROJECT_REF}:{DB_PASS}"
    f"@aws-1-{REGION}.pooler.supabase.com:6543/postgres"
)

engine = create_engine(POOLER_TXN_DSN, poolclass=NullPool)

# Fetch currency data
df_nbp_rates = get_nbp_rates()

query = text("SELECT rate_date || base_ccy AS rate_date_base_ccy FROM fx_rates")

# Fetch existing data to avoid duplicates
with engine.connect() as conn:
    df_existing_data = pd.read_sql(query, conn)
    df_existing_data = pd.DataFrame(df_existing_data)

# Check for new data
df_nbp_rates['rate_date_base_ccy'] = df_nbp_rates['rate_date'] + df_nbp_rates['base_ccy']
new_data = df_nbp_rates[~df_nbp_rates['rate_date_base_ccy'].isin(df_existing_data['rate_date_base_ccy'])]

if new_data.empty:
    print("No new data to load.")
    sys.exit(0)
print(f"Loading {len(new_data)} new rows...")


# Load DataFrame to the table
new_data.to_sql(
    name="fx_rates",
    con=engine,
    schema="public",
    if_exists="append",
    index=False
)

print("✅ Data loaded successfully!")