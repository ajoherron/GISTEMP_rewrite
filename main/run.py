"""
Execute steps of the GISTEMP algorithm.
"""

# Standard library imports
import os
import time

# 3rd party imports
from xarray import Dataset

# Local imports (step functions)
from steps import step0, step1, step2, step3, step4, step5, step6

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
    START_DATE,
    END_DATE,
    BASELINE_START_DATE,
    BASELINE_END_DATE,
    SST_CUTOFF_TEMP,
)


def main() -> Dataset:
    try:
        # Start timer
        start = time.time()

        # Location for intermediate/final results
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)

        # Formatting for stdout
        num_dashes: int = 25
        dashes: str = "-" * num_dashes

        # Execute Step 0
        # (Create a dataframe of GHCN data)
        print(f"|{dashes} Running Step 0 {dashes}|")
        step0_output = step0.step0(GHCN_TEMP_URL, GHCN_META_URL, START_YEAR)
        step0_filename = "step0_output.csv"
        step0_filepath = os.path.join(results_dir, step0_filename)
        step0_output.to_csv(step0_filepath)

        # Execute Step 1
        # (Clean data (by coordinates / drop rules file)
        print(f"|{dashes} Running Step 1 {dashes}|")
        step1_output = step1.step1(step0_output)
        step1_filename = "step1_output.csv"
        step1_filepath = os.path.join(results_dir, step1_filename)
        step1_output.to_csv(step1_filepath)

        # Execute Step 2
        # (Create the 2x2 grid)
        print(f"|{dashes} Running Step 2 {dashes}|")
        step2_output = step2.step2(NEARBY_STATION_RADIUS, EARTH_RADIUS)
        step2_filename = "step2_output.csv"
        step2_filepath = os.path.join(results_dir, step2_filename)
        step2_output.to_csv(step2_filepath)

        # Execute Step 3
        # (Calculate land anomalies)
        print(f"|{dashes} Running Step 3 {dashes}|")
        step3_output = step3.step3(
            df=step1_output,
            ANOMALY_START_YEAR=BASELINE_START_YEAR,
            ANOMALY_END_YEAR=BASELINE_END_YEAR,
        )
        step3_filename = "step3_output.csv"
        step3_filepath = os.path.join(results_dir, step3_filename)
        step3_output.to_csv(step3_filepath)

        # Execute Step 4
        # (Urban Adjustment)
        print(f"|{dashes} Running Step 4 {dashes}|")
        step4_output = step4.step4(
            df=step3_output,
            URBAN_BRIGHTNESS_THRESHOLD=URBAN_BRIGHTNESS_THRESHOLD,
            EARTH_RADIUS=EARTH_RADIUS,
            URBAN_NEARBY_RADIUS=URBAN_NEARBY_RADIUS,
            MIN_NEARBY_RURAL_STATIONS=MIN_NEARBY_RURAL_STATIONS,
            START_YEAR=START_YEAR,
            END_YEAR=END_YEAR,
            BRIGHTNESS_URL=BRIGHTNESS_URL,
            GHCN_META_URL=GHCN_META_URL,
        )
        step4_filename = "step4_output.csv"
        step4_filepath = os.path.join(results_dir, step4_filename)
        step4_output.to_csv(step4_filepath)

        # Execute Step 5
        # (Calculate ocean anomalies)
        print(f"|{dashes} Running Step 5 {dashes}|")
        step5_output = step5.step5(
            ERSST_URL=ERSST_URL,
            START_DATE=START_DATE,
            END_DATE=END_DATE,
            BASELINE_START_DATE=BASELINE_START_DATE,
            BASELINE_END_DATE=BASELINE_END_DATE,
            SST_CUTOFF_TEMP=SST_CUTOFF_TEMP,
        )
        step5_filename = "step5_output.nc"
        step5_filepath = os.path.join(results_dir, step5_filename)
        step5_output.to_netcdf(step5_filepath)

        # Execute Step 6
        # (Combine land and ocean anomlies)
        print(f"|{dashes} Running Step 6 {dashes}|")
        step6_output = step6.step6(
            df_adjusted_urban=step4_output, df_grid=step2_output, ds_ocean=step5_output
        )
        step6_filename = "gistemp_result.nc"
        step6_filepath = os.path.join(results_dir, step6_filename)
        step6_output.to_netcdf(step6_filepath)
        print("\nGISS surface temperature analysis completed.")

        # Stop timer, format duration
        end = time.time()
        duration_seconds = round(end - start)
        hours, remainder = divmod(duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(
            f"\nTotal execution time: {int(hours)} hours {int(minutes)} minutes {seconds} seconds\n"
        )

    # Handle exceptions
    except Exception as e:
        print(f"An error occurred: {e}")


# Main entry point
if __name__ == "__main__":
    main()
