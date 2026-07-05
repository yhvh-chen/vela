from typing import Optional
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

try:
    from timezonefinder import TimezoneFinder
    _TF = TimezoneFinder()
except Exception:
    _TF = None

from models import GeoLocation


async def from_location_string(location: str) -> GeoLocation:
    """Resolve a location string to a GeoLocation using geopy and timezonefinder."""
    try:
        geolocator = Nominatim(user_agent="kerykeion-mcp")
        location_data = geolocator.geocode(location, timeout=10)
        if not location_data:
            raise ValueError(f"Could not find location: {location}")

        tz = None
        if _TF is not None:
            try:
                tz = _TF.timezone_at(lng=location_data.longitude, lat=location_data.latitude)
            except Exception:
                tz = None
        if not tz:
            tz = "UTC"

        return GeoLocation(
            latitude=location_data.latitude,
            longitude=location_data.longitude,
            formatted_address=location_data.address,
            timezone=tz,
        )
    except GeocoderTimedOut:
        raise ValueError("Geocoding service timeout. Please try again.")
    except Exception as e:
        raise ValueError(f"Error getting location data: {str(e)}")


async def from_coordinates(latitude: float, longitude: float, tz_str: Optional[str] = None) -> GeoLocation:
    """Reverse-geocode coordinates to a GeoLocation and try to derive timezone."""
    try:
        geolocator = Nominatim(user_agent="kerykeion-mcp")
        location_data = geolocator.reverse((latitude, longitude), exactly_one=True, timeout=10)

        if location_data:
            formatted = location_data.address
        else:
            formatted = f"Coordinates: {latitude}, {longitude}"

        tz = tz_str
        if not tz and _TF is not None:
            try:
                tz = _TF.timezone_at(lng=longitude, lat=latitude)
            except Exception:
                tz = None
        if not tz:
            tz = "UTC"

        return GeoLocation(
            latitude=latitude,
            longitude=longitude,
            formatted_address=formatted,
            timezone=tz,
        )
    except GeocoderTimedOut:
        raise ValueError("Geocoding service timeout. Please try again.")
    except Exception as e:
        raise ValueError(f"Error reverse geocoding: {str(e)}")
