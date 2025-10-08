# pip install sqlalchemy psycopg2-binary pandas
import os, socket, urllib.parse
import sys
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from download.get_currency import get_nbp_rates

#ipv4 = socket.gethostbyname("db.ybdhjrrndwvoudrkvyjm.supabase.co") 

# Connection string (from Supabase > Database > Connection string)
DB_URL = "postgresql://postgres:kkB8K64!r-.bGm6@db.ybdhjrrndwvoudrkvyjm.supabase.co:5432/postgres?sslmode=require"

# Create SQLAlchemy engine
engine = create_engine(DB_URL, pool_pre_ping=True)

# Fetch currency data
df_nbp_rates = get_nbp_rates()

query = text("SELECT as_of_date, currency_ticker FROM currency")

# Fetch existing data to avoid duplicates
with engine.connect() as conn:
    df_existing_data = pd.read_sql(query, conn)
    df_existing_data = pd.DataFrame(df_existing_data)

# Check for new data
df_existing_data['key'] = df_existing_data['as_of_date'].astype(str) + "_" + df_existing_data['currency_ticker']    
df_nbp_rates['key'] = df_nbp_rates['as_of_date'].astype(str) + "_" + df_nbp_rates['currency_ticker']
new_data = df_nbp_rates[~df_nbp_rates['key'].isin(df_existing_data['key'])].drop(columns=['key'])


if new_data.empty:
    print("No new data to load.")
    sys.exit(0)
print(f"Loading {len(new_data)} new rows...")


# Load DataFrame to the table
new_data.to_sql(
    name="currency",
    con=engine,
    schema="public",
    if_exists="append",
    index=False
)

print("✅ Data loaded successfully!")