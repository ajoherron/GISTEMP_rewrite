"""
File used for functions shared between multiple steps
"""

# Standard library imports
import math

# 3rd party imports
import numpy as np


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    earth_radius: float,
) -> float:
    """
    Calculate the spherical distance (in kilometers) between two pairs of
    latitude and longitude coordinates using the Haversine formula.

    Args:
        lat1 (float): Latitude of the first point in degrees.
        lon1 (float): Longitude of the first point in degrees.
        lat2 (float): Latitude of the second point in degrees.
        lon2 (float): Longitude of the second point in degrees.

    Returns:
        float: Spherical distance in kilometers.
    """
    # Convert latitude and longitude from degrees to radians
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    # Haversine formula
    dlat: float = abs(lat2 - lat1)
    dlon: float = abs(lon2 - lon1)

    try:
        a: float = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c: float = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance: float = earth_radius * c

    except:
        # Otherwise set the distance just beyond the nearby radius
        distance = np.inf

    return distance


def linearly_decreasing_weight(distance: float, max_distance: float) -> float:
    """
    Calculate a linearly decreasing weight based on the given distance
    and maximum distance.

    Args:
        distance (float): The distance at which you want to calculate the weight.
        max_distance (float): The maximum distance at which the weight becomes 0.

    Returns:
        float: The linearly decreasing weight, ranging from 1 to 0.
    """
    # Ensure that distance is within the valid range [0, max_distance]
    distance: float = max(0, min(distance, max_distance))

    # Calculate the weight as a linear interpolation
    weight: float = 1.0 - (distance / max_distance)
    return weight


def normalize_dict_values(d: dict) -> dict:
    """
    Normalize the values of a dictionary to make their sum equal to 1.

    This function takes a dictionary as input and calculates the sum of its values. It then normalizes each value by dividing
    it by the total sum, ensuring that the sum of normalized values is 1. This is useful for converting a set of values into
    proportions or probabilities.

    Parameters:
        d (dict): A dictionary where values will be normalized.

    Returns:
        dict: A new dictionary with the same keys as the input, but with values normalized to ensure a sum of 1.
    """

    # Calculate the sum of all values in the dictionary
    total = sum(d.values())

    # Check if the total is not zero to avoid division by zero
    if total != 0:
        # Normalize each value by dividing by the total
        normalized_dict = {key: value / total for key, value in d.items()}
        return normalized_dict
    else:
        # Handle the case where the total is zero (all values are zero)
        return d  # Return the original dictionary
