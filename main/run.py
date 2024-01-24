"""
Execute steps of the GISTEMP algorithm.
"""

# Standard library imports
import os
import time
import argparse

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
    SST_CUTOFF_TEMP,
    URBAN_ADJUSTMENT_OPTION,
)


def parse_arguments():
    """
    Parse command-line arguments for executing the GISTEMP algorithm.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Execute steps of the GISTEMP algorithm."
    )
    parser.add_argument(
        "--urban_adjustment_option",
        type=bool,
        default=URBAN_ADJUSTMENT_OPTION,
        help="Option to include urban adjustment (baseline does not include urban adjustment)",
    )
    parser.add_argument(
        "--start_year",
        type=int,
        default=START_YEAR,
        help="Start year for processing data",
    )
    parser.add_argument(
        "--end_year", type=int, default=END_YEAR, help="End year for processing data"
    )
    parser.add_argument(
        "--baseline_start_year",
        type=int,
        default=BASELINE_START_YEAR,
        help="Start year for baseline anomaly period",
    )
    parser.add_argument(
        "--baseline_end_year",
        type=int,
        default=BASELINE_END_YEAR,
        help="End year for baseline anomaly period",
    )
    parser.add_argument(
        "--nearby_station_radius",
        type=int,
        default=NEARBY_STATION_RADIUS,
        help="Radius used for station anomaly calculation",
    )
    parser.add_argument(
        "--urban_nearby_radius",
        type=int,
        default=URBAN_NEARBY_RADIUS,
        help="Radius used for calculating urban adjustment",
    )
    parser.add_argument(
        "--urban_brightness_threshold",
        type=int,
        default=URBAN_BRIGHTNESS_THRESHOLD,
        help="Threshold for brightness above which stations are considered urban",
    )
    return parser.parse_args()


def main() -> Dataset:
    """
    Execute the GISTEMP algorithm and generate surface temperature anomalies.

    Returns:
        Dataset: Resulting surface temperature anomalies.
    """
    try:
        # Start timer
        start = time.time()

        # Parse command-line arguments
        args = parse_arguments()

        # Override constants with command-line arguments
        START_YEAR = args.start_year
        END_YEAR = args.end_year
        BASELINE_START_YEAR = args.baseline_start_year
        BASELINE_END_YEAR = args.baseline_end_year
        NEARBY_STATION_RADIUS = args.nearby_station_radius
        URBAN_NEARBY_RADIUS = args.urban_nearby_radius
        URBAN_BRIGHTNESS_THRESHOLD = args.urban_brightness_threshold
        URBAN_ADJUSTMENT_OPTION = args.urban_adjustment_option

        # Location for intermediate/final results
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)

        # Formatting for stdout
        num_dashes: int = 25
        dashes: str = "-" * num_dashes

        # Execute Step 0
        # (Create a dataframe of GHCN data)
        print(f"|{dashes} Running Step 0 {dashes}|")
        step0_output = step0.step0(GHCN_TEMP_URL, GHCN_META_URL, START_YEAR, END_YEAR)
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

        # Execute Step 4 if option is set to True
        # (Urban adjustment)
        if URBAN_ADJUSTMENT_OPTION:
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
        else:
            step4_output = step3_output

        # Execute Step 5
        # (Calculate ocean anomalies)
        print(f"|{dashes} Running Step 5 {dashes}|")
        step5_output = step5.step5(
            ERSST_URL=ERSST_URL,
            START_YEAR=START_YEAR,
            END_YEAR=END_YEAR,
            BASELINE_START_YEAR=BASELINE_START_YEAR,
            BASELINE_END_YEAR=BASELINE_END_YEAR,
            SST_CUTOFF_TEMP=SST_CUTOFF_TEMP,
        )
        step5_filename = "step5_output.nc"
        step5_filepath = os.path.join(results_dir, step5_filename)
        step5_output.to_netcdf(step5_filepath)

        # Execute Step 6
        # (Combine land and ocean anomlies)
        print(f"|{dashes} Running Step 6 {dashes}|")
        step6_output = step6.step6(
            df=step4_output, df_grid=step2_output, ds_ocean=step5_output
        )
        step6_filename = "gistemp_result.nc"
        step6_filepath = os.path.join(results_dir, step6_filename)
        step6_output.to_netcdf(step6_filepath)

        # Stop timer, format duration
        end = time.time()
        duration_seconds = round(end - start)
        hours, remainder = divmod(duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(
            f"\nTotal execution time: {int(hours)} hours {int(minutes)} minutes {seconds} seconds"
        )
        print("\nGISS surface temperature analysis completed.\n")

    # Handle exceptions
    except Exception as e:
        print(f"An error occurred: {e}")


# Main entry point
if __name__ == "__main__":
    main()
