# Ephemeris

Use this file for chart calculation behavior.

## Contract

- Input: structured JSON only
- Output: JSON only
- Errors: `{"error": "<message>"}`

## Calculation rules

- Resolve locations before calculation
- Prefer pre-resolved latitude / longitude / timezone when available
- Use IANA timezone strings
- For tool input, prefer English transliteration for place names when the original script is likely to mis-geocode non-Latin text; coordinates are better when available
- Main asteroid calculations use `script/ephe/seas_18.se1`; keep the file alongside the scripts or the asteroid layer will be empty
- Do not write interpretation text here

## Script map

- `script/natal_raw_chart.py`
- `script/synastry_raw_chart.py`
- `script/composite_raw_chart.py`
- `script/transit_raw_chart.py`
- `script/solar_return_raw_chart.py`
- `script/lunar_return_raw_chart.py`
- `script/rectify.py` — birth-time rectification scan; input: `birth_date` (YYYY-MM-DD), location/coordinates, `events` (≥2 of `{year, month?, description?}`); output: scored ascendant candidates with transit/solar-arc hits

## Helper modules

- `script/models.py`
- `script/geo_service.py`
- `script/calculator.py`
- `script/_common.py`

## Ephemeris data

- `script/ephe/seas_18.se1` for Ceres, Pallas, Juno, Vesta, and Chiron

## Output contract notes

- Natal `planets[]` includes Chiron; its aspects to planets/angles are appended to `aspects[]`
- Synastry `asteroid_contacts[]` includes the karmic-teacher layer: each person's True Node and Chiron cross-contacts to the other's planets and angles (owner-labeled, e.g. "SS True_Node conjunction CC Saturn")
- Synastry deliberately outputs **no compatibility score** — scores are banned at the interpretation layer
- Composite uses shorter-arc midpoints for planets, asteroids, and all 12 house cusps; `composite_aspects[]` are internal to the midpoint chart (cross-chart contacts belong to synastry); Mean_Node is omitted (True_Node kept)

## Recovery guidance

- JSON parse error → use stdin mode
- Location issue → pre-resolve or transliterate to English
- Missing field → recollect only the missing value
