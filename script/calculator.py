from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import re

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger("kerykeion_mcp.calculator")

import swisseph as swe
from kerykeion.main import KrInstance
from kerykeion.aspects import NatalAspects, CompositeAspects
from kerykeion.utilities import calculate_position
from models import (
    BirthInfo, GeoLocation, NatalChart, SynastryChart, CompositeChart,
    TransitChart, PlanetInfo, HouseInfo, AspectInfo, AsteroidInfo, LunarReturnChart,
    SolarReturnChart
)

def _parse_house_string(house: Any) -> int:
    """Parses a house string (e.g., 'First House') or int into an integer."""
    if isinstance(house, int):
        return house
    if isinstance(house, str):
        match = re.search(r'\d+', house)
        if match:
            return int(match.group(0))
        ord_map = {
            "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
            "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10, "eleventh": 11, "twelfth": 12,
        }
        lowered = house.lower()
        for key, val in ord_map.items():
            if key in lowered:
                return val
    return 0


EPHE_PATH = Path(__file__).resolve().parent / "ephe"
ASTEROID_BODY_IDS: dict[str, int] = {
    "Ceres": swe.CERES,
    "Pallas": swe.PALLAS,
    "Juno": swe.JUNO,
    "Vesta": swe.VESTA,
}
MAJOR_ASPECTS: tuple[tuple[float, str], ...] = (
    (0.0, "conjunction"),
    (60.0, "sextile"),
    (90.0, "square"),
    (120.0, "trine"),
    (150.0, "quincunx"),
    (180.0, "opposition"),
)
ASTEROID_ORB_LIMIT = 4.5


def _ensure_ephe_path() -> None:
    if EPHE_PATH.exists():
        swe.set_ephe_path(str(EPHE_PATH))


def _label(owner: str, name: str) -> str:
    return f"{owner} {name}" if owner else name


def _house_cusps(subject: KrInstance) -> list[float]:
    return [
        float(subject.first_house.abs_pos),
        float(subject.second_house.abs_pos),
        float(subject.third_house.abs_pos),
        float(subject.fourth_house.abs_pos),
        float(subject.fifth_house.abs_pos),
        float(subject.sixth_house.abs_pos),
        float(subject.seventh_house.abs_pos),
        float(subject.eighth_house.abs_pos),
        float(subject.ninth_house.abs_pos),
        float(subject.tenth_house.abs_pos),
        float(subject.eleventh_house.abs_pos),
        float(subject.twelfth_house.abs_pos),
    ]


def _house_from_abs_pos(abs_pos: float, cusps: list[float]) -> int:
    value = abs_pos % 360.0
    for idx, start in enumerate(cusps):
        end = cusps[(idx + 1) % len(cusps)]
        if start <= end:
            if start <= value < end:
                return idx + 1
        elif value >= start or value < end:
            return idx + 1
    return 1


def _aspect_info(
    name1: str,
    abs1: float,
    name2: str,
    abs2: float,
    *,
    owner1: str = "",
    owner2: str = "",
    orb_limit: float = ASTEROID_ORB_LIMIT,
) -> AspectInfo | None:
    diff = abs((abs1 - abs2) % 360.0)
    if diff > 180.0:
        diff = 360.0 - diff
    nearest = min(MAJOR_ASPECTS, key=lambda item: abs(diff - item[0]))
    orb = diff - nearest[0]
    if abs(orb) > orb_limit:
        return None
    return AspectInfo(
        planet1=_label(owner1, name1),
        planet2=_label(owner2, name2),
        aspect_type=nearest[1],
        orb=orb,
        applying=orb > 0,
    )


def _circular_midpoint(a: float, b: float) -> float:
    """Shorter-arc midpoint of two ecliptic longitudes."""
    diff = ((b - a + 540.0) % 360.0) - 180.0
    return (a + diff / 2.0) % 360.0


def _chiron_of(subject: KrInstance) -> AsteroidInfo | None:
    """Chiron via Swiss Ephemeris (kerykeion 3.4 does not compute it). Uses seas_18.se1."""
    _ensure_ephe_path()
    try:
        result = swe.calc(subject.julian_day, swe.CHIRON, swe.FLG_SWIEPH + swe.FLG_SPEED)
    except Exception:
        return None
    position = result[0]
    abs_pos = float(position[0]) % 360.0
    sign_point = calculate_position(abs_pos, "Sun", point_type="Planet")
    speed = float(position[3]) if len(position) > 3 else 0.0
    return AsteroidInfo(
        name="Chiron",
        sign=sign_point.sign,
        degree=sign_point.position,
        abs_pos=abs_pos,
        house=_house_from_abs_pos(abs_pos, _house_cusps(subject)),
        retrograde=speed < 0.0,
    )


def _subject_planet_refs(subject: KrInstance, owner: str = "") -> list[tuple[str, float]]:
    refs = [(_label(owner, planet.name), float(planet.abs_pos)) for planet in subject.planets_list]
    chiron = _chiron_of(subject)
    if chiron is not None:
        refs.append((_label(owner, "Chiron"), float(chiron.abs_pos)))
    refs.append((_label(owner, "First House"), float(subject.first_house.abs_pos)))
    refs.append((_label(owner, "Tenth House"), float(subject.tenth_house.abs_pos)))
    return refs


def _karmic_refs(subject: KrInstance) -> list[tuple[str, float]]:
    """True Node + Chiron — the karmic-teacher points for cross-chart contacts."""
    refs = [
        (planet.name, float(planet.abs_pos))
        for planet in subject.planets_list
        if planet.name == "True_Node"
    ]
    chiron = _chiron_of(subject)
    if chiron is not None:
        refs.append(("Chiron", float(chiron.abs_pos)))
    return refs


def _asteroid_refs(asteroids: list[AsteroidInfo], owner: str = "") -> list[tuple[str, float]]:
    return [(_label(owner, asteroid.name), float(asteroid.abs_pos)) for asteroid in asteroids]


def _contacts(
    source: list[tuple[str, float]],
    target: list[tuple[str, float]],
    *,
    owner1: str = "",
    owner2: str = "",
) -> list[AspectInfo]:
    contacts: list[AspectInfo] = []
    for source_name, source_abs in source:
        for target_name, target_abs in target:
            aspect = _aspect_info(
                source_name,
                source_abs,
                target_name,
                target_abs,
                owner1=owner1,
                owner2=owner2,
            )
            if aspect is not None:
                contacts.append(aspect)
    return contacts


def _asteroid_theme(aspect: AspectInfo) -> str | None:
    pair = {aspect.planet1.split()[-1], aspect.planet2.split()[-1]}
    if "Juno" in pair:
        return f"{aspect.planet1} {aspect.aspect_type} {aspect.planet2}: commitment and reciprocity"
    if "Vesta" in pair:
        return f"{aspect.planet1} {aspect.aspect_type} {aspect.planet2}: devotion and focus"
    if "Ceres" in pair:
        return f"{aspect.planet1} {aspect.aspect_type} {aspect.planet2}: care and nourishment"
    if "Pallas" in pair:
        return f"{aspect.planet1} {aspect.aspect_type} {aspect.planet2}: strategy and pattern recognition"
    return None


def _theme_list_from_contacts(contacts: list[AspectInfo], limit: int = 4) -> list[str]:
    themes: list[str] = []
    for contact in contacts:
        theme = _asteroid_theme(contact)
        if theme and theme not in themes:
            themes.append(theme)
        if len(themes) >= limit:
            break
    return themes


def _asteroids_for_subject(subject: KrInstance) -> list[AsteroidInfo]:
    _ensure_ephe_path()
    if not EPHE_PATH.exists():
        raise FileNotFoundError(
            f"Missing Swiss Ephemeris asteroid file in {EPHE_PATH}. "
            "Add seas_18.se1 to enable Ceres, Pallas, Juno, and Vesta."
        )

    cusps = _house_cusps(subject)
    asteroids: list[AsteroidInfo] = []
    for name, body_id in ASTEROID_BODY_IDS.items():
        result = swe.calc(subject.julian_day, body_id, swe.FLG_SWIEPH + swe.FLG_SPEED)
        position = result[0]
        abs_pos = float(position[0]) % 360.0
        sign_point = calculate_position(abs_pos, "Sun", point_type="Planet")
        speed = float(position[3]) if len(position) > 3 else 0.0
        asteroids.append(
            AsteroidInfo(
                name=name,
                sign=sign_point.sign,
                degree=sign_point.position,
                abs_pos=abs_pos,
                house=_house_from_abs_pos(abs_pos, cusps),
                retrograde=speed < 0,
            )
        )
    return asteroids

class KerykeionCalculator:
    """Core calculator class for astrological computations using kerykeion v3.4.3"""

    @staticmethod
    async def create_subject(birth_info: BirthInfo, geo_location: GeoLocation) -> KrInstance:
        """Create a Kerykeion KrInstance from birth and location info."""
        birth_time = birth_info.birth_date

        # Attempt to extract city and nation from formatted_address
        city = None
        nation = None
        
        if not geo_location.formatted_address.startswith("Coordinates:"):
            address_parts = [part.strip() for part in geo_location.formatted_address.split(',')]
            if len(address_parts) >= 2:
                nation = address_parts[-1]
                city = address_parts[0]

        subject = KrInstance(
            name=birth_info.name,
            year=birth_time.year,
            month=birth_time.month,
            day=birth_time.day,
            hour=birth_time.hour,
            minute=birth_time.minute,
            lng=geo_location.longitude,
            lat=geo_location.latitude,
            tz_str=geo_location.timezone,
            city=city,
            nation=nation,
            online=True, # Changed to True to allow online data fetching for Kerykeion
        )
        return subject

    @staticmethod
    def _get_planet_info(subject: KrInstance) -> List[PlanetInfo]:
        """Extract planet information from a KrInstance."""
        planets: List[PlanetInfo] = []
        for planet in subject.planets_list:
            planets.append(PlanetInfo(
                name=planet.name,
                sign=planet.sign,
                degree=planet.position,
                house=_parse_house_string(planet.house),
                retrograde=planet.retrograde
            ))
        chiron = _chiron_of(subject)
        if chiron is not None:
            planets.append(PlanetInfo(
                name="Chiron",
                sign=chiron.sign,
                degree=chiron.degree,
                house=chiron.house,
                retrograde=chiron.retrograde,
            ))
        return planets

    @staticmethod
    def _get_house_info(subject: KrInstance) -> List[HouseInfo]:
        """Extract house information from a KrInstance."""
        houses: List[HouseInfo] = []
        ordinals = [
            "first_house", "second_house", "third_house", "fourth_house", "fifth_house", "sixth_house",
            "seventh_house", "eighth_house", "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
        ]
        for idx, attr_name in enumerate(ordinals, 1):
            house_obj = getattr(subject, attr_name)
            houses.append(HouseInfo(
                number=idx,
                sign=house_obj.sign,
                degree=house_obj.position,
                cusp=house_obj.position
            ))
        return houses

    @staticmethod
    def _get_aspect_info(aspects: List[Dict[str, Any]]) -> List[AspectInfo]:
        """Convert Kerykeion aspect dictionaries to AspectInfo models."""
        result = []
        for aspect in aspects:
            orb = aspect.get("orbit", 0.0)
            result.append(AspectInfo(
                planet1=aspect["p1_name"],
                planet2=aspect["p2_name"],
                aspect_type=aspect["aspect"],
                orb=orb,
                applying=orb > 0
            ))
        return result

    @staticmethod
    def _extract_numeric(subject: KrInstance, candidates: List[str], default: float = 0.0) -> float:
        """Extract a numeric value from a list of possible attributes on the subject."""
        for name in candidates:
            val = getattr(subject, name, None)
            if val is None:
                continue
            if isinstance(val, (int, float)):
                return float(val)
            if hasattr(val, "position") and isinstance(val.position, (int, float)):
                return float(val.position)
        return default

    @classmethod
    async def calculate_natal_chart(cls, birth_info: BirthInfo, geo_location: GeoLocation) -> NatalChart:
        """
        Calculate a complete natal chart.

        This tool requires two parameters, `birth_info` and `geo_location`, which must be provided as JSON objects.

        Args:
            birth_info (BirthInfo): A JSON object containing the person's birth details.
                - name (str): The name of the person.
                - birth_date (str): The full birth date and time in ISO 8601 format (e.g., "1999-09-09T09:09:0").
                - location (str): The birth location as a simple string (e.g., "New York, USA").
                Example:
                {
                    "name": "Jimmy",
                    "birth_date": "1999-09-09T09:09:09",
                    "location": "New York, USA"
                }

            geo_location (GeoLocation): A JSON object containing the geographical coordinates and timezone.
                - latitude (float): The latitude of the location.
                - longitude (float): The longitude of the location.
                - formatted_address (str): The full, verified address of the location.
                - timezone (str): The IANA timezone name (e.g., "Asia/Shanghai").
                Example:
                {
                    "latitude": 40.7128,
                    "longitude": 74.0060,
                    "formatted_address": "New York, USA",
                    "timezone": "America/New york"
                }
        """
        subject = await cls.create_subject(birth_info, geo_location)
        natal_aspects = NatalAspects(subject)
        all_aspects = natal_aspects.get_all_aspects()
        asteroids = _asteroids_for_subject(subject)
        asteroid_aspects = _contacts(_asteroid_refs(asteroids), _subject_planet_refs(subject))

        aspects = cls._get_aspect_info(all_aspects)
        chiron = _chiron_of(subject)
        if chiron is not None:
            targets = [ref for ref in _subject_planet_refs(subject) if ref[0] != "Chiron"]
            aspects.extend(_contacts([("Chiron", float(chiron.abs_pos))], targets))

        return NatalChart(
            birth_info=birth_info,
            geo_location=geo_location,
            planets=cls._get_planet_info(subject),
            houses=cls._get_house_info(subject),
            aspects=aspects,
            asteroids=asteroids,
            asteroid_aspects=asteroid_aspects,
            ascendant=cls._extract_numeric(subject, ["first_house", "ASC", "ascendant"]),
            midheaven=cls._extract_numeric(subject, ["tenth_house", "MC", "mc"])
        )

    @classmethod
    async def calculate_synastry(
        cls, person1_info: BirthInfo, person1_geo: GeoLocation,
        person2_info: BirthInfo, person2_geo: GeoLocation
    ) -> SynastryChart:
        """Calculate synastry between two charts."""
        subject1 = await cls.create_subject(person1_info, person1_geo)
        subject2 = await cls.create_subject(person2_info, person2_geo)
        asteroids1 = _asteroids_for_subject(subject1)
        asteroids2 = _asteroids_for_subject(subject2)

        synastry = CompositeAspects(subject1, subject2)
        syn_aspects = synastry.get_all_aspects()
        asteroid_contacts = _contacts(
            _asteroid_refs(asteroids1),
            _subject_planet_refs(subject2) + _asteroid_refs(asteroids2),
            owner1=person1_info.name,
            owner2=person2_info.name,
        ) + _contacts(
            _asteroid_refs(asteroids2),
            _subject_planet_refs(subject1) + _asteroid_refs(asteroids1),
            owner1=person2_info.name,
            owner2=person1_info.name,
        )

        # Karmic-teacher layer: True Node and Chiron cross-contacts, which the
        # kerykeion cross-aspect engine leaves out.
        karmic_exclude = ("True_Node", "Mean_Node", "Chiron")
        karmic_contacts = _contacts(
            _karmic_refs(subject1),
            [ref for ref in _subject_planet_refs(subject2) if ref[0] != "Mean_Node"],
            owner1=person1_info.name,
            owner2=person2_info.name,
        ) + _contacts(
            _karmic_refs(subject2),
            [ref for ref in _subject_planet_refs(subject1) if ref[0] not in karmic_exclude],
            owner1=person2_info.name,
            owner2=person1_info.name,
        )
        asteroid_contacts += karmic_contacts
        relationship_themes = _theme_list_from_contacts(asteroid_contacts)

        return SynastryChart(
            person1=await cls.calculate_natal_chart(person1_info, person1_geo),
            person2=await cls.calculate_natal_chart(person2_info, person2_geo),
            aspects=cls._get_aspect_info(syn_aspects),
            asteroid_contacts=asteroid_contacts,
            relationship_themes=relationship_themes,
        )

    @classmethod
    async def calculate_composite(
        cls, person1_info: BirthInfo, person1_geo: GeoLocation,
        person2_info: BirthInfo, person2_geo: GeoLocation
    ) -> CompositeChart:
        """Approximates a composite chart by averaging planet positions."""
        subject1 = await cls.create_subject(person1_info, person1_geo)
        subject2 = await cls.create_subject(person2_info, person2_geo)
        asteroids1 = _asteroids_for_subject(subject1)
        asteroids2 = _asteroids_for_subject(subject2)

        # Midpoint-composite house cusps (pairwise shorter-arc midpoints).
        cusps1 = _house_cusps(subject1)
        cusps2 = _house_cusps(subject2)
        composite_cusps = [_circular_midpoint(c1, c2) for c1, c2 in zip(cusps1, cusps2)]
        composite_houses: list[HouseInfo] = []
        for number, cusp in enumerate(composite_cusps, start=1):
            cusp_point = calculate_position(cusp, "Sun", point_type="Planet")
            composite_houses.append(HouseInfo(
                number=number,
                sign=cusp_point.sign,
                degree=cusp_point.position,
                cusp=cusp_point.position,
            ))

        # Midpoint-composite planets (shorter-arc midpoints of absolute longitudes).
        composite_planets: list[PlanetInfo] = []
        composite_planet_refs: list[tuple[str, float]] = []
        pairs = list(zip(subject1.planets_list, subject2.planets_list))
        chiron1, chiron2 = _chiron_of(subject1), _chiron_of(subject2)
        if chiron1 is not None and chiron2 is not None:
            pairs.append((chiron1, chiron2))
        for p1, p2 in pairs:
            name = "Chiron" if p1 is chiron1 else p1.name
            if name == "Mean_Node":
                continue
            mid = _circular_midpoint(float(p1.abs_pos), float(p2.abs_pos))
            mid_point = calculate_position(mid, "Sun", point_type="Planet")
            composite_planets.append(PlanetInfo(
                name=name,
                sign=mid_point.sign,
                degree=mid_point.position,
                house=_house_from_abs_pos(mid, composite_cusps),
                retrograde=False,
            ))
            composite_planet_refs.append((name, mid))

        # Aspects *within* the composite chart (not cross-chart contacts).
        composite_aspects: list[AspectInfo] = []
        for i in range(len(composite_planet_refs)):
            for j in range(i + 1, len(composite_planet_refs)):
                name_i, pos_i = composite_planet_refs[i]
                name_j, pos_j = composite_planet_refs[j]
                aspect = _aspect_info(name_i, pos_i, name_j, pos_j, orb_limit=6.0)
                if aspect is not None:
                    composite_aspects.append(aspect)

        composite_asteroids: list[AsteroidInfo] = []
        for asteroid1, asteroid2 in zip(asteroids1, asteroids2):
            mid = _circular_midpoint(float(asteroid1.abs_pos), float(asteroid2.abs_pos))
            sign_point = calculate_position(mid, "Sun", point_type="Planet")
            composite_asteroids.append(
                AsteroidInfo(
                    name=asteroid1.name,
                    sign=sign_point.sign,
                    degree=sign_point.position,
                    abs_pos=mid,
                    house=_house_from_abs_pos(mid, composite_cusps),
                    retrograde=False,
                )
            )

        composite_asteroid_aspects = _contacts(
            _asteroid_refs(composite_asteroids),
            composite_planet_refs,
        )

        themes = []
        for aspect in composite_aspects:
            planets = {aspect.planet1, aspect.planet2}
            if ('Venus' in planets or 'Jupiter' in planets) and aspect.aspect_type in ('trine', 'sextile'):
                themes.append("Harmonious Venus/Jupiter influence")
                break
        themes.extend(_theme_list_from_contacts(composite_asteroid_aspects))

        return CompositeChart(
            person1=person1_info,
            person2=person2_info,
            composite_planets=composite_planets,
            composite_houses=composite_houses,
            composite_aspects=composite_aspects,
            composite_asteroids=composite_asteroids,
            composite_asteroid_aspects=composite_asteroid_aspects,
            relationship_themes=themes
        )

    @classmethod
    async def calculate_transits(
        cls, birth_info: BirthInfo, natal_geo_location: GeoLocation,
        transit_geo_location: GeoLocation,
        transit_time: Optional[datetime] = None
    ) -> TransitChart:
        """Calculate transit chart."""
        natal_subject = await cls.create_subject(birth_info, natal_geo_location)
        transit_time = transit_time or datetime.now()
        natal_asteroids = _asteroids_for_subject(natal_subject)

        transit_info = BirthInfo(
            name="Transit",
            birth_date=transit_time,
            location=transit_geo_location.formatted_address
        )
        transit_subject = await cls.create_subject(transit_info, transit_geo_location)
        transit_aspects_obj = CompositeAspects(natal_subject, transit_subject)
        transit_aspects = transit_aspects_obj.get_all_aspects()
        transit_asteroids = _asteroids_for_subject(transit_subject)
        transit_asteroid_aspects = _contacts(
            _asteroid_refs(transit_asteroids),
            _subject_planet_refs(natal_subject) + _asteroid_refs(natal_asteroids),
            owner1="Transit",
            owner2=birth_info.name,
        )

        themes = []
        for aspect in transit_aspects:
            if aspect['p1_name'] == 'Jupiter':
                themes.append(f"Growth opportunities through {aspect['p2_name']}")
            elif aspect['p1_name'] == 'Saturn':
                themes.append(f"Learning lessons through {aspect['p2_name']}")
        themes.extend(_theme_list_from_contacts(transit_asteroid_aspects))

        return TransitChart(
            natal_chart=await cls.calculate_natal_chart(birth_info, natal_geo_location),
            transit_time=transit_time,
            transit_planets=cls._get_planet_info(transit_subject),
            transit_aspects=cls._get_aspect_info(transit_aspects),
            transit_asteroids=transit_asteroids,
            transit_asteroid_aspects=transit_asteroid_aspects,
            current_themes=themes
        )

    @classmethod
    async def calculate_lunar_return(
        cls,
        birth_info: BirthInfo,
        natal_geo_location: GeoLocation,
        return_geo_location: Optional[GeoLocation] = None,
        start_date: Optional[datetime] = None,
    ) -> "LunarReturnChart":
        """Calculates the Lunar Return chart by finding the precise return time."""
        natal_subject = await cls.create_subject(birth_info, natal_geo_location)
        natal_moon_longitude = natal_subject.moon.abs_pos

        current_time = start_date or birth_info.birth_date
        return_geo = return_geo_location if return_geo_location is not None else natal_geo_location

        transit_info = BirthInfo(name="Transit", birth_date=current_time, location=return_geo.formatted_address)
        transit_subject = await cls.create_subject(transit_info, return_geo)
        diff = transit_subject.moon.abs_pos - natal_moon_longitude
        if diff > 180: diff -= 360
        if diff < -180: diff += 360
        
        time_adjustment_days = -diff / 13.176
        current_time += timedelta(days=time_adjustment_days)

        time_steps = [timedelta(hours=6), timedelta(hours=1), timedelta(minutes=1), timedelta(seconds=1)]
        for step in time_steps:
            while True:
                transit_info = BirthInfo(name="Transit", birth_date=current_time, location=return_geo.formatted_address)
                transit_subject = await cls.create_subject(transit_info, return_geo)
                diff = transit_subject.moon.abs_pos - natal_moon_longitude
                if diff > 180: diff -= 360
                if diff < -180: diff += 360

                if abs(diff) < 0.0001:
                    break

                next_time = current_time - step if diff > 0 else current_time + step
                next_transit_info = BirthInfo(name="Transit", birth_date=next_time, location=return_geo.formatted_address)
                next_subject = await cls.create_subject(next_transit_info, return_geo)
                next_diff = next_subject.moon.abs_pos - natal_moon_longitude
                if next_diff > 180: next_diff -= 360
                if next_diff < -180: next_diff += 360

                if diff * next_diff < 0:
                    current_time = next_time if abs(next_diff) < abs(diff) else current_time
                    break 
                current_time = next_time

        lunar_return_info = BirthInfo(name=f"Lunar Return for {birth_info.name}", birth_date=current_time, location=return_geo.formatted_address)
        chart = await cls.calculate_natal_chart(lunar_return_info, return_geo)
        return LunarReturnChart(chart=chart, return_time=current_time)

    @classmethod
    async def calculate_solar_return(
        cls,
        birth_info: BirthInfo,
        natal_geo_location: GeoLocation,
        return_geo_location: Optional[GeoLocation] = None,
        year: Optional[int] = None,
    ) -> "SolarReturnChart":
        """Find the exact Solar Return moment and compute the SR chart.

        The SR chart uses return_geo_location for house calculation (ASC/MC), so
        passing the person's current residence is important when they live away from
        their birth city.  If omitted, natal_geo_location is used.

        Algorithm:
        1. Determine target year (current year if birthday hasn't passed yet, else next year).
        2. Seed the search at the approximate solar birthday ±5 days.
        3. Converge with decreasing step sizes down to 1-second precision.
        """
        natal_subject = await cls.create_subject(birth_info, natal_geo_location)
        natal_sun_abs = natal_subject.sun.abs_pos  # 0–360 ecliptic longitude

        return_geo = return_geo_location if return_geo_location is not None else natal_geo_location

        # Determine search seed: same month/day in target year
        from datetime import date
        today = datetime.utcnow()
        if year is None:
            bday_this_year = datetime(today.year, birth_info.birth_date.month, birth_info.birth_date.day,
                                      birth_info.birth_date.hour, birth_info.birth_date.minute)
            year = today.year if bday_this_year > today else today.year + 1

        try:
            seed = datetime(year, birth_info.birth_date.month, birth_info.birth_date.day,
                            birth_info.birth_date.hour, birth_info.birth_date.minute)
        except ValueError:
            # handle Feb 29 in non-leap year
            seed = datetime(year, birth_info.birth_date.month, 28,
                            birth_info.birth_date.hour, birth_info.birth_date.minute)

        current_time = seed

        def _sun_diff(t: datetime) -> float:
            """Return signed difference: transit_sun_abs - natal_sun_abs, normalised to (-180, 180]."""
            from kerykeion.main import KrInstance as _KrI
            s = _KrI(
                name="SR_search",
                year=t.year, month=t.month, day=t.day,
                hour=t.hour, minute=t.minute,
                lng=return_geo.longitude, lat=return_geo.latitude,
                tz_str=return_geo.timezone,
                online=True,
            )
            diff = s.sun.abs_pos - natal_sun_abs
            if diff > 180:
                diff -= 360
            if diff <= -180:
                diff += 360
            return diff

        # Coarse linear correction: Sun moves ~1°/day
        diff = _sun_diff(current_time)
        current_time += timedelta(days=-diff)

        # Refine with decreasing step sizes
        for step in [timedelta(hours=6), timedelta(hours=1), timedelta(minutes=1), timedelta(seconds=1)]:
            for _ in range(400):                 # safety cap
                diff = _sun_diff(current_time)
                if abs(diff) < 0.0001:
                    break
                next_time = current_time - step if diff > 0 else current_time + step
                next_diff = _sun_diff(next_time)
                if diff * next_diff < 0:
                    current_time = next_time if abs(next_diff) < abs(diff) else current_time
                    break
                current_time = next_time

        # Compute the SR chart at the exact SR moment using return_geo for houses
        sr_info = BirthInfo(
            name=f"Solar Return {year} for {birth_info.name}",
            birth_date=current_time,
            location=return_geo.formatted_address,
        )
        sr_chart = await cls.calculate_natal_chart(sr_info, return_geo)
        natal_chart = await cls.calculate_natal_chart(birth_info, natal_geo_location)

        # SR-to-natal aspects: compare SR planets against natal planets
        sr_subject = await cls.create_subject(sr_info, return_geo)
        natal_subject2 = await cls.create_subject(birth_info, natal_geo_location)
        sr_natal_aspects_obj = CompositeAspects(sr_subject, natal_subject2)
        sr_aspects = cls._get_aspect_info(sr_natal_aspects_obj.get_all_aspects())

        return SolarReturnChart(
            natal_chart=natal_chart,
            sr_chart=sr_chart,
            sr_time=current_time,
            sr_aspects=sr_aspects,
        )
