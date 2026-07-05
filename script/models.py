from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, model_validator

class BirthInfo(BaseModel):
    """Birth information for astrological calculations"""
    name: str = Field(..., description="Name of the person")
    birth_date: datetime = Field(..., description="Birth date and time")
    location: str = Field(..., description="Birth location (city, country)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "birth_date": "1990-01-01T12:00:00",
                "location": "New York, USA"
            }
        }

class GeoLocation(BaseModel):
    """Geographical location information"""
    latitude: float
    longitude: float
    formatted_address: str
    timezone: str = "UTC"
    # GeoLocation is a pure data model; service functions that construct
    # instances from strings or coordinates live in kerykeion_mcp.geo_service


class Coordinates(BaseModel):
    """Simple coordinates model for validating lat/lon inputs and optional tz string."""
    latitude: float
    longitude: float
    tz_str: Optional[str] = None

    @validator("latitude")
    def lat_range(cls, v):
        if v < -90 or v > 90:
            raise ValueError("latitude must be between -90 and 90")
        return v

    @validator("longitude")
    def lon_range(cls, v):
        if v < -180 or v > 180:
            raise ValueError("longitude must be between -180 and 180")
        return v


class NatalRequest(BaseModel):
    """Input payload for natal_chart.py."""
    name: str
    birth_date: datetime
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None

    @model_validator(mode="after")
    def validate_coordinates_pair(self):
        lat = self.latitude
        lon = self.longitude
        if (lat is None) ^ (lon is None):
            raise ValueError("'latitude' and 'longitude' must be provided together")
        return self


class PairChartRequest(BaseModel):
    """Input payload for synastry.py and composite.py."""
    person1: BirthInfo
    person2: BirthInfo
    person1_latitude: Optional[float] = None
    person1_longitude: Optional[float] = None
    person1_timezone: Optional[str] = None
    person2_latitude: Optional[float] = None
    person2_longitude: Optional[float] = None
    person2_timezone: Optional[str] = None

    @model_validator(mode="after")
    def validate_coordinates_pairs(self):
        p1_lat = self.person1_latitude
        p1_lon = self.person1_longitude
        p2_lat = self.person2_latitude
        p2_lon = self.person2_longitude

        if (p1_lat is None) ^ (p1_lon is None):
            raise ValueError("'person1_latitude' and 'person1_longitude' must be provided together")
        if (p2_lat is None) ^ (p2_lon is None):
            raise ValueError("'person2_latitude' and 'person2_longitude' must be provided together")
        return self


class SynastryRequest(PairChartRequest):
    """Input payload for synastry.py."""


class CompositeRequest(PairChartRequest):
    """Input payload for composite.py."""


class TransitsRequest(BaseModel):
    """Input payload for transits.py."""
    name: str
    birth_date: datetime
    location: str
    transit_date: Optional[datetime] = None
    transit_location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    transit_latitude: Optional[float] = None
    transit_longitude: Optional[float] = None
    transit_timezone: Optional[str] = None

    @model_validator(mode="after")
    def validate_coordinates_pairs(self):
        lat = self.latitude
        lon = self.longitude
        t_lat = self.transit_latitude
        t_lon = self.transit_longitude
        if (lat is None) ^ (lon is None):
            raise ValueError("'latitude' and 'longitude' must be provided together")
        if (t_lat is None) ^ (t_lon is None):
            raise ValueError("'transit_latitude' and 'transit_longitude' must be provided together")
        return self


class LunarReturnRequest(BaseModel):
    """Input payload for lunar_return.py."""
    name: str
    birth_date: datetime
    location: str
    start_date: Optional[datetime] = None
    return_location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    return_latitude: Optional[float] = None
    return_longitude: Optional[float] = None
    return_timezone: Optional[str] = None

    @model_validator(mode="after")
    def validate_coordinates_pairs(self):
        lat = self.latitude
        lon = self.longitude
        r_lat = self.return_latitude
        r_lon = self.return_longitude
        if (lat is None) ^ (lon is None):
            raise ValueError("'latitude' and 'longitude' must be provided together")
        if (r_lat is None) ^ (r_lon is None):
            raise ValueError("'return_latitude' and 'return_longitude' must be provided together")
        return self


class SolarReturnRequest(BaseModel):
    """Input payload for solar_return.py.

    Finds the exact moment the Sun returns to its natal degree (solar return),
    then computes the SR chart using the observer's current location for houses.
    """
    name: str
    birth_date: datetime
    location: str                          # birth location

    # Which year's solar return to find (default: current or next upcoming)
    year: Optional[int] = None

    # Where the person will be on their birthday (determines SR ASC/MC/houses)
    return_location: Optional[str] = None  # defaults to birth location if omitted

    # Pre-resolved natal coordinates (skips geocoding for birth location)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None

    # Pre-resolved return location coordinates
    return_latitude: Optional[float] = None
    return_longitude: Optional[float] = None
    return_timezone: Optional[str] = None

    @model_validator(mode="after")
    def validate_coordinates_pairs(self):
        if (self.latitude is None) ^ (self.longitude is None):
            raise ValueError("'latitude' and 'longitude' must be provided together")
        if (self.return_latitude is None) ^ (self.return_longitude is None):
            raise ValueError("'return_latitude' and 'return_longitude' must be provided together")
        return self

class PlanetInfo(BaseModel):
    """Information about a celestial body's position"""
    name: str
    sign: str
    degree: float
    house: int
    retrograde: bool

class HouseInfo(BaseModel):
    """Information about an astrological house"""
    number: int
    sign: str
    degree: float
    cusp: float

class AspectInfo(BaseModel):
    """Information about an astrological aspect"""
    planet1: str
    planet2: str
    aspect_type: str
    orb: float
    applying: bool

class AsteroidInfo(BaseModel):
    """Information about a meaningful asteroid"""
    name: str
    sign: str
    degree: float
    abs_pos: float
    house: int
    retrograde: bool

class NatalChart(BaseModel):
    """Complete natal chart information"""
    birth_info: BirthInfo
    geo_location: GeoLocation
    planets: List[PlanetInfo]
    houses: List[HouseInfo]
    aspects: List[AspectInfo]
    asteroids: List[AsteroidInfo] = Field(default_factory=list)
    asteroid_aspects: List[AspectInfo] = Field(default_factory=list)
    ascendant: float
    midheaven: float
    
class SynastryChart(BaseModel):
    """Synastry chart between two people"""
    person1: NatalChart
    person2: NatalChart
    aspects: List[AspectInfo]
    asteroid_contacts: List[AspectInfo] = Field(default_factory=list)
    relationship_themes: List[str] = Field(default_factory=list)

class CompositeChart(BaseModel):
    """Composite chart information"""
    person1: BirthInfo
    person2: BirthInfo
    composite_planets: List[PlanetInfo]
    composite_houses: List[HouseInfo]
    composite_aspects: List[AspectInfo]
    composite_asteroids: List[AsteroidInfo] = Field(default_factory=list)
    composite_asteroid_aspects: List[AspectInfo] = Field(default_factory=list)
    relationship_themes: List[str]

class TransitChart(BaseModel):
    """Transit chart information"""
    natal_chart: NatalChart
    transit_time: datetime
    transit_planets: List[PlanetInfo]
    transit_aspects: List[AspectInfo]
    transit_asteroids: List[AsteroidInfo] = Field(default_factory=list)
    transit_asteroid_aspects: List[AspectInfo] = Field(default_factory=list)
    current_themes: List[str]

class LunarReturnChart(BaseModel):
    """Lunar Return chart information"""
    chart: NatalChart
    return_time: datetime


class SolarReturnChart(BaseModel):
    """Solar Return chart information.

    sr_chart: NatalChart computed at sr_time + return_location (gives SR ASC/MC/houses).
    natal_chart: original birth chart for cross-aspect reference.
    sr_aspects: aspects between SR planets and natal planets.
    """
    natal_chart: NatalChart
    sr_chart: NatalChart
    sr_time: datetime
    sr_aspects: List[AspectInfo]
