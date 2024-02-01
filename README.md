<u>Repo for upgrading GISTEMP v4.0 (last updated in 2016) to v5.0</u>

GISTEMP (GISS Surface Temperature Analysis) is an estimate of the global surface temperature change. The basic GISS temperature analysis scheme was defined in the late 1970s by James Hansen, when a method of estimating global temperature change was needed for comparison with 1-D global climate models. This analysis method was fully documented in [Hansen and Lebedeff 1987](https://pubs.giss.nasa.gov/abs/ha00700d.html). Several papers describing the updates to the analysis followed, most recently that of [Hansen et al. (2010)](https://pubs.giss.nasa.gov/abs/ha00510u.html) and [Lenssen et al. (2019)](https://pubs.giss.nasa.gov/abs/le05800h.html).

## Running locally
We recommend using a conda environment to manage dependencies and to avoid manually installing the required packages. Install Anaconda for your platform [here](https://docs.anaconda.com/anaconda/install/).

1. Create environment

    A. In your command line interface run: 

    ```conda env create -f environment.yml```

    B. If a conda environment already exists with the name gistemp, run:

    ```conda env update -f environment.yml --prune```

2. Activate environment

```conda activate gistemp```

3. Run the GISTEMP program

    A. To run GISTEMP with standard parameters & algorithm:
    
    ```python -m main.run```

    B. To run GISTEMP with user-set parameters and option of urban adjustment step:

    ```python -m main.run --urban_adjustment_option --start_year 1900 --end_year 2000```
    
    C. Lastly, an example of all command line arguments being used:

    ```python -m main.run  --urban_adjustment_option --start_year 1900 --end_year 2000 --baseline_start_year 1940 --baseline_end_year 1960 --nearby_station_radius 1000 --urban_nearby_radius 100 --urban_brightness_threshold 15```

Repository structure:
* docs:
    * Documentation for overall GISTEMP project
* main
    * Execution of all steps in GISTEMP algorithm
* parameters
    * Storing constants used throughout the repository
    * Data
        * NOAA GHCN v4 (meteorological stations)
        * ERSST v5 (ocean areas)
    * Rules used from dropping data
* plots
    * Notebooks for explaining GISTEMP & analyzing outputs
* steps
    * Steps 0-5, outlined in docs/overview.txt
* tools
    * Utility functions used for multiple files