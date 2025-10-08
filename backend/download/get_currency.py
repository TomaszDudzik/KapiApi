import requests
import pandas as pd

# URL to fetch currency rates from NBP API
URL = "https://api.nbp.pl/api/exchangerates/tables/A/2025-10-02/?format=json"

def get_nbp_rates():
    """
    Fetch and process currency exchange rates from the National Bank of Poland (NBP) API.

    This function retrieves exchange rates from the NBP public API for a given date
    (hardcoded in the `URL` constant). The data is returned as a pandas DataFrame
    containing selected columns in a standardized format.

    Workflow:
        1. Send an HTTP GET request to the NBP API.
        2. Parse the JSON response and extract the first (and only) element.
        3. Convert the 'rates' list into a pandas DataFrame.
        4. Select, rename, and reorder relevant columns for readability.

    Returns:
        pd.DataFrame: A DataFrame with the following columns:
            - as_of_date (datetime.date): Effective date of the rates.
            - currency_ticker (str): Currency code (e.g., 'USD', 'EUR').
            - currency_value (float): Mid exchange rate in PLN.
            - currency_name (str): Full name of the currency.

    Raises:
        requests.exceptions.RequestException: If the HTTP request fails.
        ValueError: If the API response format is unexpected.

    Example:
        >>> df = get_nbp_rates()
        >>> print(df.head())
             as_of_date currency_ticker  currency_value      currency_name
        0  2025-10-06             THB           0.1179  bat (Tajlandia)
        1  2025-10-06             USD           4.2170  dolar amerykański
    """
    # Fetch data from NBP API
    response = requests.get(URL)
    response.raise_for_status()  # rzuca wyjątek przy błędzie
    data = response.json()[0]    # NBP zwraca listę, bierzemy pierwszy element

    # Get rates and convert to DataFrame
    rates = data['rates']
    df = pd.DataFrame(rates)
    df['effectiveDate'] = data['effectiveDate']

    # Select columns and rename for clarity
    df = df[['currency', 'code', 'mid', 'effectiveDate']]
    df.columns = ['currency_name', 'currency_ticker', 'currency_value', 'as_of_date']
    
    df['as_of_date'] = pd.to_datetime(df['as_of_date']).dt.strftime("%Y-%m-%d")
    df['currency_value'] = df['currency_value'].astype(float)

    # Reorder columns
    df = df[['as_of_date', 'currency_ticker', 'currency_value', 'currency_name']]

    return df

# Example usage
if __name__ == "__main__":
    df = get_nbp_rates()
    print(df.head())
