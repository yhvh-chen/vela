#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from _common import (
    add_ephemeris_path,
    load_json_input,
    next_solar_return_year,
    print_error_and_exit,
    print_json,
    resolve_geo,
)


async def main() -> None:
    payload = load_json_input("Calculate solar return raw chart JSON")
    add_ephemeris_path()
    from calculator import KerykeionCalculator
    from models import BirthInfo
    from models import SolarReturnRequest

    request = SolarReturnRequest.model_validate(payload)
    natal_geo = await resolve_geo(
        location=request.location,
        latitude=request.latitude,
        longitude=request.longitude,
        timezone=request.timezone,
    )
    return_geo = await resolve_geo(
        location=request.return_location or request.location,
        latitude=request.return_latitude,
        longitude=request.return_longitude,
        timezone=request.return_timezone,
    ) if (
        request.return_location
        or request.return_latitude is not None
        or request.return_longitude is not None
    ) else natal_geo
    tz = ZoneInfo(return_geo.timezone)
    target_year = request.year or next_solar_return_year(
        birth_date=request.birth_date,
        reference=datetime.now(tz),
    )
    chart = await KerykeionCalculator.calculate_solar_return(
        BirthInfo(name=request.name, birth_date=request.birth_date, location=request.location),
        natal_geo,
        return_geo,
        target_year,
    )
    print_json({"chart_type": "solar_return", **chart.model_dump()})


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:  # noqa: BLE001
        sys.exit(print_error_and_exit(exc))
