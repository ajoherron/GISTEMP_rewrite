"""
Testing suite for functions in steps/ and testing/ directories
"""

# Standard library imports
import os
import pytest
import sys

# 3rd party imports
import pandas as pd
import numpy as np
import xarray as xr
from xarray import Dataset

# Get the parent directory of the current script
current_script_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.abspath(os.path.join(current_script_directory, os.pardir))

# Add the parent directory to the Python path
sys.path.append(parent_directory)

# Local imports (overall step functions)
from steps import step0, step1, step2, step3, step4, step5, step6

# Local imports (functions making up overall step functions)
from steps.step4 import add_brightness_to_df

# Local imports (tools functions)
from tools import utilities

# Local imports (data sources)
from parameters.data import GHCN_TEMP_URL, GHCN_META_URL, BRIGHTNESS_URL, ERSST_URL

# Local imports (constants)
from parameters.constants import (
    START_YEAR,
    END_YEAR,
    NEARBY_STATION_RADIUS,
    EARTH_RADIUS,
    BASELINE_START_YEAR,
    BASELINE_END_YEAR,
    URBAN_BRIGHTNESS_THRESHOLD,
    URBAN_NEARBY_RADIUS,
    MIN_NEARBY_RURAL_STATIONS,
    SST_CUTOFF_TEMP,
    URBAN_ADJUSTMENT_OPTION,
)

# Constants
TEST_DATA_DIR = "testing/test_data"
STEP0_TEST_DATA_PATH = os.path.join(TEST_DATA_DIR, "step0_test_data.csv")
STEP1_TEST_DATA_PATH = os.path.join(TEST_DATA_DIR, "step1_test_data.csv")
STEP2_TEST_DATA_PATH = os.path.join(TEST_DATA_DIR, "step2_test_data.csv")
STEP3_TEST_DATA_PATH = os.path.join(TEST_DATA_DIR, "step3_test_data.csv")
STEP4_TEST_DATA_PATH = os.path.join(TEST_DATA_DIR, "step4_test_data.csv")
STEP5_TEST_DATA_PATH = os.path.join(TEST_DATA_DIR, "step5_test_data.nc")
STEP6_TEST_DATA_PATH = os.path.join(TEST_DATA_DIR, "step6_test_data.nc")


# Fixture to provide paths to input and expected output files
@pytest.fixture
def file_paths():
    return {
        "step0": STEP0_TEST_DATA_PATH,
        "step1": STEP1_TEST_DATA_PATH,
        "step2": STEP2_TEST_DATA_PATH,
        "step3": STEP3_TEST_DATA_PATH,
        "step4": STEP4_TEST_DATA_PATH,
        "step5": STEP5_TEST_DATA_PATH,
        "step6": STEP6_TEST_DATA_PATH,
    }


def test_step0(file_paths):
    # Create GHCN dataframe with main step 0 function
    df0 = step0.step0(GHCN_TEMP_URL, GHCN_META_URL, START_YEAR, END_YEAR)

    # Test that start and end years are correct for land data
    numeric_columns = [
        col for col in df0.columns if col not in ["Latitude", "Longitude"]
    ]
    start_year = int(numeric_columns[0].split("_")[1])
    end_year = int(numeric_columns[-1].split("_")[1])
    assert start_year == START_YEAR
    assert end_year == END_YEAR

    # Test that the number of columns is correct (for base GISTEMP settings)
    df0_test = pd.read_csv(file_paths["step0"], index_col="Station_ID")
    num_columns = len(df0.columns)
    test_num_columns = len(df0_test.columns)
    assert num_columns == test_num_columns


def test_step1(file_paths):
    # Test that the coordinates are properly filtered
    latitude_max = 90
    latitude_min = -latitude_max
    longitude_max = 180
    longitude_min = -longitude_max
    df0 = pd.read_csv(file_paths["step0"], index_col="Station_ID")
    df1 = step1.step1(df0)
    latitude_values = df1["Latitude"].values
    longitude_values = df1["Longitude"].values
    assert max(latitude_values) <= latitude_max
    assert min(latitude_values) >= latitude_min
    assert max(longitude_values) <= longitude_max
    assert min(longitude_values) >= longitude_min


def test_step2():
    # Test that data types for grid columns are correct
    df2 = step2.step2(NEARBY_STATION_RADIUS, EARTH_RADIUS)
    column_data_types = df2.dtypes
    assert column_data_types["Latitude"] == float
    assert column_data_types["Latitude"] == float
    assert column_data_types["Nearby_Stations"] == dict

    # Test that the number of grid rows is correct
    num_latitude = 89
    num_longitude = 180
    num_polar = 2
    total_grid_points = (num_latitude * num_longitude) + num_polar
    assert len(df2) == total_grid_points


def test_step3(file_paths):
    # Test that anomaly values in step3 are within reasonable range
    anomaly_max = 30
    anomaly_min = -anomaly_max
    df1 = pd.read_csv(file_paths["step1"], index_col="Station_ID")
    df3 = step3.step3(df1, BASELINE_START_YEAR, BASELINE_END_YEAR)
    anomaly_columns = df3.drop(columns=["Latitude", "Longitude"])
    anomaly_values = anomaly_columns.values.flatten().tolist()
    cleaned_anomalies = [x for x in anomaly_values if not np.isnan(x)]
    assert min(cleaned_anomalies) > anomaly_min
    assert max(cleaned_anomalies) < anomaly_max


def test_step4(file_paths):
    df3 = pd.read_csv(file_paths["step3"], index_col="Station_ID")

    # Determine which rows are urban/rural
    df_brightness = add_brightness_to_df(
        df=df3,
        brightness_url=BRIGHTNESS_URL,
        meta_url=GHCN_META_URL,
    )
    df_urban = df_brightness[df_brightness["Value"] > URBAN_BRIGHTNESS_THRESHOLD]
    df_rural = df_brightness[df_brightness["Value"] <= URBAN_BRIGHTNESS_THRESHOLD]
    index_values_urban = df_urban.index
    index_values_rural = df_rural.index

    # Ensure that urban rows are adjusted, while rural rows are not
    df4 = step4.step4(
        df=df3,
        URBAN_BRIGHTNESS_THRESHOLD=URBAN_BRIGHTNESS_THRESHOLD,
        EARTH_RADIUS=EARTH_RADIUS,
        URBAN_NEARBY_RADIUS=URBAN_NEARBY_RADIUS,
        MIN_NEARBY_RURAL_STATIONS=MIN_NEARBY_RURAL_STATIONS,
        START_YEAR=START_YEAR,
        END_YEAR=END_YEAR,
        BRIGHTNESS_URL=BRIGHTNESS_URL,
        GHCN_META_URL=GHCN_META_URL,
    )
    df3_urban = df3[df3.index.isin(index_values_urban)]
    df3_rural = df3[df3.index.isin(index_values_rural)]
    df4_urban = df4[df4.index.isin(index_values_urban)]
    df4_rural = df4[df4.index.isin(index_values_rural)]
    assert df3_rural.equals(df4_rural)
    assert not df4_urban.equals(df3_urban)


# CAUSING NUMPY WARNING
# @pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_step5():
    # Test that start and end years are correct for ocean data
    ds5 = step5.step5(
        ERSST_URL=ERSST_URL,
        START_YEAR=START_YEAR,
        END_YEAR=END_YEAR,
        BASELINE_START_YEAR=BASELINE_START_YEAR,
        BASELINE_END_YEAR=BASELINE_END_YEAR,
        SST_CUTOFF_TEMP=SST_CUTOFF_TEMP,
    )
    min_year = ds5["time"].dt.year.min().item()
    max_year = ds5["time"].dt.year.max().item()
    assert START_YEAR == min_year
    assert END_YEAR == max_year


def test_step6(file_paths):
    # Create final result dataset
    df2 = step2.step2(NEARBY_STATION_RADIUS, EARTH_RADIUS)
    df3 = pd.read_csv(file_paths["step3"], index_col="Station_ID")
    ds5 = xr.open_dataset(file_paths["step5"])
    ds6 = step6.step6(df=df3, df_grid=df2, ds_ocean=ds5)

    # Confirm that output data has same coordinates as step 2 grid
    grid_latitudes = sorted(df2["Latitude"].unique().tolist())
    grid_longitudes = sorted(df2["Longitude"].unique().tolist())
    result_lat_values = sorted(list(ds6["lat"].values))
    result_lon_values = sorted(list(ds6["lon"].values))
    assert result_lat_values == grid_latitudes
    assert result_lon_values == grid_longitudes


def test_normalize_dict_values():
    # Normalize two different dictionaries
    test_dict_1 = {"This": 0.1, "sums": 0.2, "to": 0.3, "1": 0.4}
    test_dict_2 = {"This": 0.2, "sums": 0.4, "to": 0.6, "2": 0.8}
    normalized_dict_1 = utilities.normalize_dict_values(test_dict_1)
    normalized_dict_2 = utilities.normalize_dict_values(test_dict_2)

    # Check that normalized dictionaries sum to 1
    assert sum(normalized_dict_1.values()) == 1.0
    assert sum(normalized_dict_2.values()) == 1.0

    # Check that pre-normalized dictionary is not changed
    assert test_dict_1 == normalized_dict_1

    # Check that non-normalized dictionary is changed
    assert test_dict_2 != normalized_dict_2


def test_haversine_distance():
    # Test distances of 0 are correctly calculated
    assert (
        utilities.haversine_distance(
            lat1=0, lon1=0, lat2=0, lon2=0, earth_radius=EARTH_RADIUS
        )
        == 0.0
    )


def test_calculate_distances():
    # Test that this returns a numpy array of dimension n x n
    df = pd.read_csv("testing/test_data/step0_test_data.csv", index_col="Station_ID")
    n = 10
    df_a = df.head(n)
    df_b = df.tail(n)
    distances = utilities.calculate_distances(df_a, df_b, EARTH_RADIUS)
    assert len(distances) == n
    assert len(distances[0]) == n
