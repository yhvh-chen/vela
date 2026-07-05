# Birth-Time Rectification (Lightweight)

Triage protocol for uncertain birth times. Resolution target is the **ascendant sign** (a ~2-hour window), never minute precision — claiming more is performance, not craft.

## When to run — and when not to

- **Run only when the user raises the doubt themselves** ("时间可能不准" / "只知道大概上午" / "户口本上是整点"). The default is to trust the stated birth time.
- If the calibration question in the consultation loop misses but the user is **confident** in their birth time, the problem is the interpretation — re-diagnose the reading, do not blame the clock.
- If the stated time already produces an ascendant within ~3° of a sign boundary, mention the sensitivity in the reading's technical note, but still do not rectify unless the user asks.

## Protocol

1. **Collect 2-4 dated turning points.** Ask for years (month if known) of events in these categories — they are the ones heavy transits to the angles mark most reliably:
   - relocation or major career change
   - a significant relationship beginning or ending (marriage, divorce, defining breakup)
   - major family upheaval (loss, split, crisis)
   - a major health event or accident
   Phrase it as one question, in the user's language: "说 2-4 件带年份的大事——换过城市或行业、重要关系的开始或结束、家里的大变故。"

2. **Run the scan**: `script/rectify.py` with birth date, location, and the events. Default 2-hour grid (12 ascendant candidates); it scores each candidate by heavy transits (Jupiter–Pluto, weighted) and solar-arc directions crossing that candidate's four angles in the event years.

3. **Read the result honestly:**
   - **Clear leader** (top score comfortably ahead): present the rising sign and its time window — "你的上升更可能在X座，对应出生时间大约在 HH:MM–HH:MM 之间" — then re-cast the chart with the window's midpoint and tell the user exactly which conclusions changed from the original reading.
   - **Close scores**: say the scan is inconclusive and ask for one more dated event. Never break ties by narrative preference.
   - **`moon_sign_boundary_day: true`**: the Moon changes sign that day — flag which emotional readings depend on the time before proceeding.

4. **Confirm forward, not just backward.** After re-casting, give the user one falsifiable expectation ("如果这个时间对，X年前后你应该经历过/将经历……") so the corrected chart keeps earning trust with lived evidence.

## Honesty rules

- State the resolution plainly: sign-level, from N events — more events, more confidence.
- The scan supports a rising sign; it does not certify a birth minute. Angle-degree-sensitive techniques (exact returns, precise house cusps near boundaries) stay soft-flagged even after rectification.
- If the user's stated time and the scan's leader agree, say so — confirmation is also a result.
