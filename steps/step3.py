"""
Step 3: Calculation of land anomalies
"""

# 3rd party library imports
import pandas as pd
from tqdm import tqdm

# Local imports (logging configuration)
from tools.logger import logger


def calculate_monthly_averages(
    df: pd.DataFrame, start_year: int, end_year: int
) -> pd.DataFrame:
    """
    Calculates monthly average temperatures from a DataFrame for the
    specified year range.

    Parameters:
    - df (DataFrame): Input DataFrame with temperature data.
    - start_year (int): Start year for the range of data.
    - end_year (int): End year for the range of data.

    Returns:
    - DataFrame: New DataFrame with monthly average temperatures.
    """

    # Make dictionary (key: month #, value: series for station/average temperature)
    monthly_averages = {}
    for month in range(1, 13):
        columns_to_average = [
            f"{month}_{year}" for year in range(start_year, end_year + 1)
        ]
        monthly_averages[month] = df[columns_to_average].mean(axis=1)

    # Create a DataFrame with the monthly averages
    monthly_averages_df = pd.DataFrame(monthly_averages)
    monthly_averages_df.columns = [f"{month}_Average" for month in range(1, 13)]
    return monthly_averages_df


def calculate_station_anomalies(
    df: pd.DataFrame, monthly_averages_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate temperature anomalies for a DataFrame by subtracting monthly averages.

    Parameters:
    - df (DataFrame): Input DataFrame with temperature data.
    - monthly_averages_df (DataFrame): DataFrame containing monthly average temperatures.

    Returns:
    - DataFrame: New DataFrame with temperature anomalies.
    """

    # Create a copy of input dataframe
    anomaly_df = df.copy()

    # Create a tqdm object to track progress
    with tqdm(anomaly_df.columns, desc="Calculating anomalies for GHCN data") as progress_bar:
        for col in progress_bar:
            # Skip the "Latitude" and "Longitude" columns
            if col in ["Latitude", "Longitude"]:
                continue

            # Extract the month from the column name
            month = int(col.split("_")[0])

            # Define the column name for the monthly average
            monthly_avg_col = f"{month}_Average"

            # Subtract the monthly average from the raw data column
            anomaly_df[col] = anomaly_df[col] - monthly_averages_df[monthly_avg_col]
            
            progress_bar.update(1)

    logger.debug(progress_bar)
    return anomaly_df


def step3(df, ANOMALY_START_YEAR, ANOMALY_END_YEAR):
    """
    Perform Step 3 of the anomaly calculation process.

    Parameters:
    - df (pd.DataFrame): DataFrame containing temperature data with columns "Station_ID," "Year," "Month," and "Temperature."
    - ANOMALY_START_YEAR (int): Start year for calculating anomalies.
    - ANOMALY_END_YEAR (int): End year for calculating anomalies.

    Returns:
    pd.DataFrame: DataFrame containing temperature anomalies for all stations.

    This function performs the following steps:
    1. Calculate monthly averages for the specified range of years (ANOMALY_START_YEAR to ANOMALY_END_YEAR).
    2. Calculate temperature anomalies for all stations based on the monthly averages.
    """
    # Calculate all monthly averages
    monthly_averages_df = calculate_monthly_averages(
        df=df, start_year=ANOMALY_START_YEAR, end_year=ANOMALY_END_YEAR
    )

    # Calculate anomalies for all stations
    anomaly_df = calculate_station_anomalies(
        df=df, monthly_averages_df=monthly_averages_df
    )
    return anomaly_df
