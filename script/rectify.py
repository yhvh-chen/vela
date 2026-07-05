#!/usr/bin/env python3
"""Lightweight birth-time rectification scan.

Scans candidate birth times across the day, scoring each candidate by how
well heavy transits and solar-arc directions to the four angles line up with
user-supplied major life events. Resolution is deliberately coarse (default
2-hour grid = ascendant-sign level); this is a triage tool, not a
minute-precision rectification.
"""
from __future__ import annotations

import asyncio
import sys
from datetime import date, datetime
from typing import Any

from _common import (
    add_ephemeris_path,
    load_json_input,
    print_error_and_exit,
    print_json,
    resolve_geo,
)

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

TRANSIT_WEIGHTS = {"Saturn": 3, "Pluto": 3, "Uranus": 2, "Neptune": 2, "Jupiter": 1}
SOLAR_ARC_WEIGHT = 2
TIGHT_ORB_BONUS = 1
TIGHT_ORB = 1.0
NAIBOD_RATE = 0.9856  # mean solar-arc degrees per year

ANGLE_NAMES = ("ASC", "MC", "DSC", "IC")
DIRECTED_POINTS = (
    "sun", "moon", "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
)


def _sign(abs_pos: float) -> str:
    return SIGNS[int(abs_pos % 360.0 // 30)]


def _separation(a: float, b: float) -> float:
    diff = abs((a - b) % 360.0)
    return min(diff, 360.0 - diff)


def _subject(name: str, dt: datetime, geo) -> Any:
    from kerykeion import KrInstance

    return KrInstance(
        name=name,
        year=dt.year,
        month=dt.month,
        day=dt.day,
        hour=dt.hour,
        minute=dt.minute,
        lng=geo.longitude,
        lat=geo.latitude,
        tz_str=geo.timezone,
        city="Custom",
        online=False,
    )


def _event_sample_dates(event: dict[str, Any]) -> list[date]:
    year = int(event["year"])
    month = event.get("month")
    if month:
        month = int(month)
        months = {max(1, month - 1), month, min(12, month + 1)}
    else:
        months = {2, 5, 8, 11}
    return [date(year, m, 15) for m in sorted(months)]


async def main() -> None:
    payload = load_json_input("Rectification scan JSON")
    add_ephemeris_path()

    birth_date_raw = payload.get("birth_date")
    events = payload.get("events") or []
    if not birth_date_raw:
        raise ValueError("'birth_date' is required (YYYY-MM-DD)")
    if len(events) < 2:
        raise ValueError("at least 2 dated events are required for a meaningful scan")

    birth_day = datetime.fromisoformat(str(birth_date_raw)).date()
    orb = float(payload.get("orb", 3.0))
    sa_orb = float(payload.get("sa_orb", 1.0))
    step_minutes = int(payload.get("time_step_minutes", 120))

    geo = await resolve_geo(
        location=payload.get("location"),
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
        timezone=payload.get("timezone"),
    )

    # Transit longitudes are birth-time independent: compute once per sample date.
    transit_samples: list[dict[str, Any]] = []
    for event in events:
        for sample_day in _event_sample_dates(event):
            subj = _subject("transit", datetime(sample_day.year, sample_day.month, sample_day.day, 12, 0), geo)
            for planet in ("jupiter", "saturn", "uranus", "neptune", "pluto"):
                transit_samples.append(
                    {
                        "event_year": int(event["year"]),
                        "event": event.get("description") or str(event["year"]),
                        "planet": planet.capitalize(),
                        "lon": float(getattr(subj, planet).abs_pos),
                    }
                )

    # Moon sign-boundary warning for the day.
    moon_start = _subject("m0", datetime.combine(birth_day, datetime.min.time()), geo).moon.abs_pos
    moon_end = _subject("m1", datetime.combine(birth_day, datetime.min.time()).replace(hour=23, minute=59), geo).moon.abs_pos
    moon_boundary = _sign(float(moon_start)) != _sign(float(moon_end))

    candidates = []
    minutes = 0
    while minutes < 24 * 60:
        candidate_dt = datetime.combine(birth_day, datetime.min.time()).replace(
            hour=minutes // 60, minute=minutes % 60
        )
        subj = _subject("candidate", candidate_dt, geo)
        asc = float(subj.first_house.abs_pos)
        mc = float(subj.tenth_house.abs_pos)
        angles = {
            "ASC": asc,
            "MC": mc,
            "DSC": (asc + 180.0) % 360.0,
            "IC": (mc + 180.0) % 360.0,
        }
        natal_points = {p.capitalize(): float(getattr(subj, p).abs_pos) for p in DIRECTED_POINTS}

        hits: list[dict[str, Any]] = []
        best: dict[tuple, dict[str, Any]] = {}
        for sample in transit_samples:
            for angle_name, angle_pos in angles.items():
                sep = _separation(sample["lon"], angle_pos)
                if sep <= orb:
                    key = (sample["event_year"], sample["planet"], angle_name)
                    if key not in best or sep < best[key]["orb"]:
                        best[key] = {
                            "type": "transit",
                            "event": sample["event"],
                            "event_year": sample["event_year"],
                            "planet": sample["planet"],
                            "angle": angle_name,
                            "orb": round(sep, 2),
                        }
        hits.extend(best.values())

        for event in events:
            years = (date(int(event["year"]), int(event.get("month") or 7), 1) - birth_day).days / 365.2422
            if years <= 0:
                continue
            arc = years * NAIBOD_RATE
            for point_name, natal_pos in natal_points.items():
                directed = (natal_pos + arc) % 360.0
                for angle_name, angle_pos in angles.items():
                    sep = _separation(directed, angle_pos)
                    if sep <= sa_orb:
                        hits.append(
                            {
                                "type": "solar_arc",
                                "event": event.get("description") or str(event["year"]),
                                "event_year": int(event["year"]),
                                "planet": point_name,
                                "angle": angle_name,
                                "orb": round(sep, 2),
                            }
                        )

        score = 0
        for hit in hits:
            if hit["type"] == "transit":
                score += TRANSIT_WEIGHTS.get(hit["planet"], 1)
            else:
                score += SOLAR_ARC_WEIGHT
            if hit["orb"] <= TIGHT_ORB:
                score += TIGHT_ORB_BONUS

        candidates.append(
            {
                "time": candidate_dt.strftime("%H:%M"),
                "ascendant_sign": _sign(asc),
                "ascendant_degree": round(asc % 30.0, 1),
                "mc_sign": _sign(mc),
                "score": score,
                "hits": sorted(hits, key=lambda h: h["orb"]),
            }
        )
        minutes += step_minutes

    candidates.sort(key=lambda c: c["score"], reverse=True)
    print_json(
        {
            "chart_type": "rectification_scan",
            "birth_date": birth_day.isoformat(),
            "location": geo.formatted_address,
            "resolution_minutes": step_minutes,
            "moon_sign_boundary_day": moon_boundary,
            "events": events,
            "candidates": candidates,
            "note": (
                "Scores rank ascendant-sign-level candidates only. "
                "A clear leader supports that rising sign; close scores mean the scan is inconclusive — "
                "collect one more dated event rather than over-claiming precision."
            ),
        }
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:  # noqa: BLE001
        sys.exit(print_error_and_exit(exc))
