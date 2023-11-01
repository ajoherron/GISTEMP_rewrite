"""
Constants used throughout the GISTEMP algorithm
"""

# Earth's radius (kilometers)
# (can update to be more accurate)
EARTH_RADIUS = 6371

# Radius within stations are considered "nearby" (kilometers)
NEARBY_STATION_RADIUS = 1200.0

# Years (integers)
START_YEAR = 1880
ANOMALY_START_YEAR = 1951
ANOMALY_END_YEAR = 1980

# Dates (strings)
START_DATE = '1880-01-01'
END_DATE = '2023-12-01'
BASELINE_START_DATE = '1950-01-01'
BASELINE_END_DATE = '1980-12-31'
