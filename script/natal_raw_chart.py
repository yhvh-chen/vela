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
    payload = load_json_input("Calculate natal raw chart JSON")
    add_ephemeris_path()
    from calculator import KerykeionCalculator
    from models import BirthInfo, NatalRequest

    request = NatalRequest.model_validate(payload)
    geo = await resolve_geo(
        location=request.location,
        latitude=request.latitude,
        longitude=request.longitude,
        timezone=request.timezone,
    )
    chart = await KerykeionCalculator.calculate_natal_chart(
        BirthInfo(
        name=request.name,
        birth_date=request.birth_date,
        location=request.location,
        ),
        geo,
    )
    print_json({"chart_type": "natal", **chart.model_dump()})


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:  # noqa: BLE001
        sys.exit(print_error_and_exit(exc))
