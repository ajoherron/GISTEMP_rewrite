'''
Step 3: Creation of 2x2 Grid

There are 16200 cells across the globe (90 lat x 180 lon).
Each cell's values are computed using station records within a 1200km radius.
    - Contributions are weighted according to distance to cell center
    (linearly decreasing to 0 at distance 1200km)
'''

# Standard library imports
import os
import sys
import math
from itertools import product

# 3rd party library imports
import pandas as pd
import numpy as np
from tqdm import tqdm

# Add the parent directory to sys.path
current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

# Local imports
from parameters.constants import NEARBY_STATION_RADIUS
from parameters.constants import EARTH_RADIUS


def create_grid() -> pd.DataFrame:
    '''
    Create a grid of latitude and longitude values.

    This function generates a grid of latitude and longitude coordinates by using numpy's `np.arange` to create a range
    of values for both latitude and longitude. It then computes all possible combinations of these values and stores
    them in a Pandas DataFrame.

    Returns:
        pd.DataFrame: A DataFrame with two columns, 'Lat' and 'Lon', containing all possible combinations of latitude
        and longitude coordinates.
    '''
    
    # Create latitude and longitude values using np.arange
    lat_values = np.arange(88.0, -90.0, -2.0, dtype=np.float32)
    lon_values = np.arange(-180.0, 180.0, 2.0, dtype=np.float32)

    # Generate all possible combinations of latitude and longitude values
    combinations = list(product(lat_values, lon_values))

    # Create a DataFrame from the combinations
    grid = pd.DataFrame(combinations, columns=['Lat', 'Lon'])
    return grid

def collect_metadata() -> pd.DataFrame:
    '''
    Collect station metadata from NASA GISS GISTEMP dataset.

    This function fetches station metadata from the NASA GISS GISTEMP dataset, specifically from the provided URL. The data
    is read as a fixed-width formatted (FWF) text file and stored in a Pandas DataFrame.

    Returns:
        pd.DataFrame: A DataFrame containing station metadata, including columns for 'Station_ID', 'Latitude',
        'Longitude', 'Elevation', 'State', and 'Name'.
    '''
    
    # Create station metadata dataframe
    meta_url = 'https://data.giss.nasa.gov/pub/gistemp/v4.inv'
    column_widths = [11, 9, 10, 7, 3, 31]
    station_df: pd.DataFrame = pd.read_fwf(meta_url, widths=column_widths, header=None,
                              names=['Station_ID', 'Latitude', 'Longitude', 'Elevation', 'State', 'Name'])
    return station_df

def nearby_stations(grid_df: pd.DataFrame, station_df: pd.DataFrame, max_distance: float, earth_radius: float) -> pd.DataFrame:
    '''
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
    '''

    # Initialize an empty list to store station IDs and weights as dictionaries
    station_weights_within_radius = []

    # Use tqdm to track progress
    for index, row in tqdm(grid_df.iterrows(), total=len(grid_df), desc="Processing"):
        center_lat = row['Lat']
        center_lon = row['Lon']

        # Calculate distances for each station in station_df
        distances = station_df.apply(lambda x: haversine_distance(center_lat, center_lon,
                                                                  x['Latitude'], x['Longitude'],
                                                                  earth_radius, max_distance), axis=1)

        # Find station IDs within the specified radius
        nearby_stations = station_df[distances <= max_distance]

        # Calculate weights for each nearby station
        weights = nearby_stations.apply(lambda x: linearly_decreasing_weight(distances[x.name], max_distance), axis=1)

        # Create a dictionary of station IDs and weights
        station_weights = dict(zip(nearby_stations['Station_ID'], weights))
        
        # Normalize weights to sum to 1
        station_weights = normalize_dict_values(station_weights)

        # Append the dictionary to the result list
        station_weights_within_radius.append(station_weights)

    # Add the list of station IDs and weights as a new column
    grid_df['Nearby_Stations'] = station_weights_within_radius

    # Set index name
    grid_df.index.name = 'Box_Number'
    return grid_df

def haversine_distance(lat1: float, lon1: float,
                       lat2: float, lon2: float,
                       earth_radius: float, station_radius: float) -> float:
    """
    Calculate the spherical distance (in kilometers) between two pairs of
    latitude and longitude coordinates using the Haversine formula.

    Args:
        lat1 (float): Latitude of the first point in degrees.
        lon1 (float): Longitude of the first point in degrees.
        lat2 (float): Latitude of the second point in degrees.
        lon2 (float): Longitude of the second point in degrees.

    Returns:
        float: Spherical distance in kilometers.
    """
    # Convert latitude and longitude from degrees to radians
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    # Haversine formula
    dlat: float = abs(lat2 - lat1)
    dlon: float = abs(lon2 - lon1)

    try:
        a: float = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c: float = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance: float = earth_radius * c
            
    except:
        # Otherwise set the distance just beyond the nearby radius
        distance = station_radius + 1

    return distance

def linearly_decreasing_weight(distance: float, max_distance: float) -> float:
    """
    Calculate a linearly decreasing weight based on the given distance
    and maximum distance.

    Args:
        distance (float): The distance at which you want to calculate the weight.
        max_distance (float): The maximum distance at which the weight becomes 0.

    Returns:
        float: The linearly decreasing weight, ranging from 1 to 0.
    """
    # Ensure that distance is within the valid range [0, max_distance]
    distance: float = max(0, min(distance, max_distance))

    # Calculate the weight as a linear interpolation
    weight: float = 1.0 - (distance / max_distance)
    return weight

def normalize_dict_values(d: dict) -> dict:
    '''
    Normalize the values of a dictionary to make their sum equal to 1.

    This function takes a dictionary as input and calculates the sum of its values. It then normalizes each value by dividing
    it by the total sum, ensuring that the sum of normalized values is 1. This is useful for converting a set of values into
    proportions or probabilities.

    Parameters:
        d (dict): A dictionary where values will be normalized.

    Returns:
        dict: A new dictionary with the same keys as the input, but with values normalized to ensure a sum of 1.
    '''
    
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
    
def step3() -> pd.DataFrame:
    '''
    This function represents Step 3 of the data processing pipeline. It involves the creation of a 2x2 grid of latitude
    and longitude values, gathering station metadata, and identifying nearby weather stations for each grid point along
    with their weights. The resulting information is stored in a Pandas DataFrame.

    Returns:
        pd.DataFrame: A DataFrame containing the grid points, station metadata, and nearby stations with their weights.
    '''

    # Create 2x2 grid
    grid = create_grid()

    # Gather station metadata
    station_df = collect_metadata()

    # Find nearby stations for each grid point
    grid = nearby_stations(grid, station_df, NEARBY_STATION_RADIUS, EARTH_RADIUS)
    return grid
