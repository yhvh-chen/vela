from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "script"

SKILLS = {
    "natal-raw-chart": "natal_raw_chart.py",
    "synastry-raw-chart": "synastry_raw_chart.py",
    "composite-raw-chart": "composite_raw_chart.py",
    "transit-raw-chart": "transit_raw_chart.py",
    "solar-return-raw-chart": "solar_return_raw_chart.py",
    "lunar-return-raw-chart": "lunar_return_raw_chart.py",
}

SAMPLE_INPUTS = {
    "natal-raw-chart": {
        "name": "Demo",
        "birth_date": "1990-01-15T08:30:00",
        "location": "Beijing, China",
        "latitude": 39.9042,
        "longitude": 116.4074,
        "timezone": "Asia/Shanghai",
    },
    "synastry-raw-chart": {
        "person1": {
            "name": "Alice",
            "birth_date": "1991-07-08T16:10:00",
            "location": "Guangzhou, China",
        },
        "person1_latitude": 23.1291,
        "person1_longitude": 113.2644,
        "person1_timezone": "Asia/Shanghai",
        "person2": {
            "name": "Bob",
            "birth_date": "1989-03-03T09:15:00",
            "location": "Sydney, Australia",
        },
        "person2_latitude": -33.8688,
        "person2_longitude": 151.2093,
        "person2_timezone": "Australia/Sydney",
    },
    "composite-raw-chart": {
        "person1": {
            "name": "Alice",
            "birth_date": "1991-07-08T16:10:00",
            "location": "Guangzhou, China",
        },
        "person1_latitude": 23.1291,
        "person1_longitude": 113.2644,
        "person1_timezone": "Asia/Shanghai",
        "person2": {
            "name": "Bob",
            "birth_date": "1989-03-03T09:15:00",
            "location": "Sydney, Australia",
        },
        "person2_latitude": -33.8688,
        "person2_longitude": 151.2093,
        "person2_timezone": "Australia/Sydney",
    },
    "transit-raw-chart": {
        "name": "Demo",
        "birth_date": "1990-01-15T08:30:00",
        "location": "Beijing, China",
        "latitude": 39.9042,
        "longitude": 116.4074,
        "timezone": "Asia/Shanghai",
        "transit_date": "2025-05-01T12:00:00",
        "transit_location": "Shanghai, China",
        "transit_latitude": 31.2304,
        "transit_longitude": 121.4737,
        "transit_timezone": "Asia/Shanghai",
    },
    "solar-return-raw-chart": {
        "name": "Demo",
        "birth_date": "1990-01-15T08:30:00",
        "location": "Beijing, China",
        "latitude": 39.9042,
        "longitude": 116.4074,
        "timezone": "Asia/Shanghai",
        "year": 2026,
        "return_location": "Shanghai, China",
        "return_latitude": 31.2304,
        "return_longitude": 121.4737,
        "return_timezone": "Asia/Shanghai",
    },
    "lunar-return-raw-chart": {
        "name": "Demo",
        "birth_date": "1990-01-15T08:30:00",
        "location": "Beijing, China",
        "latitude": 39.9042,
        "longitude": 116.4074,
        "timezone": "Asia/Shanghai",
        "start_date": "2025-05-01T00:00:00",
        "return_location": "Shanghai, China",
        "return_latitude": 31.2304,
        "return_longitude": 121.4737,
        "return_timezone": "Asia/Shanghai",
    },
}


def test_chart_skill_scripts_expose_help():
    for script_name in SKILLS.values():
        completed = subprocess.run(
            ["uv", "run", "python", str(SCRIPTS_DIR / script_name), "--help"],
            cwd=SKILL_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert "usage:" in completed.stdout.lower()


@pytest.mark.parametrize("skill_name,script_name", SKILLS.items())
def test_chart_skill_scripts_return_json(skill_name: str, script_name: str):
    completed = subprocess.run(
        ["uv", "run", "python", str(SCRIPTS_DIR / script_name)],
        cwd=SKILL_ROOT,
        input=json.dumps(SAMPLE_INPUTS[skill_name]),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    payload = json.loads(completed.stdout)
    expected_chart_type = skill_name.replace("-raw-chart", "").replace("-", "_")
    assert payload["chart_type"] == expected_chart_type


RECTIFY_INPUT = {
    "birth_date": "1993-04-02",
    "location": "Guangzhou, China",
    "latitude": 23.1291,
    "longitude": 113.2644,
    "timezone": "Asia/Shanghai",
    "events": [{"year": 2016, "description": "relocation"}, {"year": 2021, "month": 6}],
}


def _run_script(script_name: str, payload: dict) -> dict:
    completed = subprocess.run(
        ["uv", "run", "python", str(SCRIPTS_DIR / script_name)],
        cwd=SKILL_ROOT,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    return json.loads(completed.stdout)


def test_rectify_returns_ranked_ascendant_candidates():
    payload = _run_script("rectify.py", RECTIFY_INPUT)
    assert payload["chart_type"] == "rectification_scan"
    candidates = payload["candidates"]
    assert len(candidates) == 12
    scores = [c["score"] for c in candidates]
    assert scores == sorted(scores, reverse=True)
    assert {"time", "ascendant_sign", "ascendant_degree", "mc_sign", "score", "hits"} <= set(candidates[0])


def test_composite_uses_circular_midpoints_with_signs_and_houses():
    payload = _run_script("composite_raw_chart.py", SAMPLE_INPUTS["composite-raw-chart"])
    planets = {p["name"]: p for p in payload["composite_planets"]}
    assert "Mean_Node" not in planets
    for planet in planets.values():
        assert planet["sign"], planet
        assert 1 <= planet["house"] <= 12, planet
    assert len(payload["composite_houses"]) == 12
    assert all(h["sign"] for h in payload["composite_houses"])
    # Composite aspects are internal to the midpoint chart, not cross-chart contacts.
    assert payload["composite_aspects"], "composite chart should have internal aspects"


def test_synastry_has_karmic_contacts_and_no_score():
    payload = _run_script("synastry_raw_chart.py", SAMPLE_INPUTS["synastry-raw-chart"])
    assert "compatibility_score" not in payload
    contact_text = json.dumps(payload["asteroid_contacts"])
    assert "True_Node" in contact_text or "Chiron" in contact_text


def test_natal_includes_chiron():
    payload = _run_script("natal_raw_chart.py", SAMPLE_INPUTS["natal-raw-chart"])
    names = {p["name"] for p in payload["planets"]}
    assert "Chiron" in names
