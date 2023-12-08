"""
Step 4: Adjusting urban stations

An urban station must meet various criteria to have its trend adjusted:
    - Must have sufficient nearby rural stations
    - Their combined record must have enough overlap with the urban station

If the urban station does not meet the criteria, it is discarded.
All stations with short records are discarded.
"""

# Standard library imports
import requests
from typing import Dict, List

# 3rd-party library imports
import pandas as pd
import numpy as np
from tqdm import tqdm

# Local imports
from tools.utilities import (
    haversine_distance,
    linearly_decreasing_weight,
    normalize_dict_values,
)


def read_night_file(url: str) -> Dict:
    """
    Read night brightness data from a given URL and create a dictionary.

    The function sends a GET request to the provided URL, processes the response
    to extract (i, j) coordinates and their corresponding brightness values, and
    populates a dictionary with this information.

    Parameters:
    - url (str): The URL from which to fetch the night brightness data.

    Returns:
    - dict: A dictionary where keys are (i, j) coordinates and values are brightness values.
    """
    i_j_dict = {}

    # Send GET request
    response = requests.get(url)

    # Check if request was successful
    if response.status_code == 200:
        # Loop through each line in response text
        for line in response.text.splitlines():
            # Populate dictionary
            line = line.split()
            i, j, value = line[0], line[1], line[2]
            i_j = (i, j)
            i_j_dict[i_j] = value

    return i_j_dict


def process_inv_file(url: str, i_j_dict: Dict) -> List[Dict]:
    """
    Process inventory data from a given URL and enrich it with brightness information.

    The function sends a GET request to the provided URL, processes the response
    to extract metadata (Station_ID, Latitude, Longitude), calculates search indices
    based on geographical coordinates, and enriches the metadata with brightness values
    obtained from the provided i_j_dict.

    Parameters:
    - url (str): The URL from which to fetch the inventory data.
    - i_j_dict (dict): A dictionary where keys are (i, j) coordinates and values are brightness values.

    Returns:
    - list: A list of dictionaries containing enriched metadata, including Station_ID, Latitude, Longitude, and brightness Value.
    """

    data = []

    # Send GET request
    response = requests.get(url)

    # Check if request was successful
    if response.status_code == 200:
        # Loop through each line in response text
        for line in response.text.splitlines():
            inv_line = line.split()

            # Extract lon and lat from split line
            lon, lat = float(inv_line[2]), float(inv_line[1])

            # Calculate search_i and search_j based on lon and lat
            search_i = str(round((lon + 180) * 120 + 1))
            search_j = str(round(21600 + 0.5 - (lat + 90) * 120))

            # Ensure search_j < 21600 and search_i < 43200
            search_j = "21600" if int(search_j) >= 21600 else search_j
            search_i = "1" if int(search_i) >= 43200 else search_i

            # Try to get value from i_j_dict, set to 0 if not found
            try:
                value = int(i_j_dict.get((search_i, search_j), 0))
            except:
                value = 0

            # Append metadata to data dictionary
            data.append(
                {
                    "Station_ID": inv_line[0],
                    "Latitude": lat,
                    "Longitude": lon,
                    "Value": value,
                }
            )
    return data


def collect_brightness_data(brightness_url: str, meta_url: str) -> pd.DataFrame:
    """
    Collects night brightness data and inventory metadata, creating a Pandas DataFrame.

    Parameters:
    - brightness_url (str): URL for night brightness data.
    - meta_url (str): URL for inventory metadata.

    Returns:
    - pd.DataFrame: DataFrame with enriched metadata and brightness values, indexed by Station_ID.
    """
    # Create i_j_dict and data dictionary
    i_j_dict = read_night_file(brightness_url)
    data = process_inv_file(meta_url, i_j_dict)

    # Create dataframe from data dictionary, set index to station ID
    df = pd.DataFrame(data)
    df = df.set_index("Station_ID")
    return df


def add_brightness_data(
    df: pd.DataFrame, brightness_url: str, meta_url: str
) -> pd.DataFrame:
    """
    Adds brightness data to the input DataFrame.

    Parameters:
    - df (pd.DataFrame): Input DataFrame containing temperature data.
    - brightness_url (str): URL for night brightness data.
    - meta_url (str): URL for inventory metadata.

    Returns:
    - pd.DataFrame: Input DataFrame with added brightness data.
    """

    # Gather brightness data
    brightness_df = collect_brightness_data(brightness_url, meta_url)

    # Merge with input dataframe
    df = df.merge(brightness_df["Value"], left_index=True, right_index=True)
    return df


def calculate_rural_weights(
    df: pd.DataFrame,
    brightness_threshold: float,
    min_nearby_stations: int,
    earth_radius: float,
    urban_nearby_radius: float,
) -> pd.DataFrame:
    """
    Calculate weights for nearby rural stations based on brightness threshold.

    Parameters:
    - df (pd.DataFrame): Input DataFrame containing temperature data.
    - brightness_threshold (float): Threshold for considering stations as urban.
    - min_nearby_stations (int): Minimum number of nearby rural stations required.
    - earth_radius (float): Radius of the Earth for distance calculations.
    - urban_nearby_radius (float): Radius for considering stations as nearby urban stations.

    Returns:
    - pd.DataFrame: DataFrame with urban stations and their corresponding rural weights.
    """
    # Add column for urban flag
    df_copy = df.copy()
    df_copy["Urban"] = df_copy["Value"] > brightness_threshold

    # Filter urban stations (where 'Urban' is True)
    df_urban = df_copy[df_copy["Urban"] == True]

    # Filter rural stations (where 'Urban' is False)
    df_rural = df_copy[df_copy["Urban"] == False]

    # Create dataframes for urban/rural coordinates
    df_urban_meta = df_urban[["Latitude", "Longitude"]]
    df_rural_meta = df_rural[["Latitude", "Longitude"]]

    # Initialize list of rural weights
    rural_weights = []

    # Loop through urban station metadata
    for urban_station_id, urban_row in tqdm(df_urban_meta.iterrows()):
        # Collect urban coordinates
        urban_lat = urban_row["Latitude"]
        urban_lon = urban_row["Longitude"]

        # Find all rural stations within given radius of urban station, add to dictionary
        distances = df_rural_meta.apply(
            lambda x: haversine_distance(
                urban_lat,
                urban_lon,
                x["Latitude"],
                x["Longitude"],
                earth_radius=earth_radius,
            ),
            axis=1,
        )
        rural_within_radius = df_rural_meta[distances <= urban_nearby_radius]

        # Creat dictionary of Station IDs and weights
        weights = rural_within_radius.apply(
            lambda x: linearly_decreasing_weight(
                distances[x.name], urban_nearby_radius
            ),
            axis=1,
        )
        weights_dict = dict(zip(rural_within_radius.index, weights))

        # Normalize weights to sum to 1
        normalized_weights = normalize_dict_values(weights_dict)

        # Append dictionary to result list
        rural_weights.append(normalized_weights)

    # Create dataframe for urban stations with minimum number of nearby rural stations
    df_urban_valid = df_urban.copy()
    df_urban_valid["Rural_Station_Weights"] = rural_weights
    df_urban_valid = df_urban_valid[
        df_urban_valid["Rural_Station_Weights"].apply(len) >= min_nearby_stations
    ]
    return df_urban_valid


def adjust_urban_anomalies(
    df: pd.DataFrame,
    df_urban_valid: pd.DataFrame,
    start_year: int,
    end_year: int,
    brightness_threshold: float,
) -> pd.DataFrame:
    """
    Adjust urban temperature anomalies using nearby rural stations.

    Parameters:
    - df (pd.DataFrame): Input DataFrame containing temperature data.
    - df_urban_valid (pd.DataFrame): DataFrame with valid urban stations and rural weights.
    - start_year (int): Start year for temperature anomalies adjustment.
    - end_year (int): End year for temperature anomalies adjustment.
    - brightness_threshold (float): Threshold for considering stations as urban.

    Returns:
    - pd.DataFrame: DataFrame with adjusted temperature anomalies for urban stations.
    """
    # Create dataframe for rural data
    df_copy = df.copy()
    df_copy["Urban"] = df_copy["Value"] > brightness_threshold
    df_rural = df_copy[df_copy["Urban"] == False]

    # Define the range of years (1880 to 2023) and months (1 to 12)
    years = range(start_year, end_year + 1)  # 2024 is exclusive, so it includes 2023
    months = range(1, 13)

    # Create a list to store the column names
    timeseries_columns = []

    # Generate column names for all year and month combinations
    for year in years:
        for month in months:
            column_name = f"{month}_{year}"
            timeseries_columns.append(column_name)

    # Loop through all urban stations with valid number of surrounding rural stations
    for station, row in tqdm(df_urban_valid.iterrows()):
        # Collect weights for rural stations for given urban station
        weights_dict = row["Rural_Station_Weights"]

        # Create dataframe of all nearby rural timeseries
        rural_stations = list(weights_dict.keys())
        rural_station_timeseries = df_rural.loc[rural_stations][timeseries_columns]

        # Multiply normalized weights by corresponding station timeseries
        weights = list(weights_dict.values())
        weighted_timeseries = rural_station_timeseries.multiply(weights, axis=0)

        # Calculate overall timeseries
        # (Only need to sum since weights are normalized)
        weighted_timeseries_mean = weighted_timeseries.sum(axis=0)

        # Replace 0.0 values with NaN
        weighted_timeseries_mean = weighted_timeseries_mean.replace(0.000000, np.nan)

        # Replace urban timeseries with weighted nearby rural station timeseries
        df.loc[station, timeseries_columns] = weighted_timeseries_mean

    return df


def step4(
    df: pd.DataFrame,
    URBAN_BRIGHTNESS_THRESHOLD: float,
    EARTH_RADIUS: float,
    URBAN_NEARBY_RADIUS: float,
    MIN_NEARBY_RURAL_STATIONS: int,
    START_YEAR: int,
    END_YEAR: int,
    BRIGHTNESS_URL: str,
    GHCN_META_URL: str,
) -> pd.DataFrame:
    """
    Perform Step 4 of the gistemp algorithm: adjusting urban anomalies.

    Parameters:
    - df (pd.DataFrame): Input DataFrame containing temperature data.
    - URBAN_BRIGHTNESS_THRESHOLD (float): Threshold for considering stations as urban based on brightness.
    - EARTH_RADIUS (float): Radius of the Earth for distance calculations.
    - URBAN_NEARBY_RADIUS (float): Radius for considering stations as nearby urban stations.
    - MIN_NEARBY_RURAL_STATIONS (int): Minimum number of nearby rural stations required.
    - START_YEAR (int): Start year for temperature anomalies adjustment.
    - END_YEAR (int): End year for temperature anomalies adjustment.
    - BRIGHTNESS_URL (str): URL for night brightness data.
    - GHCN_META_URL (str): URL for inventory metadata.

    Returns:
    - pd.DataFrame: DataFrame with adjusted temperature anomalies for urban stations.
    """
    # Add brightness data to input dataframe
    anomaly_with_brightness = add_brightness_data(
        df=df,
        brightness_url=BRIGHTNESS_URL,
        meta_url=GHCN_META_URL,
    )

    # Calculate weights for nearby rural stations
    df_urban_valid = calculate_rural_weights(
        df=anomaly_with_brightness,
        brightness_threshold=URBAN_BRIGHTNESS_THRESHOLD,
        min_nearby_stations=MIN_NEARBY_RURAL_STATIONS,
        earth_radius=EARTH_RADIUS,
        urban_nearby_radius=URBAN_NEARBY_RADIUS,
    )

    # Adjust urban anomalies based on weights
    df_adjusted_urban = adjust_urban_anomalies(
        df=anomaly_with_brightness,
        df_urban_valid=df_urban_valid,
        start_year=START_YEAR,
        end_year=END_YEAR,
        brightness_threshold=URBAN_BRIGHTNESS_THRESHOLD,
    )
    return df_adjusted_urban
