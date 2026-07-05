#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys

from _common import (
    add_ephemeris_path,
    load_json_input,
    print_error_and_exit,
    print_json,
    resolve_geo,
)


async def main() -> None:
    payload = load_json_input("Calculate transit raw chart JSON")
    add_ephemeris_path()
    from calculator import KerykeionCalculator
    from models import BirthInfo
    from models import TransitsRequest

    request = TransitsRequest.model_validate(payload)
    natal_geo = await resolve_geo(
        location=request.location,
        latitude=request.latitude,
        longitude=request.longitude,
        timezone=request.timezone,
    )
    transit_geo = await resolve_geo(
        location=request.transit_location or request.location,
        latitude=request.transit_latitude,
        longitude=request.transit_longitude,
        timezone=request.transit_timezone,
    ) if (
        request.transit_location
        or request.transit_latitude is not None
        or request.transit_longitude is not None
    ) else natal_geo
    chart = await KerykeionCalculator.calculate_transits(
        BirthInfo(name=request.name, birth_date=request.birth_date, location=request.location),
        natal_geo,
        transit_geo,
        request.transit_date,
    )
    print_json({"chart_type": "transit", **chart.model_dump()})


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:  # noqa: BLE001
        sys.exit(print_error_and_exit(exc))
