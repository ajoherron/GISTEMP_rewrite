File for keeping track of progress throughout the rewrite effort, as well as general documentation.

Step implementation progress:
- Step 0: Retrieval and formatting of GHCN temperature and metadata, formatted as a pandas dataframe
- Step 1: Cleaning GHCN data, both by filtering out bad coordinates and using drop_rules (adapted from Ts.strange file in GISTEMPv4)
- Step 2: Creation of a 2x2 (lat x lon) grid and a dictionary of station:weight key:value pairs for all stations within 1200km of a given grid point
- Step 3: Calculation of land anomalies
- Step 4: Urban adjustment of land anomalies
- Step 5: Creation of a SST anomaly xarray dataset using ERSST data (large temporary file created then deleted after creation of dataset)
- Step 6: Conversion of land anomalies into xarray dataset, which is then combined with ocean anomalies into the final resulting dataset

IMPORTANT NOTE:
- Although rough drafts of each step has been completed, there is a divergence in results in Step 3: calculation of land anomalies
  - Steps 0, 1, and 2 have comparable results to gistempv4.0
  - Steps 3, 4, 5, and 6 do not
- The GISTEMP_light repository was created to try to troubleshoot the main problem of **gridding the data**, however was not successful in completing this task
  - This would be the next step, if someone were to pick up the GISTEMP_rewrite
 
NOTE ON GRIDDING / ANOMALY CALCULATION:
- There is a difference between GISTEMP_rewrite and GISTEMP_light regarding the ordering of anomaly calculation
- GISTEMP_rewrite:
  - Gridding and land anomaly calculation are both accomplished in Step 3
  - Ocean anomalies are calculated Step 5
  - Ocean and land anomalies are combined in Step 6
- GISTEMP_light:
  - Only focused on gridding
    - Discussion with Reto determined that it would be easier / more flexible to have the output be gridded time series data set
    - Steps 0, 1, and 2 can be run
    - Then, the gridding.ipynb notebook can be used to troubleshoot the gridding algorithm and compare with gistemp4.0 results
  - Then, anomalies could be calculated as a post-processing step
    - This would allow for various different baseline periods (e.g., 1951-1980 vs. 1961-1990) without re-running the entire script
