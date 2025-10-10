import requests
import pandas as pd
from datetime import datetime, timedelta


def get_nbp_rates():
    """
    Fetches currency exchange rates from the NBP API for the previous day.
    Returns a DataFrame with columns: as_of_date, currency_ticker, currency_value, currency_name.
    If the API request fails, returns None.

    Arguments:
        None

    Returns:
        pd.DataFrame or None: DataFrame with currency rates or None if the request fails.
    """
    # Get yesterday's date in YYYY-MM-DD format
    yesterday_date = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d")

    # NBP API endpoint for exchange rates
    url = f"https://api.nbp.pl/api/exchangerates/tables/A/{yesterday_date}/?format=json"
    #url = f"https://api.nbp.pl/api/exchangerates/tables/A/2025-10-08/?format=json"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()[0]

        # Get rates and convert to DataFrame
        df = pd.DataFrame(data['rates'])
        df['effectiveDate'] = data['effectiveDate']

        # Select columns and rename for clarity
        df = df[['currency', 'code', 'mid', 'effectiveDate']]
        df.columns = ['currency_name', 'currency_ticker', 'currency_value', 'currency_date']
        
        # Convert data types
        df['currency_date'] = pd.to_datetime(df['currency_date']).dt.strftime("%Y-%m-%d")
        df['currency_value'] = df['currency_value'].astype(float)

        # Reorder columns
        df = df[['currency_date', 'currency_ticker', 'currency_value', 'currency_name']]

        # Add key column for deduplication
        df['currency_id'] = df['currency_ticker'] + "_" + df['currency_date'].astype(str)

        return df

    except requests.exceptions.RequestException as e:
        return None
