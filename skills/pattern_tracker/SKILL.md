---
name: pattern_tracker
description: Trigger when user runs /patterns or when the weekly Monday scheduler fires to surface interview weak spots.
---

Trigger when user runs /patterns or on the weekly Monday 8am SGT scheduled job.

1. Call `analyse_patterns()` from `memory/pattern_tracker.py` — reads all logged interviews from memory.
2. Call `format_pattern_report(analysis)` to produce the formatted report.
3. Report must include: total interviews logged, win rate, weak spots ranked by struggle frequency (top 3), strong spots, and one specific drill targeting the top weak spot.
4. If no interviews are logged, return "No interviews logged yet. Use /debrief after each interview."
5. Never invent categories or manufacture patterns from insufficient data.
