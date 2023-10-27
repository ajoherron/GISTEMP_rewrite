"""
Execute steps of the GISTEMP algorithm.
"""

# Standard library imports
import sys
import os

# Add the parent directory to sys.path
current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

# Local imports
from steps import step0, step3

def main():

    try:
        # Formatting for stdout
        num_dashes: int = 25
        dashes: str = "-" * num_dashes

        # Execute Step 0
        # (Collect a dataframe of GHCN data)
        print(f"|{dashes} Running Step 0 {dashes}|")
        step0_output = step0.step0()
        print(step0_output)

        # Execute Step 3
        # Create the 2x2 grid 
        # (including station IDs and weights dictionary for each point in grid)
        print(f"|{dashes} Running Step 3 {dashes}|")
        step3_output = step3.step3()
        print(step3_output)

    # Handle exceptions
    except Exception as e:
        print(f'An error occurred: {e}')

# Main entry point
if __name__ == '__main__':
    main()