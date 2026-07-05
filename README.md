# Vela Astrology Skill

<p align="center">
  <img src="assets/logo.png" alt="Vela Astrology Logo" width="200" style="border-radius: 50%;"/>
</p>

<p align="center">
  <b>English README</b> | <a href="README_CN.md">简体中文</a>
</p>

A self-contained astrological chart calculation and interpretation Agent Skill package. It encapsulates the underlying Swiss Ephemeris calculation framework based on `kerykeion`, specifically designed to provide precise astrological data support for various LLM Agents (such as LangGraph, MCP, AutoGen, CrewAI, etc.).

## Scope

This skill package supports the underlying calculation and formatted output for the following 6 types of charts:

- **Natal Chart**: Calculates positions and aspects for basic planets, virtual points (North/South Nodes, Chiron), and major asteroids (Ceres, Pallas, Juno, Vesta).
- **Synastry Chart**: Calculates cross-chart aspect contacts between two individuals' charts and provides compatibility scores.
- **Composite Chart**: Computes relationship midpoint charts for couples.
- **Transit Chart**: Calculates the aspect relationships between transiting planets at a specific time and natal planets.
- **Solar Return Chart**: Computes the return chart for the exact moment the Sun returns to its precise birth longitude.
- **Lunar Return Chart**: Computes the return chart for the exact moment the Moon returns to its precise birth longitude.

## Directory Structure

```text
vela-skill/
├── pyproject.toml        # Dependency and packaging configuration file (based on uv)
├── SKILL.md              # Agent Skill entry point (includes frontmatter triggers description)
├── script/               # Calculation scripts directory
│   ├── ephe/             # Swiss Ephemeris data package (contains seas_18.se1)
│   ├── _common.py        # Geographical, input, and formatting helper functions
│   ├── calculator.py     # Core calculation engine layer (wraps kerykeion / swisseph)
│   ├── geo_service.py    # Geocoding service (Nominatim + TimezoneFinder)
│   ├── models.py         # Pydantic validation and data structures definition
│   ├── rectify.py        # Birth time rectification scan (used only when the user doubts their birth time)
│   └── *_raw_chart.py    # Executable command-line entry points for various chart types
├── reference/            # Astrological interpretation reference specifications (for RAG / Context Injection)
│   ├── delivery.md       # Reading voice (astrologer writing style) and delivery format specifications
│   ├── examples.md       # Average vs Deep reading examples (calibrates interpretation depth)
│   ├── ephemeris.md      # Ephemeris calculation protocol specifications
│   ├── retrieval_protocol.md # Optional retrieval protocol
│   └── charts/           # Deep interpretation library for charts, planets, houses, and aspects
└── tests/                # Independent unit tests directory
```

## Host Integration Notes

- **Trigger Mechanism**: The host Agent discovers and triggers this Skill via the `name` + `description` in `SKILL.md`'s frontmatter. Do not delete the frontmatter.
- **Refusal Strategy is Host-Level**: If the product requires guardrails like "only talk about astrology and refuse coding/news/chitchat", implement this in the host Agent's system prompt instead of this Skill. The Skill should remain reusable and not pollute the general-purpose Agent loading it.
- **Geocoding Network Dependency**: `geo_service.py` makes real-time calls to Nominatim (which has rate limits). For production environments, it is recommended that the host pre-resolves latitude, longitude, and timezone, passing them directly to bypass online geocoding.

## Input & Output Contracts

Calculation scripts are designed as pure functions:
- **Input**: Reads structured JSON from `stdin` or via the `--input` argument.
- **Output**: Prints calculated results to `stdout` in JSON format.
- **Error Handling**: If any exception occurs, the program catches it and outputs `{"error": "<error reason>"}` to `stdout`, exiting with a non-zero status code.

### Example Usage

```bash
# Enter skill directory
cd vela-skill

# Run natal chart calculation
echo '{"name": "Demo", "birth_date": "1990-01-15T08:30:00", "location": "Beijing, China", "latitude": 39.9042, "longitude": 116.4074, "timezone": "Asia/Shanghai"}' | uv run python script/natal_raw_chart.py
```

## Developer and Testing Guide

### Installation

The Skill package requires Python `>=3.10` and is recommended to run using `uv`:

```bash
uv sync --dev
```

### Running Tests

The Skill package contains a fully independent automated test suite. Run the following command to verify all script calculation logic and data structure contracts:

```bash
uv run pytest tests/
```

## License

Copyright © 2026 DATATECHIE PTY LTD.

This entire package (including code and documentation) is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)** license. See [LICENSE](LICENSE) for details.

Note that third-party dependencies (such as Swiss Ephemeris data, kerykeion, and pyswisseph) are subject to their own respective licenses (AGPL-3.0).
