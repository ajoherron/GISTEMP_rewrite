File for keeping track of progress throughout the rewrite effort, as well as general documentation.

0. Step 0 implemented: Retrieval and formatting of GHCN temperature and metadata, formatted as a pandas dataframe
1. Step 3 implemented: Creation of a 2x2 (lat x lon) grid and a dictionary of station:weight key:value pairs for all stations within 1200km of a given grid point
2. Step 1 implemented: Cleaning GHCN data, both by filtering out bad coordinates and using drop_rules (adapted from Ts.strange file in GISTEMPv4)
3. Step 4 implemented: Creation of a SST xarray dataset using ERSST data (large temporary file created then deleted after creation of dataset)
4. Step 5 implemented: Calculation of land anomalies, which is then converted to an xarray dataset and combined with ocean anomalies into the final resulting dataset