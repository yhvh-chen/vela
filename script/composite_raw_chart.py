#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys

from _common import (
    add_ephemeris_path,
    load_json_input,
    print_error_and_exit,
    print_json,
    resolve_prefixed_geo,
)


async def main() -> None:
    payload = load_json_input("Calculate composite raw chart JSON")
    add_ephemeris_path()
    from calculator import KerykeionCalculator
    from models import BirthInfo
    from models import CompositeRequest

    request = CompositeRequest.model_validate(payload)
    geo1, geo2 = await asyncio.gather(
        resolve_prefixed_geo(payload, "person1", request.person1.location),
        resolve_prefixed_geo(payload, "person2", request.person2.location),
    )
    chart = await KerykeionCalculator.calculate_composite(
        BirthInfo(name=request.person1.name, birth_date=request.person1.birth_date, location=request.person1.location),
        geo1,
        BirthInfo(name=request.person2.name, birth_date=request.person2.birth_date, location=request.person2.location),
        geo2,
    )
    print_json({"chart_type": "composite", **chart.model_dump()})


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:  # noqa: BLE001
        sys.exit(print_error_and_exit(exc))
