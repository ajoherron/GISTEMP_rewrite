File for keeping track of progress throughout the rewrite effort, as well as general documentation.

Step implementation progress:
- Step 0: Retrieval and formatting of GHCN temperature and metadata, formatted as a pandas dataframe
- Step 1: Cleaning GHCN data, both by filtering out bad coordinates and using drop_rules (adapted from Ts.strange file in GISTEMPv4)
- Step 2: Creation of a 2x2 (lat x lon) grid and a dictionary of station:weight key:value pairs for all stations within 1200km of a given grid point
- Step 3: Calculation of land anomalies
- Step 4: Urban adjustment of land anomalies
- Step 5: Creation of a SST xarray dataset using ERSST data (large temporary file created then deleted after creation of dataset)
- Step 6: Conversion of land anomalies into xarray dataset, which is then combined with ocean anmolies into the final resulting dataset

Status update:
- Rough draft complete
- Sped up rough draft over 3x using numpy vectorization
- Added command line parameters