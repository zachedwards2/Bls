# Install required libraries

import os
import requests
import pandas as pd
import streamlit as st

# Load API key from environment variables or use default
BLS_API_KEY = os.getenv("BLS_API_KEY", "3a3bc740675c42529050683a2c4fddee")  # Replace with your own key if needed

# Check if the API key is loaded properly
if not BLS_API_KEY:
    raise ValueError("API key not found. Please add your BLS_API_KEY in the environment variables or hardcode it.")

# BLS API endpoint
API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

def fetch_bls_data(series_id, start_year, end_year):
    """
    Fetch data from the BLS Public API for a given series ID and date range.

    Args:
        series_id (str): The BLS series ID.
        start_year (int): The start year for the data request.
        end_year (int): The end year for the data request.

    Returns:
        dict: Raw JSON response containing the BLS data.
    """
    headers = {"Content-Type": "application/json"}
    payload = {
        "seriesid": [series_id],
        "startyear": str(start_year),
        "endyear": str(end_year),
        "registrationkey": BLS_API_KEY
    }
    response = requests.post(API_URL, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code}")

def process_bls_data(raw_data):
    """
    Process the raw BLS API data into a clean Pandas DataFrame.

    Args:
        raw_data (dict): The raw JSON response from the BLS API.

    Returns:
        pd.DataFrame: A DataFrame containing 'date' and 'value' columns.
    """
    try:
        series = raw_data.get('Results', {}).get('series', [])
        if not series:
            raise Exception("No series data found in response.")

        data = series[0].get('data', [])
        if not data:
            raise Exception("No data found in series.")

        df = pd.DataFrame(data)

        # Ensure 'year' and 'period' columns exist
        if 'year' not in df or 'period' not in df:
            raise Exception(f"Expected columns 'year' and 'period' not found in data. Raw data: {raw_data}")

        # Combine year and period (e.g., 'M01', 'M02') to create a proper datetime column
        df['date'] = pd.to_datetime(df['year'] + '-' + df['period'].str[1:], errors='coerce')

        # Drop rows where date is NaT (Not a Time) after conversion
        df = df.dropna(subset=['date'])

        # Sort by date and reset index
        df = df.sort_values(by='date').reset_index(drop=True)

        # Convert 'value' column to numeric (coerce errors)
        df['value'] = pd.to_numeric(df['value'], errors='coerce')

        return df[['date', 'value']]
    except Exception as e:
        raise Exception(f"Error processing data: {e}")

# Streamlit app
st.title("US Labor Statistics Dashboard")

# Sidebar inputs
st.sidebar.header("Data Configuration")
start_year = st.sidebar.number_input("Start Year", min_value=2000, max_value=2024, value=2023)
end_year = st.sidebar.number_input("End Year", min_value=2000, max_value=2024, value=2024)

# Series IDs and descriptions
series_info = {
    "CES0000000001": {
        "name": "Total Non-Farm Workers",
        "description": "The total number of non-farm workers in the United States."
    },
    "LNS14000000": {
        "name": "Unemployment Rate",
        "description": "The percentage of unemployed persons in the labor force."
    },
    "PRS85006112": {
        "name": "Nonfarm Business Unit Labor Costs",
        "description": "The costs associated with labor per unit of output in nonfarm businesses."
    },
    "CES0500000003": {
        "name": "Total Private Average Hourly Earnings",
        "description": "The average hourly earnings of private employees, seasonally adjusted."
    }
}

# Main dashboard display
for series_id, series_data in series_info.items():
    st.write(f"### {series_data['name']}")
    st.write(f"**Description:** {series_data['description']}")
    
    try:
        # Fetch and process data
        raw_data = fetch_bls_data(series_id, start_year, end_year)
        df = process_bls_data(raw_data)

        # Format dates for display
        df['formatted_date'] = df['date'].dt.strftime('%m/%Y')

        # Ensure sorting of the original dates for the chart
        df = df.sort_values(by='date')

        # Display data table
        st.dataframe(df[['formatted_date', 'value']].rename(columns={"formatted_date": "Date"}))

        # Display chart
        st.line_chart(data=df.set_index('date')['value'])  # Use 'date' as x-axis for proper chronological display
    except Exception as e:
        st.error(f"Error fetching data for {series_data['name']}: {e}")
