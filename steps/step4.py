'''
Step 4: Creation of ERSST Dataset

Create xarray dataset of ERSST data from NOAA.
Calculate anomaly of sea surface temperature from the dataset.
'''

# Standard imports
import urllib.request
import shutil
import os
import sys

# 3rd party imports
import xarray as xr
import requests

# Add the parent directory to sys.path
current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

# Local imports
from parameters.data import ERSST_url
from parameters.constants import start_date, end_date, baseline_start_date, baseline_end_date


def sst_dataset(url, start, end):
    """
    Downloads ERSST data from a given URL, trims it to specified years, and returns it as an xarray dataset.

    Args:
    url (str): The URL to download the ERSST data file.
    start (str): The start date for trimming the dataset (e.g., '1880-01-01').
    end (str): The end date for trimming the dataset (e.g., '2023-12-31').

    Returns:
    xr.Dataset: An xarray dataset containing the ERSST data for the specified time range.
    """

    # Set temporary file name
    local_file = "sst.mnmean.nc"

    # Send an HTTP GET request to the URL and save the content to the local file
    response = requests.get(url)

    # Check the status code
    if response.status_code == 200:
        # Download the file from the URL
        with urllib.request.urlopen(url) as url_response, open(local_file, 'wb') as out_file:
            shutil.copyfileobj(url_response, out_file)

        # Load the local file into an xarray dataset
        ds_ocean = xr.open_dataset(local_file)

        # Confirm successful loading
        print("ERSST data loaded into xarray dataset successfully.")

        # Remove the local file after loading
        os.remove(local_file)
        
        # Trim to specified years
        ds_ocean = ds_ocean['sst'].sel(time=slice(start, end))
        return ds_ocean
        
    else:
        print(f"Failed to download ERSST data. Status code: {response.status_code}")


def sst_anomaly(ds_ocean, baseline_start, baseline_end):
    """
    Calculate Sea Surface Temperature (SST) Anomalies.

    This function calculates SST anomalies by subtracting the monthly climatology
    of a baseline time range from the input SST dataset.

    Args:
        ds_ocean (xr.Dataset): Input dataset containing Sea Surface Temperature data.
        baseline_start (str): Start date of the baseline time range (e.g., '1951-01-01').
        baseline_end (str): End date of the baseline time range (e.g., '1980-12-31').

    Returns:
        xr.Dataset: A dataset containing Sea Surface Temperature anomalies.
    """
    
    # Create trimmed dataset for baseline years
    baseline_ds = ds_ocean.sel(time=slice(baseline_start, baseline_end))
    
    # Calculate monthly averages for each month in baseline time range
    monthly_climatology = baseline_ds.groupby('time.month').mean(dim='time')
    
    # Calculate anomaly values
    ds_ocean_anomaly = ds_ocean.groupby('time.month') - monthly_climatology
    return ds_ocean_anomaly


def step4() -> xr.Dataset:
    """
    Step 4: Calculate Sea Surface Temperature (SST) Anomalies

    This function performs the following steps:
    1. Loads the SST dataset for the correct time range from 'sst.mnmean.nc'.
    2. Calculates SST anomalies using the inputted baseline range from '1951-01-01' to '1980-12-31'.

    Returns:
        xr.Dataset: A dataset containing Sea Surface Temperature anomalies.
    """
    # Create SST dataset for correct time range
    ds_ocean = sst_dataset(url=ERSST_url, start=start_date, end=end_date)

    # Calculate SST anomalies using inputted baseline range
    ds_ocean_anomaly = sst_anomaly(ds_ocean=ds_ocean, baseline_start=baseline_start_date, baseline_end=baseline_end_date)
    return ds_ocean_anomaly