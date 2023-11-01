"""
Execute steps of the GISTEMP algorithm.
"""

# Standard library imports
import sys
import os

# 3rd party imports
from xarray import Dataset

# Add the parent directory to sys.path
current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

# Local imports
from steps import step0, step1, step3, step4, step5
from parameters.constants import ANOMALY_START_YEAR, ANOMALY_END_YEAR


def main() -> Dataset:

    try:
        # Formatting for stdout
        num_dashes: int = 25
        dashes: str = "-" * num_dashes

        # Execute Step 0
        # (Create a dataframe of GHCN data)
        print(f"|{dashes} Running Step 0 {dashes}|")
        step0_output = step0.step0()
        print(step0_output)

        # Execute Step 1
        # (Clean data (by coordinates / drop rules file)
        print(f"|{dashes} Running Step 1 {dashes}|")
        step1_output = step1.step1(step0_output)
        print(step1_output)

        # # Execute Step 3
        # (Create the 2x2 grid)
        print(f"|{dashes} Running Step 3 {dashes}|")
        step3_output = step3.step3()
        print(step3_output)

        # Execute Step 4
        # (Create a dataset of ERSST data)
        print(f"|{dashes} Running Step 4 {dashes}|")
        step4_output = step4.step4()
        print(step4_output)

        # Execute Step 5 and return output
        # (Create dataset of combined land/ocean anomalies)
        print(f"|{dashes} Running Step 5 {dashes}|")
        step5_output = step5.step5(df_temperature=step1_output,
                                   grid=step3_output,
                                   ds_ocean=step4_output,
                                   anomaly_start_year=ANOMALY_START_YEAR,
                                   anomaly_end_year=ANOMALY_END_YEAR)
        print(step5_output)
        return step5_output

    # Handle exceptions
    except Exception as e:
        print(f'An error occurred: {e}')

# Main entry point
if __name__ == '__main__':
    main()