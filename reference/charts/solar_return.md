# Solar Return Interpretation Guide

## What is a Solar Return?

The Solar Return (太阳返照盘) is cast for the exact moment the Sun returns to its
natal ecliptic longitude, once per year near the native's birthday.  The SR chart
governs themes and energy patterns for the ~12 months until the next SR.

**Critical rule:** SR house cusps (ASC/MC) are calculated using the observer's
*current residence* at the SR moment, not the birth location.  Always use
`return_location` from the user's profile cache or confirm with the user.

---

## Interpretation Sequence

### 1. SR ASC / SR MC — annual identity and career axis
- SR ASC sign → outer persona the year demands
- SR MC sign → career / public domain focus for the year
- Compare SR ASC to natal ASC: same sign = steady year; different sign = shift in presentation

### 2. SR Sun house placement
- Shows the *domain* where the year's core energy is spent
- 1st house: self-focus, new beginnings
- 7th house: partnerships dominate
- 10th house: career and public recognition year
- 4th house: family, roots, private life

### 3. SR Moon — emotional tone and fluctuation domain
- SR Moon sign → emotional coloring of the year
- SR Moon house → area of life with most emotional activity
- SR Moon aspects to natal planets → key emotional triggers

### 4. SR planets on natal angles (ASC/MC/DSC/IC)
- Any SR planet within 5° of a natal angle = major theme for the year
- SR Pluto on natal ASC → identity transformation year
- SR Jupiter on natal MC → career expansion or visibility year
- SR Saturn on natal ASC → discipline, responsibility, limitation year

### 5. SR stellium (3+ planets in one house)
- The occupied house becomes the year's primary domain regardless of other factors

### 6. SR-to-natal aspects (`sr_aspects` array)
- Tight orbs (≤2°) only for year-level interpretation
- SR Jupiter conjunct natal Venus → abundance, relationships open
- SR Saturn square natal Sun → effort, restructuring, tests of identity
- SR Uranus conjunct natal MC → sudden career changes

### 7. Synthesise with current transits
- SR chart sets the *annual background*; exact-date transits trigger events within that backdrop
- When a transit planet activates a sensitive SR planet, that period is a key event window

---

## Output Structure from `script/solar_return_raw_chart.py`

| Field | Use |
|---|---|
| `sr_chart.planets[]` | SR planet positions (where sky is on birthday) |
| `sr_chart.houses[]` | SR house cusps at return_location |
| `sr_chart.ascendant` | SR ASC — annual identity axis |
| `sr_chart.midheaven` | SR MC — annual career axis |
| `sr_time` | Exact SR moment (UTC); convert to local tz for user |
| `natal_chart` | Reference for SR-to-natal comparisons |
| `sr_aspects[]` | Cross-aspects between SR planets and natal planets |

---

## Location note

If the user may travel on their birthday, note:
> "The SR ASC/MC shown here are calculated for [return_location]. If you are in
> a different city on [sr_date], the ASC/MC will shift — let me know and I can
> recalculate."
