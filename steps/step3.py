"""
Step 3: Calculation of land anomalies
"""

# 3rd party library imports
import pandas as pd
from tqdm import tqdm

# Local imports (logging configuration)
from tools.logger import logger


def calculate_station_anomalies(
    df: pd.DataFrame,
    START_YEAR: int,
    END_YEAR: int,
    BASELINE_START_YEAR: int,
    BASELINE_END_YEAR: int,
) -> pd.DataFrame:
    """
    Calculates anomalies for each GHCN station.

    For each station/month pair, if there are 20 or more valid data points in the baseline period:
        anomaly = raw_temperature - baseline_period_average

    Otherwise, if there are fewer than 20 baseline data points for a given station/month pair:
        anomaly = raw_temperature - full_timeseries_average

    Parameters:
    - df (DataFrame): Input DataFrame with temperature data.
    - START_YEAR (int): Start year for the range of data.
    - END_YEAR (int): End year for the range of data.
    - BASELINE_START_YEAR (int): Start year for the anomaly baseline period.
    - BASELINE_END_YEAR (int): Start year for the anomaly baseline period.

    Returns:
    - DataFrame: New DataFrame with monthly average temperatures.
    """

    # Initialize list for monthly anomaly dataframes
    monthly_anomalies_list = []

    # Loop through all months
    # for month in range(1, 13):
    with tqdm(
        range(1, 13), desc="Calculating monthly anomalies for GHCN data"
    ) as progress_bar:

        for month in progress_bar:

            # Gather list of all columns for given month
            monthly_columns = []
            for year in range(START_YEAR, END_YEAR + 1):
                monthly_columns.append(str(month) + "_" + str(year))
            monthly_columns.append("Latitude")
            monthly_columns.append("Longitude")

            # Create monthly dataframe from column list
            df_monthly = df[monthly_columns]

            # Determine number of valid data points in baseline period
            month_columns = df_monthly.columns.drop(["Latitude", "Longitude"])
            baseline_columns = [
                col
                for col in month_columns
                if int(col.split("_")[1]) >= BASELINE_START_YEAR
                and int(col.split("_")[1]) <= BASELINE_END_YEAR
            ]
            baseline_data = df_monthly[baseline_columns]
            valid_data_count = baseline_data.count(axis=1)

            # Create column indicating if station has enough baseline data
            df_monthly = df_monthly.copy()
            df_monthly.loc[:, "Valid Data Count"] = valid_data_count
            df_monthly.loc[:, "Enough Baseline Data"] = (
                df_monthly["Valid Data Count"] >= 20
            )

            # Create dataframe for all stations with enough baseline data
            df_reg_anom = df_monthly[df_monthly["Enough Baseline Data"]]
            df_reg_anom = df_reg_anom.drop(
                columns=["Valid Data Count", "Enough Baseline Data"]
            )

            # Calculate baseline period average
            baseline_average = df_reg_anom[baseline_columns].mean(axis=1)
            df_reg_anom["Baseline Average"] = baseline_average

            # Calculate anomalies for each column
            for col in df_reg_anom.columns:
                if col in ["Latitude", "Longitude", "Baseline Average"]:
                    continue
                df_reg_anom[col] = df_reg_anom[col] - df_reg_anom["Baseline Average"]

            # Create dataframe for all stations without enough baseline data
            df_mon_avg = df_monthly[~df_monthly["Enough Baseline Data"]]
            df_mon_avg = df_mon_avg.drop(
                columns=["Valid Data Count", "Enough Baseline Data"]
            )

            # Calculate average for entire timeseries
            timeseries_columns = [
                col
                for col in df_mon_avg.columns
                if col not in ["Latitude", "Longitude"]
            ]
            timeseries_average = df_mon_avg[timeseries_columns].mean(axis=1)
            df_mon_avg["Timeseries Average"] = timeseries_average

            # Calculate anomalies for each column
            for col in df_mon_avg.columns:
                if col in ["Latitude", "Longitude", "Timeseries Average"]:
                    continue
                df_mon_avg[col] = df_mon_avg[col] - df_mon_avg["Timeseries Average"]

            # Combine both dataframes, sort according to Station ID index
            df_monthly_anomalies = pd.concat([df_reg_anom, df_mon_avg])
            df_monthly_anomalies = df_monthly_anomalies.drop(
                columns=["Baseline Average", "Timeseries Average"]
            )
            df_monthly_anomalies = df_monthly_anomalies.sort_index()
            monthly_anomalies_list.append(df_monthly_anomalies)
            progress_bar.update(1)

    # Debug progress bar
    logger.debug(progress_bar)

    # Combine all dataframes into complete anomaly dataframe
    df_anomalies = pd.concat(monthly_anomalies_list, axis=1)

    # Get list of sorted columns
    sorted_columns = []
    for year in range(START_YEAR, END_YEAR + 1):
        for month in range(1, 13):
            column = str(month) + "_" + str(year)
            sorted_columns.append(column)
    sorted_columns.append("Latitude")
    sorted_columns.append("Longitude")

    # Reorder DataFrame columns
    df_anomalies = df_anomalies[sorted_columns]

    # Drop repeat Latitude / Longitude columns
    df_anomalies = df_anomalies.loc[:, ~df_anomalies.columns.duplicated()]
    return df_anomalies


def step3(
    df: pd.DataFrame,
    START_YEAR: int,
    END_YEAR: int,
    BASELINE_START_YEAR: int,
    BASELINE_END_YEAR: int,
) -> pd.DataFrame:
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
    # Calculate anomalies for all stations
    df_station_anomalies = calculate_station_anomalies(
        df=df,
        START_YEAR=START_YEAR,
        END_YEAR=END_YEAR,
        BASELINE_START_YEAR=BASELINE_START_YEAR,
        BASELINE_END_YEAR=BASELINE_END_YEAR,
    )
    return df_station_anomalies
