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
    calculate_distances,
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


def add_brightness_to_df(
    df: pd.DataFrame, brightness_url: str, meta_url: str
) -> pd.DataFrame:
    """
    Adds night brightness data to the input DataFrame.

    Parameters:
    - df (pd.DataFrame): Input DataFrame containing temperature data.
    - brightness_url (str): URL for night brightness data.
    - meta_url (str): URL for inventory metadata.

    Returns:
    - pd.DataFrame: Input DataFrame with added night brightness data.
    """

    # Create i_j_dict and data dictionary
    i_j_dict = read_night_file(brightness_url)
    data = process_inv_file(meta_url, i_j_dict)

    # Create dataframe from data dictionary, set index to station ID
    brightness_df = pd.DataFrame(data)
    brightness_df = brightness_df.set_index("Station_ID")

    # Merge with input dataframe
    df = df.merge(brightness_df["Value"], left_index=True, right_index=True)
    return df


def find_nearby_rural_stations(
    df,
    BRIGHTNESS_THRESHOLD,
    URBAN_NEARBY_RADIUS,
    MIN_NEARBY_RURAL_STATIONS,
    EARTH_RADIUS,
):
    """
    Identify nearby rural stations for urban locations based on brightness and distance.

    Parameters:
    - df (pd.DataFrame): DataFrame containing station data, including columns "Latitude," "Longitude," and "Value" (brightness).
    - BRIGHTNESS_THRESHOLD (float): Threshold value to classify stations as urban (True) or rural (False).
    - URBAN_NEARBY_RADIUS (float): Radius in the desired units for considering nearby rural stations.
    - MIN_NEARBY_RURAL_STATIONS (int): Minimum number of nearby rural stations to retain an urban location.
    - EARTH_RADIUS (float): Earth's radius in the desired units for distance calculation.

    Returns:
    pd.DataFrame: DataFrame containing urban locations with information on nearby rural stations.

    This function identifies nearby rural stations for each urban location based on brightness and distance.
    It calculates distances between urban and rural stations, considers nearby stations within the specified radius,
    and retains urban locations with the minimum required number of nearby rural stations.
    """
    # Add column for urban flag
    df_copy = df.copy()
    df_copy["Urban"] = df_copy["Value"] > BRIGHTNESS_THRESHOLD

    # Filter urban and rural dataframes
    urban_df = df_copy[df_copy["Urban"] == True]
    rural_df = df_copy[df_copy["Urban"] == False]

    # Calculate all distances between urban and rural stations
    distances = calculate_distances(urban_df, rural_df, EARTH_RADIUS)

    nearby_dict_list = []

    distances[distances > URBAN_NEARBY_RADIUS] = np.nan
    weights = 1.0 - (distances / URBAN_NEARBY_RADIUS)

    for i in tqdm(
        range(len(urban_df)), desc="Finding nearby stations for each grid point"
    ):
        # Find indices of stations within the specified radius
        valid_indices = np.where(weights[i] <= 1.0)

        # Create a dictionary using numpy operations
        nearby_dict = {rural_df.index[j]: weights[i, j] for j in valid_indices[0]}

        # Normalize weights to sum to 1
        nearby_dict = normalize_dict_values(nearby_dict)

        nearby_dict_list.append(nearby_dict)

    # Add the list of station IDs and weights as a new column
    urban_df_weights = urban_df.copy()
    urban_df_weights.loc[:, "Rural_Station_Weights"] = nearby_dict_list

    # Drop rows with fewer than minimum number of nearby rural stations
    urban_df_weights = urban_df_weights[
        urban_df_weights["Rural_Station_Weights"].apply(
            lambda x: len(x) >= MIN_NEARBY_RURAL_STATIONS
        )
    ]

    return urban_df_weights


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
    for station, row in tqdm(
        df_urban_valid.iterrows(),
        total=len(df_urban_valid),
        desc="Adjusting urban anomalies",
        unit="row",
    ):
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
    anomaly_with_brightness = add_brightness_to_df(
        df=df,
        brightness_url=BRIGHTNESS_URL,
        meta_url=GHCN_META_URL,
    )

    # Calculate weights for nearby rural stations
    df_urban_valid = find_nearby_rural_stations(
        anomaly_with_brightness,
        URBAN_BRIGHTNESS_THRESHOLD,
        URBAN_NEARBY_RADIUS,
        MIN_NEARBY_RURAL_STATIONS,
        EARTH_RADIUS,
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
