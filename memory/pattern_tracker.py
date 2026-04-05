from memory.store import get_all

CATEGORIES = [
    "system design",
    "behavioural",
    "data structures",
    "algorithms",
    "sql",
    "probability and statistics",
    "product sense",
    "communication",
]

DRILLS = {
    "system design": "Design a URL shortener end-to-end: define requirements, estimate scale, draw component diagram, pick a DB schema, discuss trade-offs. Time-box to 30 minutes.",
    "behavioural": "Write STAR-format answers for: a time you failed, a conflict with a teammate, a project you led under pressure. Practice out loud, under 2 minutes each.",
    "data structures": "Solve 5 LeetCode medium problems using only hash maps and stacks/queues. Focus on explaining your choice of data structure before writing any code.",
    "algorithms": "Complete one LeetCode daily challenge + one sliding window problem. Narrate your thought process aloud as if in an interview.",
    "sql": "Write 10 queries on a sample schema covering GROUP BY, window functions (ROW_NUMBER, LAG), and a self-join. Use db-fiddle.com to verify.",
    "probability and statistics": "Solve 3 probability puzzles from Brilliant.org (combinatorics section). For each, write out the sample space before solving.",
    "product sense": "Pick one app you use daily. Write a 1-page product critique: top user pain point, proposed fix, and how you'd measure success. Post it to a notes app for review.",
    "communication": "Record yourself answering two behavioural questions. Watch the playback and cut filler words (um, like, basically). Re-record until under 90 seconds.",
}


def analyse_patterns() -> dict:
    data = get_all()
    interviews = data.get("interviews", [])

    if not interviews:
        return {
            "total": 0,
            "weak_spots": [],
            "strong_spots": [],
            "win_rate": "0% (no interviews logged)",
            "suggested_drill": None,
        }

    category_counts = {cat: 0 for cat in CATEGORIES}
    category_struggles = {cat: 0 for cat in CATEGORIES}

    wins = 0
    for interview in interviews:
        outcome = interview.get("outcome", "").lower()
        if outcome in ("offer", "next round"):
            wins += 1

        question_types = interview.get("question_types", [])
        if isinstance(question_types, str):
            question_types = [q.strip().lower() for q in question_types.split(",")]
        else:
            question_types = [q.strip().lower() for q in question_types]

        struggled = interview.get("struggled_with", [])
        if isinstance(struggled, str):
            struggled = [s.strip().lower() for s in struggled.split(",")]
        else:
            struggled = [s.strip().lower() for s in struggled]

        for cat in CATEGORIES:
            for qt in question_types:
                if cat in qt:
                    category_counts[cat] += 1
            for s in struggled:
                if cat in s:
                    category_struggles[cat] += 1

    total = len(interviews)
    win_rate_pct = round((wins / total) * 100) if total > 0 else 0
    win_rate = f"{win_rate_pct}% ({wins}/{total} offers or next rounds)"

    # Rank by struggle frequency, break ties by appearance count
    ranked = sorted(
        [(cat, category_struggles[cat], category_counts[cat]) for cat in CATEGORIES],
        key=lambda x: (-x[1], -x[2]),
    )

    weak_spots = [
        {"category": cat, "struggle_count": struggles, "appearance_count": appearances}
        for cat, struggles, appearances in ranked
        if struggles > 0
    ][:3]

    strong_spots = [
        cat for cat, struggles, appearances in ranked
        if appearances > 0 and struggles == 0
    ]

    top_weak = weak_spots[0]["category"] if weak_spots else None
    suggested_drill = DRILLS.get(top_weak) if top_weak else None

    return {
        "total": total,
        "weak_spots": weak_spots,
        "strong_spots": strong_spots,
        "win_rate": win_rate,
        "suggested_drill": suggested_drill,
        "top_weak_category": top_weak,
    }


def format_pattern_report(analysis: dict) -> str:
    if analysis["total"] == 0:
        return "*INTERVIEW PATTERN REPORT*\n\nNo interviews logged yet. Use /debrief after each interview to build your pattern history."

    lines = [
        "*INTERVIEW PATTERN REPORT*\n",
        f"*Total interviews logged:* {analysis['total']}",
        f"*Win rate:* {analysis['win_rate']}\n",
    ]

    if analysis["weak_spots"]:
        lines.append("*WEAK SPOTS (ranked by frequency)*")
        for i, spot in enumerate(analysis["weak_spots"], 1):
            lines.append(f"{i}. {spot['category'].title()} — {spot['struggle_count']} struggles")
        lines.append("")

    if analysis["strong_spots"]:
        lines.append("*STRONG SPOTS*")
        lines.append(", ".join(s.title() for s in analysis["strong_spots"]))
        lines.append("")

    if analysis["suggested_drill"]:
        lines.append("*THIS WEEK'S DRILL*")
        lines.append(f"_{analysis['top_weak_category'].title()} focus:_ {analysis['suggested_drill']}")

    return "\n".join(lines)
