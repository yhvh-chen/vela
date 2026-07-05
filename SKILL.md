---
name: vela-astrology
description: Astrology chart calculation and soul-level interpretation. Use this skill whenever the user provides birth details (date, time, place) or asks about natal charts, relationship compatibility (synastry/composite), transits, solar or lunar returns, 星盘/本命盘/合盘/行运盘/太阳返照/月亮返照, astrological timing, or any follow-up question about a chart already computed — even if they never say the word "astrology".
license: CC-BY-NC-4.0 © DATATECHIE PTY LTD (see LICENSE)
---

# Vela Skill

**Purpose**: One self-contained astrology skill package for chart calculation and interpretation.

## Scope

- Natal charts
- Synastry and composite relationship charts
- Transit charts
- Solar return charts
- Lunar return charts

## Workflow

1. Collect birth data (ask only for missing required fields; reuse stored chart context when available)
2. Run the matching calculation script (see `reference/ephemeris.md` for the contract)
3. Interpret using the chart-family reference plus `reference/delivery.md`
4. Deliver the complete reading in the first turn, in the user's language
5. End with one consultation question and run the dialogue loop (`reference/delivery.md`, "The consultation loop") — calibrate, locate the real question, advance the choice

## Scripts

- `script/natal_raw_chart.py`
- `script/synastry_raw_chart.py`
- `script/composite_raw_chart.py`
- `script/transit_raw_chart.py`
- `script/solar_return_raw_chart.py`
- `script/lunar_return_raw_chart.py`
- `script/rectify.py` (birth-time rectification scan — only when the user doubts their birth time)

## Contract

- Calculation scripts read structured JSON and write JSON to stdout
- Errors are returned as `{"error": "<message>"}`
- Dependency manifest lives at `pyproject.toml`
- For location input, prefer English transliteration or pre-resolved coordinates; non-Latin place names can geocode ambiguously

## Interpretation Principle

The reference files are scaffolding, not a ceiling. Bring your full astrological knowledge — archetype, myth, psychological depth — to every reading. The discipline is anchoring, not restraint: every interpretive claim must tie to a specific placement, aspect, or orb tightness in *this* chart. Never invent chart facts; go as deep as the real ones allow. `reference/delivery.md` defines the voice; `reference/examples.md` shows the standard.

## Execution Flow

- Calculation and helper modules live in `script/`
- Interpretation happens through the reference layers
- Internal multi-step work stays inside the runtime
- External clients only render public output

## Progressive Disclosure

1. Read this file first
2. Then open only the minimum reference file(s) needed for the current chart type:
   - `reference/delivery.md` for voice and writing shape (always, before writing any reading)
   - `reference/examples.md` to calibrate depth when writing a full reading
   - `reference/retrieval_protocol.md` if retrieval is available
   - `reference/ephemeris.md` for calculation rules and script contract
   - one file under `reference/charts/` for the active chart family
   - base meaning files (`reference/charts/signs.md`, `reference/charts/planets.md`, `reference/charts/houses.md`, `reference/charts/aspects.md`, `reference/charts/asteroids.md`) only when needed
3. Do not load every reference file at once

## Reference Map

- Voice, writing shape, and synthesis rules → `reference/delivery.md`
- Flat-vs-alive calibration examples → `reference/examples.md`
- Optional retrieval policy → `reference/retrieval_protocol.md`
- Calculation rules and script contract → `reference/ephemeris.md`
- Base meaning layers → `reference/charts/signs.md`, `reference/charts/planets.md`, `reference/charts/houses.md`, `reference/charts/aspects.md`, `reference/charts/asteroids.md`
- Concrete life domains (parents, spouse, wealth, health) and aspect complexes → `reference/charts/life_domains.md`
- Birth-time rectification protocol (only on user-raised doubt) → `reference/rectification.md`
- Chart families → `reference/charts/natal.md`, `reference/charts/synastry.md` (includes composite), `reference/charts/composite.md`, `reference/charts/transits.md`, `reference/charts/solar_return.md`, `reference/charts/lunar_return.md`
