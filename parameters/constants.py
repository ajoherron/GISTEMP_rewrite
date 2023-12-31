"""
Constants used throughout the GISTEMP algorithm
"""

# Years (integers)
START_YEAR = 1880
END_YEAR = 2023
BASELINE_START_YEAR = 1961
BASELINE_END_YEAR = 1990

# Dates (strings)
START_DATE = str(START_YEAR) + "-01-01"
END_DATE = str(END_YEAR) + "-12-01"
BASELINE_START_DATE = str(BASELINE_START_YEAR) + "-01-01"
BASELINE_END_DATE = str(BASELINE_END_YEAR) + "-12-31"

# Earth's radius (kilometers)
# (can update to be more accurate)
EARTH_RADIUS = 6371

# Radius within stations are considered "nearby" (kilometers)
NEARBY_STATION_RADIUS = 1200.0

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
