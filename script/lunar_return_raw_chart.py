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
    payload = load_json_input("Calculate lunar return raw chart JSON")
    add_ephemeris_path()
    from calculator import KerykeionCalculator
    from models import BirthInfo
    from models import LunarReturnRequest

    request = LunarReturnRequest.model_validate(payload)
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
    chart = await KerykeionCalculator.calculate_lunar_return(
        BirthInfo(name=request.name, birth_date=request.birth_date, location=request.location),
        natal_geo,
        return_geo,
        request.start_date,
    )
    print_json({"chart_type": "lunar_return", **chart.model_dump()})


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:  # noqa: BLE001
        sys.exit(print_error_and_exit(exc))
