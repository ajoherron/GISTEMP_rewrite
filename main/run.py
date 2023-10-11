"""
Execute steps of the GISTEMP algorithm.
"""

# Standard library imports
import sys
import os

# 3rd-party library imports
import pandas as pd

# Add the parent directory to sys.path
current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

# Local imports
from steps import step0

# Formatting for stdout
num_dashes: int = 25
dashes: str = "-" * num_dashes

# Step 0
print(f"|{dashes} Running Step 0 {dashes}|")
step0_output: pd.DataFrame = step0.step0()
print(step0_output)
