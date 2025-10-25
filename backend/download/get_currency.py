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
        df = df[['code', 'mid', 'effectiveDate']]
        df.columns = ['base_ccy', 'rate_close', 'rate_date']
        
        # Convert data types
        df['rate_date'] = pd.to_datetime(df['rate_date']).dt.strftime("%Y-%m-%d")
        df['rate_close'] = df['rate_close'].astype(float)

        # Reorder columns
        df = df[['rate_date', 'base_ccy', 'rate_close']]

        # Add key column for deduplication
        df['quate_ccy'] = 'PLN'

        return df

    except requests.exceptions.RequestException as e:
        return None
