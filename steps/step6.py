"""
Step 6: Combination of land and ocean anomalies
"""

# 3rd-party library imports
import pandas as pd
import numpy as np
import xarray as xr
from tqdm import tqdm
from xarray import Dataset

# Local imports (logging configuration)
from tools.logger import logger

def calculate_grid_anomalies(df: pd.DataFrame, grid: pd.DataFrame) -> pd.DataFrame:
    """
    This function takes as input a DataFrame containing station-level temperature anomalies and a grid information DataFrame
    that provides weights for each station within grid cells. It calculates grid-level temperature anomalies by applying the
    provided weights to each station's data, summing the weighted anomalies, and replacing zero anomalies with NaN values.
    The output DataFrame has columns representing grid cells, and additional columns 'Lat' and 'Lon' that indicate the center
    latitude and longitude of each grid cell.

    Parameters:
    - df (DataFrame): Input DataFrame with station temperature anomalies.
    - grid (DataFrame): Grid information DataFrame with station weights.

    Returns:
    - DataFrame: A new DataFrame containing grid-level temperature anomalies with NaN values for cells with no valid data.
    """

    # Make copy on input dataframe
    anomaly_df = df.copy()

    # Drop location columns
    exclude_columns = ["Latitude", "Longitude"]
    anomaly_df = anomaly_df.drop(columns=exclude_columns)

    # Initialize anomaly list for rows in anomaly dataframe
    anomaly_dict = {}
    anomaly_list = []
    with tqdm(range(len(grid)), desc="Calculating anomalies for grid points") as progress_bar:
        for i in progress_bar:
            # Create a dataframe of all the stations within 1200km of a
            station_dict = grid.iloc[i]["Nearby_Stations"]

            # Create grid_stations_df by selecting rows for the desired stations
            grid_stations_df = anomaly_df.loc[
                anomaly_df.index.isin(station_dict.keys())
            ].copy()

            # Iterate through the station_dict and apply weights to columns
            for station, weight in station_dict.items():
                if station not in exclude_columns and station in grid_stations_df.index:
                    grid_stations_df.loc[station] *= weight

            # Calculate average anomaly (add up all rows)
            grid_anomaly = grid_stations_df.sum()
            anomaly_list.append(grid_anomaly)

            # Add to anomaly dictionary
            anomaly_dict[i] = grid_anomaly
            progress_bar.update(1)
        logger.info(progress_bar)

    # Create dataframe and set index
    grid_anomaly = pd.DataFrame(anomaly_list)
    grid_anomaly = grid_anomaly.rename_axis("grid")

    # Replace 0.0 with NaN in all columns except 'box_number'
    grid_anomaly = grid_anomaly.replace(0.0, np.nan)

    # Initialize an empty dictionary to store the mapping
    box_coord_dict = {}

    # Iterate through the rows of the DataFrame
    for index, row in grid.iterrows():
        # Get the Center_Latitude and Center_Longitude values
        center_latitude = row["Latitude"]
        center_longitude = row["Longitude"]

        # Add the mapping to the dictionary
        box_coord_dict[index] = (center_latitude, center_longitude)

    # Add the "Center_Latitude" and "Center_Longitude" columns based on the dictionary
    grid_anomaly["Latitude"] = grid_anomaly.index.map(lambda x: box_coord_dict[x][0])
    grid_anomaly["Longitude"] = grid_anomaly.index.map(lambda x: box_coord_dict[x][1])
    return grid_anomaly


def dataframe_to_dataset(grid_anomaly: pd.DataFrame) -> Dataset:
    """
    Convert a DataFrame with temperature data into an xarray Dataset.

    Parameters:
    - grid_anomaly (DataFrame): Input DataFrame with temperature data, containing columns 'Lat', 'Lon', and columns representing time steps.

    Returns:
    - Dataset: xarray Dataset with temperature data, indexed by latitude, longitude, and time.
    """

    # Create copy of input dataframe, rename columns
    df = grid_anomaly.copy()
    df = df.rename(columns={"Latitude": "lat", "Longitude": "lon"})

    # Reshape dataframe into long format
    df = df.melt(id_vars=["lat", "lon"], var_name="date", value_name="temp")

    # Get months and years, drop duplicate rows
    df[["month", "year"]] = df["date"].str.split("_", expand=True).astype(int)
    df = df.drop_duplicates(subset=["lat", "lon", "month", "year"])

    # Create date column formatted as year-month-01
    dates = df["year"].astype(str) + "-" + df["month"].astype(str) + "-01"

    # Convert dates to datetime objects
    datetimes = pd.to_datetime(dates)

    # Remove unnecessary columns
    df = df.drop(columns=["date", "month", "year"])

    # Create new time column using datetime objects
    df["time"] = pd.to_datetime(datetimes)

    # Set multi-index
    df = df.set_index(["lat", "lon", "time"])

    # Convert pandas dataframe to xarray dataset
    ds = df.to_xarray()
    return ds


def combine_land_ocean_anomalies(ds_land: Dataset, ds_ocean: Dataset) -> Dataset:
    """
    Combine land and ocean temperature anomalies into a single dataset.

    This function takes two xarray Datasets, one representing land temperature anomalies
    and the other representing ocean temperature anomalies. It aligns the time range of
    the land dataset with the ocean dataset and combines them while considering missing
    values. The result is a single Dataset containing normalized temperature anomalies.

    Parameters:
    - ds_land (Dataset): xarray Dataset with land temperature anomalies.
    - ds_ocean (Dataset): xarray Dataset with ocean temperature anomalies.

    Returns:
    - Dataset: Combined xarray Dataset with normalized temperature anomalies.
    """

    # Find the last date from ds_ocean
    last_date_ocean = ds_ocean["time"].isel(time=-1).values

    # Select the corresponding time range from ds_land
    ds_land = ds_land.sel(time=slice(None, last_date_ocean))

    # Count NaN values
    ocean_nan = ds_ocean.isnull().sum(dim="time")
    land_nan = ds_land.isnull().sum(dim="time")

    # Normalize NaN counts to become weights
    time_length = len(ds_ocean["time"])
    ocean_weight = 1 - (ocean_nan / time_length)
    land_weight = 1 - (land_nan / time_length)

    # Calculate weighted land / ocean data
    weighted_ocean = ds_ocean * ocean_weight
    weighted_land = ds_land * land_weight

    # Combine weighted data into single anomaly dataset
    ds_combined = weighted_land.fillna(0) + weighted_ocean.fillna(0)
    ds_anomaly = ds_combined.where(ds_combined != 0.0, np.nan)
    return ds_anomaly


def step6(
    df_adjusted_urban: pd.DataFrame, df_grid: pd.DataFrame, ds_ocean: xr.Dataset
) -> xr.Dataset:
    """
    Perform Step 6 of the analysis, calculating anomalies for each point in a 2x2 grid.

    Parameters:
    - df_adjusted_urban (pd.DataFrame): DataFrame with adjusted temperature anomalies for urban stations.
    - df_grid (pd.DataFrame): DataFrame containing information about the 2x2 grid.
    - ds_ocean (xr.Dataset): Dataset containing ocean temperature anomalies.

    Returns:
    - xr.Dataset: Combined dataset containing land and ocean temperature anomalies.
    """
    # Get rid of unnecessary brightness and urban flag columns
    df_trimmed = df_adjusted_urban.drop(columns=["Value"])

    # Calculate anomalies for each point in 2x2 grid
    grid_anomaly = calculate_grid_anomalies(df=df_trimmed, grid=df_grid)

    # Convert land anomaly dataframe to dataset
    ds_land = dataframe_to_dataset(grid_anomaly)

    # Combine land and anomaly datasets into final result dataset
    ds_anomaly = combine_land_ocean_anomalies(ds_land=ds_land, ds_ocean=ds_ocean)
    return ds_anomaly
