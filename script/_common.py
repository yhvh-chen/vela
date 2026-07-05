from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_ROOT = Path(__file__).resolve().parent
_SIGN_NAMES = {
    "Ari": "Aries",
    "Tau": "Taurus",
    "Gem": "Gemini",
    "Can": "Cancer",
    "Leo": "Leo",
    "Vir": "Virgo",
    "Lib": "Libra",
    "Sco": "Scorpio",
    "Sag": "Sagittarius",
    "Cap": "Capricorn",
    "Aqu": "Aquarius",
    "Pis": "Pisces",
}
_HOUSE_NAME_TO_NUMBER = {
    "First_House": 1,
    "Second_House": 2,
    "Third_House": 3,
    "Fourth_House": 4,
    "Fifth_House": 5,
    "Sixth_House": 6,
    "Seventh_House": 7,
    "Eighth_House": 8,
    "Ninth_House": 9,
    "Tenth_House": 10,
    "Eleventh_House": 11,
    "Twelfth_House": 12,
}
_PRIMARY_POINT_ATTRS = (
    "sun",
    "moon",
    "mercury",
    "venus",
    "mars",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
    "pluto",
    "chiron",
    "true_north_lunar_node",
    "true_south_lunar_node",
)
_ASTEROID_ATTRS = ("ceres", "pallas", "juno", "vesta")
_HOUSE_ATTRS = (
    "first_house",
    "second_house",
    "third_house",
    "fourth_house",
    "fifth_house",
    "sixth_house",
    "seventh_house",
    "eighth_house",
    "ninth_house",
    "tenth_house",
    "eleventh_house",
    "twelfth_house",
)


def add_ephemeris_path() -> None:
    path = str(SCRIPT_ROOT)
    if path not in sys.path:
        sys.path.insert(0, path)


def load_json_input(description: str) -> dict[str, Any]:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--input", "-i", help="JSON input string")
    args = parser.parse_args()
    if args.input:
        return json.loads(args.input)
    raw = sys.stdin.buffer.read().decode("utf-8-sig").strip()
    return json.loads(raw) if raw else {}


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, default=str))


def print_error_and_exit(exc: Exception) -> int:
    print_json({"error": str(exc)})
    return 1


def make_birth_info(*, name: str, birth_date: Any, location: str) -> Any:
    add_ephemeris_path()
    from models import BirthInfo

    return BirthInfo(name=name, birth_date=birth_date, location=location)


def build_subject(*, name: str, birth_date: datetime, location: str, geo: Any) -> Any:
    from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory

    city, nation = _split_location(location or getattr(geo, "formatted_address", ""))
    return AstrologicalSubjectFactory.from_birth_data(
        name=name,
        year=birth_date.year,
        month=birth_date.month,
        day=birth_date.day,
        hour=birth_date.hour,
        minute=birth_date.minute,
        seconds=birth_date.second,
        city=city,
        nation=nation or None,
        lng=getattr(geo, "longitude"),
        lat=getattr(geo, "latitude"),
        tz_str=getattr(geo, "timezone"),
        online=False,
    )


def _normalize_sign(sign: str | None) -> str:
    if not sign:
        return ""
    return _SIGN_NAMES.get(sign, sign)


def _house_number(value: Any) -> int | None:
    if isinstance(value, int) and 1 <= value <= 12:
        return value
    if hasattr(value, "value"):
        value = getattr(value, "value")
    if isinstance(value, str):
        mapped = _HOUSE_NAME_TO_NUMBER.get(value.strip())
        if mapped is not None:
            return mapped
        try:
            parsed = int(value)
        except ValueError:
            return None
        return parsed if 1 <= parsed <= 12 else None
    return None


def _split_location(location: str) -> tuple[str, str]:
    parts = [part.strip() for part in location.split(",") if part.strip()]
    if not parts:
        return location.strip(), ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[-1]


def _point_payload(point: Any) -> dict[str, Any]:
    return {
        "name": getattr(point, "name", ""),
        "sign": _normalize_sign(getattr(point, "sign", "")),
        "position": round(float(getattr(point, "position", 0.0)), 4),
        "abs_pos": round(float(getattr(point, "abs_pos", getattr(point, "position", 0.0))), 4),
        "house": _house_number(getattr(point, "house", None)),
        "retrograde": bool(getattr(point, "retrograde", False)),
    }


def subject_to_raw_chart(subject: Any, *, include_asteroids: bool = True) -> dict[str, Any]:
    planets = []
    for attr_name in _PRIMARY_POINT_ATTRS:
        point = getattr(subject, attr_name, None)
        if point is not None:
            planets.append(_point_payload(point))

    asteroids: list[dict[str, Any]] = []
    if include_asteroids:
        for attr_name in _ASTEROID_ATTRS:
            point = getattr(subject, attr_name, None)
            if point is not None:
                asteroids.append(_point_payload(point))

    houses: dict[str, dict[str, Any]] = {}
    for attr_name in _HOUSE_ATTRS:
        house = getattr(subject, attr_name, None)
        if house is None:
            continue
        key = "ascendant" if attr_name == "first_house" else "midheaven" if attr_name == "tenth_house" else f"house_{_HOUSE_NAME_TO_NUMBER[getattr(house, 'name', attr_name.title())]}"
        houses[key] = {
            "sign": _normalize_sign(getattr(house, "sign", "")),
            "position": round(float(getattr(house, "position", 0.0)), 4),
            "abs_pos": round(float(getattr(house, "abs_pos", getattr(house, "position", 0.0))), 4),
        }

    location_parts = [part for part in (getattr(subject, "city", ""), getattr(subject, "nation", "")) if part]
    return {
        "subject": getattr(subject, "name", ""),
        "birth": getattr(subject, "iso_formatted_local_datetime", ""),
        "location": ", ".join(location_parts),
        "ascendant": _point_payload(getattr(subject, "ascendant")),
        "midheaven": _point_payload(getattr(subject, "medium_coeli")),
        "planets": planets,
        "asteroids": asteroids,
        "houses": houses,
    }


def aspects_to_payload(aspects: Any) -> list[dict[str, Any]]:
    if hasattr(aspects, "model_dump"):
        aspect_rows = aspects.model_dump().get("aspects", [])
    else:
        aspect_rows = aspects or []
    return [
        {
            "p1": row.get("p1_name"),
            "p2": row.get("p2_name"),
            "aspect": row.get("aspect"),
            "orb": round(float(row.get("orbit", 0.0)), 2),
            "movement": row.get("aspect_movement"),
            "p1_owner": row.get("p1_owner"),
            "p2_owner": row.get("p2_owner"),
        }
        for row in aspect_rows
    ]


def synastry_score(aspect_payload: list[dict[str, Any]]) -> float:
    harmonious = sum(1 for row in aspect_payload if row.get("aspect") in {"trine", "sextile"})
    challenging = sum(1 for row in aspect_payload if row.get("aspect") in {"square", "opposition", "quincunx"})
    total = len(aspect_payload)
    return round(((harmonious - challenging) / total) * 100, 2) if total else 50.0


def relationship_themes_from_aspects(aspect_payload: list[dict[str, Any]]) -> list[str]:
    themes: list[str] = []
    for row in aspect_payload[:6]:
        p1 = row.get("p1") or ""
        p2 = row.get("p2") or ""
        aspect = row.get("aspect") or ""
        if not (p1 and p2 and aspect):
            continue
        themes.append(f"{p1} {aspect} {p2}")
    return themes


def transit_themes_from_aspects(aspect_payload: list[dict[str, Any]]) -> list[str]:
    themes: list[str] = []
    for row in aspect_payload[:6]:
        p1 = row.get("p1") or ""
        p2 = row.get("p2") or ""
        aspect = row.get("aspect") or ""
        if not (p1 and p2 and aspect):
            continue
        themes.append(f"{p1} {aspect} {p2}")
    return themes


def next_solar_return_year(*, birth_date: datetime, reference: datetime) -> int:
    birthday_tuple = (birth_date.month, birth_date.day)
    current_tuple = (reference.month, reference.day)
    return reference.year if current_tuple <= birthday_tuple else reference.year + 1


async def resolve_geo(
    *,
    location: str,
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
) -> Any:
    add_ephemeris_path()
    from geo_service import from_location_string
    from models import GeoLocation

    if latitude is not None and longitude is not None:
        return GeoLocation(
            latitude=float(latitude),
            longitude=float(longitude),
            formatted_address=location,
            timezone=timezone or "UTC",
        )
    return await from_location_string(location)


async def resolve_prefixed_geo(payload: dict[str, Any], prefix: str, location: str) -> Any:
    return await resolve_geo(
        location=location,
        latitude=payload.get(f"{prefix}_latitude"),
        longitude=payload.get(f"{prefix}_longitude"),
        timezone=payload.get(f"{prefix}_timezone"),
    )
