"""
Constants used throughout the GISTEMP algorithm
"""

# Standard library imports
import time

# Set start year and end year (use prior year if currently in January)
# (This accounts for 1 month lag time for measurements)
START_YEAR = 1880
current_time = time.gmtime()
END_YEAR = (
    current_time.tm_year if current_time.tm_mon != 1 else current_time.tm_year - 1
)

# Anomaly baseline period (integers)
BASELINE_START_YEAR = 1961
BASELINE_END_YEAR = 1990

# Earth's radius (kilometers)
# (can update to be more accurate)
EARTH_RADIUS = 6371

# Radius within stations are considered "nearby" (kilometers)
NEARBY_STATION_RADIUS = 1200.0

# Option to include urban adjustment option (set to True)
# Baseline excludes urban adjustment (set to False)
URBAN_ADJUSTMENT_OPTION = False

# Brightness above which stations are considered urban
URBAN_BRIGHTNESS_THRESHOLD = 10

# Minimum number of nearby rural stations needed for urban station
# (otherwise station is dropped)
MIN_NEARBY_RURAL_STATIONS = 3

# Radius of urban stations to find nearby rural stations
URBAN_NEARBY_RADIUS = 50.0

# Ocean temperature below which is considered ice
# (and consequently converted to NaN values)
SST_CUTOFF_TEMP = -1.77
