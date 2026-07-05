# Transits Reading Framework

A transit chart shows the current (or future) position of planets in the sky and how they interact with a person's natal chart. Transits describe timing, active themes, opportunities, and challenges.

---

## Planet Speed & Influence Duration

| Planet | Speed Through a Sign | Transit Duration (aspect) | Nature |
|--------|---------------------|--------------------------|--------|
| Moon | 2.5 days | Hours to 1 day | Emotional triggers, moods |
| Sun | 1 month | Days | Vitality, focus areas |
| Mercury | 3–4 weeks | Days to 1 week | Communication, decisions |
| Venus | 4–5 weeks | Days to 1 week | Relationships, aesthetics, pleasure |
| Mars | 6–8 weeks | 1–2 weeks | Energy, conflict, ambition |
| Jupiter | 1 year | 2–4 weeks | Expansion, luck, growth |
| Saturn | 2.5 years | 1–3 months | Discipline, restructuring, mastery |
| Uranus | 7 years | Months | Disruption, breakthrough |
| Neptune | 14 years | Years | Dissolution, idealism, fog |
| Pluto | 20 years | Years | Transformation, power, rebirth |

---

## Reading Sequence

### Step 1 — Identify Active Outer Planet Transits (Years-Long Themes)

These are the most significant. Check which outer planets (Jupiter through Pluto) are currently making major aspects (conjunction, square, opposition, trine) to natal planets.

| Transit | Themes |
|---------|--------|
| **Transiting Jupiter** conjunct/trine natal planet | Expansion, opportunity, growth in that area |
| **Transiting Jupiter** square/opposition natal planet | Over-expansion, overconfidence; test of growth |
| **Transiting Saturn** conjunct natal planet | Discipline required; reality check; mastery being tested |
| **Transiting Saturn** square natal planet | Friction between current structure and life goals; hard work required |
| **Transiting Saturn** opposition natal planet | Major life audit; something must end or be restructured |
| **Transiting Saturn** trine/sextile natal planet | Support for disciplined effort; good time to formalize |
| **Transiting Uranus** conjunct/square/opposition natal planet | Unexpected change, disruption, liberation; what's outgrown falls away |
| **Transiting Uranus** trine/sextile natal planet | Exciting innovation; progressive change on good terms |
| **Transiting Neptune** conjunct/square/opposition natal planet | Fog, confusion, spiritual opening; be wary of illusions |
| **Transiting Neptune** trine/sextile natal planet | Spiritual gift, creativity, compassion deepened |
| **Transiting Pluto** conjunct natal planet | Profound, irreversible transformation; death and rebirth of that area |
| **Transiting Pluto** square/opposition natal planet | Power struggle, intense pressure; forced transformation |
| **Transiting Pluto** trine/sextile natal planet | Deep empowerment; access to hidden strength |

### Step 2 — Saturn & Jupiter Cycles

**Saturn Return** (~age 29, 58): Major identity restructuring. Old structures that no longer serve must be released. New adult chapter begins.

**Jupiter Return** (~every 12 years): New growth cycle begins. The house Jupiter returns to shows where a lucky new chapter opens.

**Saturn transiting the 4 Angles** (conjunct Ascendant, IC, Descendant, Midheaven): Each is a major threshold crossing:
- Conjunct Ascendant: New identity, new chapter begins
- Conjunct IC: Foundation restructuring; family matters
- Conjunct Descendant: Relationship reality check
- Conjunct Midheaven: Career peak or major shift

### Step 3 — Inner Planet Transits (Weeks — Timing & Events)

Use these to time events within the longer outer planet themes.

- **Transiting Mars** triggers natal planets: activation, action, possible conflict
- **Transiting Venus** triggers natal planets: harmony, pleasure, relationship moments
- **Transiting Mercury** over natal planets: mental clarity, communication events
- **Transiting Sun** over natal planets: annual spotlight and activation

### Step 3.5 — Optional asteroid transit layer

If the output includes `transit_asteroid_aspects[]`, use only the tightest 1-2 contacts that clearly sharpen the main story:

- **Juno**: commitment, agreements, reciprocity, relationship contract pressure
- **Ceres**: care, nourishment, attachment, soothing / depletion patterns
- **Vesta**: devotion, sacrifice, focus, what must be protected
- **Pallas**: strategy, discernment, problem-solving pattern

These contacts refine the reading; they should not replace the main outer/inner-planet transit backbone.

### Step 4 — Current Themes Summary

The `current_themes[]` array from the ephemeris output summarizes active themes. Use these as chapter headings in the reading.

Expand each theme using:
- Which planets are involved (from `transit_aspects[]`)
- The aspect type (see `aspects.md`)
- How long the transit lasts (from planet speed table above)

### Step 5 — Timing Guidance

Give the person a practical timeline:
- What is active **right now** (within 2 weeks orb)
- What is building over the **next 3 months**
- What major theme shapes the **next 1–2 years** (outer planets)

### Step 6 — Suggestions for Working with the Energies

For each major active transit, offer:
1. The core theme
2. What to lean into
3. What to watch out for
4. A practical action or mindset


## Delivering the Reading

Structure:
1. **Overview**: "Right now, the sky is activating [area(s)] of your chart..."
2. **Long-term themes** (outer planets): the underlying story for the next months/years
3. **Shorter-term highlights** (inner planets, Mars): immediate focus areas
4. **Current themes** from ephemeris output: name and interpret each
5. **Timeline**: what's building, what's peaking, what's passing
6. **Closing**: affirm how the person can consciously work with these energies

---

## Common Transit Phrases

| Transit | Opening phrase |
|---------|---------------|
| Jupiter conjunct Sun | "A fortunate window for expansion in your sense of self and visibility..." |
| Saturn conjunct Moon | "Emotional responsibilities are coming into focus; this is a time to build inner structure..." |
| Uranus square natal Sun | "A period of unexpected change in your identity and life direction..." |
| Neptune conjunct Venus | "A spiritually rich but potentially confusing time in relationships and values..." |
| Pluto opposition Moon | "A profound, years-long process of emotional transformation is underway..." |
