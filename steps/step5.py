"""
Step 5: Calculating ocean anomalies

Create xarray dataset of ERSST data from NOAA.
Calculate anomaly of sea surface temperature from the dataset.
"""

# Standard imports
import urllib.request
import shutil
import os
from tqdm import tqdm

# 3rd party imports
import requests
import xarray as xr
import numpy as np
from xarray import DataArray


def sst_dataset(url: str, start: int, end: int) -> DataArray:
    """
    Downloads ERSST data from a given URL, trims it to specified years, and returns it as an xarray dataset.

    Args:
    url (str): The URL to download the ERSST data file.
    start (str): The start date for trimming the dataset (e.g., '1880-01-01').
    end (str): The end date for trimming the dataset (e.g., '2023-12-31').

    Returns:
    xr.Dataset: An xarray data array containing the ERSST data for the specified time range.
    """

    # Set temporary file name
    local_file = "sst.mnmean.nc"

    # Send an HTTP GET request to the URL and save the content to the local file
    response = requests.get(url)

    # Check the status code
    if response.status_code == 200:
        # Download the file from the URL with tqdm
        with tqdm.wrapattr(
            open(local_file, "wb"),
            "write",
            miniters=1,
            total=int(response.headers.get("content-length", 0)),
            desc="Downloading ERSST data",
        ) as out_file:
            with urllib.request.urlopen(url) as url_response:
                shutil.copyfileobj(url_response, out_file)

        # Load the local file into an xarray dataset
        da_ocean = xr.open_dataset(local_file)

        # Confirm successful loading
        print("ERSST data loaded into xarray data array successfully.")

        # Remove the local file after loading
        os.remove(local_file)

        # Trim to specified years
        da_ocean = da_ocean["sst"].sel(time=slice(start, end))
        return da_ocean

    else:
        print(f"Failed to download ERSST data. Status code: {response.status_code}")


def sst_anomaly(
    da_ocean: DataArray, baseline_start: str, baseline_end: str
) -> DataArray:
    """
    Calculate Sea Surface Temperature (SST) Anomalies.

    This function calculates SST anomalies by subtracting the monthly climatology
    of a baseline time range from the input SST data array.

    Args:
        ds_ocean (xr.DataArray): Input dataset containing Sea Surface Temperature data.
        baseline_start (str): Start date of the baseline time range (e.g., '1951-01-01').
        baseline_end (str): End date of the baseline time range (e.g., '1980-12-31').

    Returns:
        xr.DataArray: A data array containing Sea Surface Temperature anomalies.
    """

    # Create trimmed dataset for baseline years
    baseline_da = da_ocean.sel(time=slice(baseline_start, baseline_end))

    # Calculate monthly averages for each month in baseline time range
    monthly_climatology = baseline_da.groupby("time.month").mean(dim="time")

    # Calculate anomaly values
    da_ocean_anomaly = da_ocean.groupby("time.month") - monthly_climatology
    return da_ocean_anomaly


def add_polar_coordinates(da):
    """
    Add polar coordinates to an xarray DataArray, creating NaN values at the poles.

    Parameters:
    - da (xarray.DataArray): Input DataArray containing values.

    Returns:
    xarray.DataArray: Modified DataArray with added polar coordinates and NaN values at the poles.
    """
    # Create new latitude/longitude coordinates with values lat=+/-90, lon=0
    new_lat = xr.DataArray([90.0, -90.0], dims=["lat"], coords={"lat": [90.0, -90.0]})
    new_lon = xr.DataArray([0.0], dims=["lon"], coords={"lon": [0.0]})

    # Create a new DataArray with NaN values at the poles
    nan_data = np.full((2, 1, len(da["time"])), np.nan, dtype=np.float32)
    da_with_poles = xr.concat(
        [
            da,
            xr.DataArray(
                nan_data,
                dims=["lat", "lon", "time"],
                coords={"lat": new_lat, "lon": new_lon},
            ),
        ],
        dim="lat",
    )

    # Sort the 'lat' coordinate in ascending order
    da_with_poles_sorted = da_with_poles.sortby("lat")

    # Add the new latitude/longitude coordinates with NaN values
    da_with_poles_sorted = da_with_poles_sorted.assign_coords(
        {"lat_pole": new_lat, "lon_pole": new_lon}
    )

    # Remove 'lat_pole' and 'lon_pole' coordinates
    da_with_poles_sorted = da_with_poles_sorted.drop_vars(["lat_pole", "lon_pole"])
    return da_with_poles_sorted


def remove_ice_values(da, threshold):
    """
    Remove ice values from an xarray DataArray by setting values below a threshold to NaN.

    Parameters:
    - da (xarray.DataArray): Input DataArray containing values to be modified.
    - threshold (float): Threshold value; values below this threshold will be set to NaN.

    Returns:
    xarray.DataArray: Modified DataArray with ice values set to NaN.
    """
    # Count non-NaN values before modification
    valid_values_before = int(np.sum(~np.isnan(da.values)))

    # Set values below the threshold to NaN
    da_iceless = da.where(da >= threshold, np.nan)

    # Count non-NaN values after modification
    valid_values_after = int(np.sum(~np.isnan(da_iceless.values)))

    # Count number of values converted to NaN
    num_removed_nan = valid_values_before - valid_values_after

    # Calculate the percentage of values removed
    percentage_removed = round((num_removed_nan / valid_values_before) * 100, 3)

    # Print number / percent of converted data points
    print(
        f"Number of ice values (below {threshold}) converted to NaN:\n{num_removed_nan} ({percentage_removed}% of all data points)"
    )

    return da_iceless


def step5(
    ERSST_URL,
    START_DATE,
    END_DATE,
    BASELINE_START_DATE,
    BASELINE_END_DATE,
    SST_CUTOFF_TEMP,
) -> DataArray:
    """
    Step 5: Calculate Sea Surface Temperature (SST) Anomalies

    This function performs the following steps:
    1. Loads the SST data array for the correct time range from 'sst.mnmean.nc'.
    2. Calculates SST anomalies using the inputted baseline range from '1951-01-01' to '1980-12-31'.
    3. Adds two coordinates for the north and south pole.
    4. Converts all ice data to NaN

    Returns:
        xr.Dataset: A dataset containing Sea Surface Temperature anomalies.
    """
    # Create SST dataset for correct time range
    da = sst_dataset(url=ERSST_URL, start=START_DATE, end=END_DATE)

    # Calculate SST anomalies using inputted baseline range
    da_anomaly = sst_anomaly(
        da_ocean=da,
        baseline_start=BASELINE_START_DATE,
        baseline_end=BASELINE_END_DATE,
    )

    # Add polar coordinates to anomaly dataset
    da_anomaly_polar = add_polar_coordinates(da_anomaly)

    # Convert ice values to NaN
    da_ocean = remove_ice_values(da_anomaly_polar, SST_CUTOFF_TEMP)
    return da_ocean
