File for documenting changes/updates from gistemp4.0

- Change in primary data type: passing Pandas dataframes between steps instead of streaming individual records
- Shifting from the use of an equal area grid to a 2x2 lat x lon grid
- Integrating xarray for both ocean data and overall combined land / ocean dataset
- Restructuring order of steps to more logically follow the data structures and algorithm