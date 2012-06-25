"""
Utilities and helpers for the driver
"""

def circle(lat, lon, radius):
    """
    Creates an API-ready circle from the given latitude, longitude,
    and radius parameters
    """
    return {'$circle': {'$center': [lat, lon], '$meters': radius}}

def point(lat, lon):
    """
    Creates an API-ready point from the given latitude and longitue.
    """
    return {'$point': [lat, lon]}
