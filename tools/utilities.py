"""
File used for functions shared between multiple steps
"""

# Standard library imports
from tqdm import tqdm

# 3rd party imports
import numpy as np
import pandas as pd

# Local imports (logging configuration)
from tools.logger import logger

def normalize_dict_values(d: dict) -> dict:
    """
    Normalize the values of a dictionary to make their sum equal to 1.

    This function takes a dictionary as input and calculates the sum of its values. It then normalizes each value by dividing
    it by the total sum, ensuring that the sum of normalized values is 1. This is useful for converting a set of values into
    proportions or probabilities.

    Parameters:
        d (dict): A dictionary where values will be normalized.

    Returns:
        dict: A new dictionary with the same keys as the input, but with values normalized to ensure a sum of 1.
    """

    # Calculate the sum of all values in the dictionary
    total = sum(d.values())

    # Check if the total is not zero to avoid division by zero
    if total != 0:
        # Normalize each value by dividing by the total
        normalized_dict = {key: value / total for key, value in d.items()}
        return normalized_dict
    else:
        # Handle the case where the total is zero (all values are zero)
        return d  # Return the original dictionary


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: pd.Series,
    lon2: pd.Series,
    earth_radius: float,
) -> pd.Series:
    """
    Calculate Haversine distance between two sets of latitude and longitude coordinates.

    Parameters:
    - lat1 (float): Latitude of the first point in radians.
    - lon1 (float): Longitude of the first point in radians.
    - lat2 (pd.Series): Series of latitudes for the second points in radians.
    - lon2 (pd.Series): Series of longitudes for the second points in radians.
    - earth_radius (float): Earth's radius in the desired unit.

    Returns:
    pd.Series: Series of calculated Haversine distances between the first point and each point defined by lat2, lon2.

    This function calculates the Haversine distance between a single point (lat1, lon1)
    and a set of points defined by lat2 and lon2. The input coordinates should be in radians.
    The result is a Series containing the distances between the first point and each point defined by lat2, lon2.
    """

    # Haversine formula
    dlat = np.abs(lat2 - lat1)
    dlon = np.abs(lon2 - lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    a = np.clip(a, 0, 1)
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    distance = earth_radius * c

    return distance


def calculate_distances(df_1, df_2, EARTH_RADIUS):
    """
    Calculate distances between each grid point and station pair.

    Parameters:
    - grid_df (pd.DataFrame): DataFrame containing grid coordinates with "Lat" and "Lon" columns.
    - station_df (pd.DataFrame): DataFrame containing station coordinates with "Latitude" and "Longitude" columns.
    - EARTH_RADIUS (float): Radius of the Earth in the chosen units (e.g., kilometers or miles).

    Returns:
    np.ndarray: 2D array of distances where rows represent grid points and columns represent stations.
    """
    # Broadcast grid coordinates to match station coordinates
    lat_1 = np.radians(df_1["Latitude"].values[:, np.newaxis])
    lon_1 = np.radians(df_1["Longitude"].values[:, np.newaxis])
    lat_2 = np.radians(df_2["Latitude"].values)
    lon_2 = np.radians(df_2["Longitude"].values)

    distances = np.empty((len(df_1), len(df_2)))

    with tqdm(range(len(df_1)), desc="Calculating distances between all grid point/station pairs") as progress_bar:
        for i in progress_bar:
            distances[i, :] = haversine_distance(
                lat_1[i],
                lon_1[i],
                lat_2,
                lon_2,
                EARTH_RADIUS,
            )
            progress_bar.update(1)
        logger.info(progress_bar)
    return distances
