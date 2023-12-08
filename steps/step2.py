"""
Step 2: Creation of 2x2 Grid

There are 16200 cells across the globe (90 lat x 180 lon).
Each cell's values are computed using station records within a 1200km radius.
    - Contributions are weighted according to distance to cell center
    (linearly decreasing to 0 at distance 1200km)
"""

# Standard library imports
from itertools import product

# 3rd party library imports
import pandas as pd
import numpy as np
from tqdm import tqdm

# Local imports (tools functions)
from tools.utilities import (
    haversine_distance,
    linearly_decreasing_weight,
    normalize_dict_values,
)


def create_grid() -> pd.DataFrame:
    """
    Create a grid of latitude and longitude values.

    This function generates a grid of latitude and longitude coordinates by using numpy's `np.arange` to create a range
    of values for both latitude and longitude. It then computes all possible combinations of these values and stores
    them in a Pandas DataFrame.

    Returns:
        pd.DataFrame: A DataFrame with two columns, 'Lat' and 'Lon', containing all possible combinations of latitude
        and longitude coordinates.
    """

    # Create latitude and longitude values using np.arange
    lat_values = np.arange(88.0, -90.0, -2.0, dtype=np.float32)
    lon_values = np.arange(0.0, 360.0, 2.0, dtype=np.float32)

    # Include coordinates for north/south poles
    polar_coordinates = [(90.0, 0.0), (-90.0, 0.0)]

    # Generate all possible combinations of latitude and longitude values
    combinations = list(product(lat_values, lon_values)) + polar_coordinates

    # Create a DataFrame from the combinations
    grid = pd.DataFrame(combinations, columns=["Lat", "Lon"])
    return grid


def collect_metadata() -> pd.DataFrame:
    """
    Collect station metadata from NASA GISS GISTEMP dataset.

    This function fetches station metadata from the NASA GISS GISTEMP dataset, specifically from the provided URL. The data
    is read as a fixed-width formatted (FWF) text file and stored in a Pandas DataFrame.

    Returns:
        pd.DataFrame: A DataFrame containing station metadata, including columns for 'Station_ID', 'Latitude',
        'Longitude', 'Elevation', 'State', and 'Name'.
    """

    # Create station metadata dataframe
    meta_url = "https://data.giss.nasa.gov/pub/gistemp/v4.inv"
    column_widths = [11, 9, 10, 7, 3, 31]
    station_df: pd.DataFrame = pd.read_fwf(
        meta_url,
        widths=column_widths,
        header=None,
        names=["Station_ID", "Latitude", "Longitude", "Elevation", "State", "Name"],
    )
    return station_df


def nearby_stations(
    grid_df: pd.DataFrame,
    station_df: pd.DataFrame,
    max_distance: float,
    earth_radius: float,
) -> pd.DataFrame:
    """
    Identify nearby weather stations for each grid point and calculate their weights.

    This function calculates the nearby weather stations and their corresponding weights for each grid point in the provided
    grid DataFrame. It uses the Haversine distance formula to find stations within a specified maximum distance from each
    grid point and computes weights based on the distance. The resulting information is added as a new column in the grid
    DataFrame.

    Parameters:
        grid_df (pd.DataFrame): A DataFrame containing grid points with 'Lat' and 'Lon' columns.
        station_df (pd.DataFrame): A DataFrame containing station metadata, including 'Station_ID', 'Latitude',
            'Longitude'.
        max_distance (float): The maximum distance (in kilometers) for which stations are considered 'nearby'.

    Returns:
        pd.DataFrame: A modified grid DataFrame with an additional 'Nearby_Stations' column containing dictionaries of
        station IDs and their corresponding weights.
    """

    # Initialize an empty list to store station IDs and weights as dictionaries
    station_weights_within_radius = []

    # Use tqdm to track progress
    for index, row in tqdm(grid_df.iterrows(), total=len(grid_df), desc="Processing"):
        center_lat = row["Lat"]
        center_lon = row["Lon"]

        # Calculate distances for each station in station_df
        distances = station_df.apply(
            lambda x: haversine_distance(
                center_lat,
                center_lon,
                x["Latitude"],
                x["Longitude"],
                earth_radius,
            ),
            axis=1,
        )

        # Find station IDs within the specified radius
        nearby_stations = station_df[distances <= max_distance]

        # Calculate weights for each nearby station
        weights = nearby_stations.apply(
            lambda x: linearly_decreasing_weight(distances[x.name], max_distance),
            axis=1,
        )

        # Create a dictionary of station IDs and weights
        station_weights = dict(zip(nearby_stations["Station_ID"], weights))

        # Normalize weights to sum to 1
        station_weights = normalize_dict_values(station_weights)

        # Append the dictionary to the result list
        station_weights_within_radius.append(station_weights)

    # Add the list of station IDs and weights as a new column
    grid_df["Nearby_Stations"] = station_weights_within_radius

    # Set index name
    grid_df.index.name = "Box_Number"
    return grid_df


def step2(NEARBY_STATION_RADIUS, EARTH_RADIUS) -> pd.DataFrame:
    """
    This function represents Step 1 of the data processing pipeline. It involves the creation of a 2x2 grid of latitude
    and longitude values, gathering station metadata, and identifying nearby weather stations for each grid point along
    with their weights. The resulting information is stored in a Pandas DataFrame.

    Returns:
        pd.DataFrame: A DataFrame containing the grid points, station metadata, and nearby stations with their weights.
    """

    # Create 2x2 grid
    grid = create_grid()

    # Gather station metadata
    station_df = collect_metadata()

    # Find nearby stations for each grid point
    grid = nearby_stations(grid, station_df, NEARBY_STATION_RADIUS, EARTH_RADIUS)
    return grid
