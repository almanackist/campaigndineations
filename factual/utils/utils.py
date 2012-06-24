"""
Utilities and helpers for the driver
"""

def circle(lat, lon, radius):
    """
    Creates an API-ready circle from the given latitude, longitude,
    and radius parameters
    """
    return {'$circle': {'$center': [lat, lon], '$meters': radius}}
