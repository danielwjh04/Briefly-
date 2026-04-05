import re
import requests
from bs4 import BeautifulSoup

DDGO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Regex to detect question-like sentences
QUESTION_PATTERN = re.compile(
    r"(what|how|why|describe|tell me|walk me|explain|have you|can you|do you|"
    r"give me|what would|design|implement|solve)[^.!?]{10,120}[?]",
    re.IGNORECASE,
)


def _ddgo_search(query: str) -> list[dict]:
    url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
    try:
        resp = requests.get(url, headers=DDGO_HEADERS, timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for result in soup.select(".result__body"):
        title_el = result.select_one(".result__title")
        snippet_el = result.select_one(".result__snippet")
        source_el = result.select_one(".result__url")
        results.append({
            "title": title_el.get_text(strip=True) if title_el else "",
            "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
            "source": source_el.get_text(strip=True) if source_el else "",
        })
    return results


def get_interview_questions(company_name: str, role: str) -> str:
    """
    Search DuckDuckGo targeting glassdoor.com and teamblind.com for interview questions.
    Returns up to 5 question-like sentences.
    """
    query = f'site:glassdoor.com OR site:teamblind.com "{company_name}" "{role}" interview questions'
    results = _ddgo_search(query)

    if not results:
        # Fallback without site restriction
        query = f'"{company_name}" {role} interview questions glassdoor teamblind'
        results = _ddgo_search(query)

    if not results:
        return f"No public interview questions found for {company_name} {role}."

    # Extract question-like sentences from all snippets
    questions = []
    seen = set()
    for r in results:
        text = r["title"] + " " + r["snippet"]
        matches = QUESTION_PATTERN.findall(text)
        # findall returns the capture group; get full match
        for match in re.finditer(
            r"(what|how|why|describe|tell me|walk me|explain|have you|can you|do you|"
            r"give me|what would|design|implement|solve)[^.!?]{10,120}[?]",
            text,
            re.IGNORECASE,
        ):
            q = match.group(0).strip()
            normalized = q.lower()
            if normalized not in seen:
                seen.add(normalized)
                questions.append(q)
            if len(questions) >= 5:
                break
        if len(questions) >= 5:
            break

    if not questions:
        # Fall back to returning raw snippets
        snippets = [r["snippet"] for r in results[:3] if r["snippet"]]
        if snippets:
            return (
                f"No specific questions extracted. Relevant snippets from search results:\n"
                + "\n".join(f"• {s[:200]}" for s in snippets)
            )
        return f"No public interview questions found for {company_name} {role}."

    lines = [f"{i}. {q}" for i, q in enumerate(questions, 1)]
    return "*Reported interview questions (Glassdoor/Blind):*\n" + "\n".join(lines)


def get_interview_process(company_name: str, role: str) -> str:
    """
    Search for the known interview process/stages for a company and role.
    Returns a description of stages (e.g. OA → HireVue → panel rounds).
    """
    query = f'site:glassdoor.com OR site:teamblind.com "{company_name}" "{role}" interview process stages rounds'
    results = _ddgo_search(query)

    if not results:
        query = f'"{company_name}" {role} interview process online assessment rounds glassdoor'
        results = _ddgo_search(query)

    if not results:
        return f"No publicly reported interview process found for {company_name} {role}."

    # Keywords indicating stages/process
    PROCESS_PATTERN = re.compile(
        r"(online assessment|hackerrank|codility|hirevue|phone screen|technical screen|"
        r"take.home|coding test|panel interview|onsite|round \d|first round|second round|"
        r"hiring manager|case study|group discussion|aptitude test)[^.!?]{0,120}[.!?]?",
        re.IGNORECASE,
    )

    stages = []
    seen = set()
    for r in results[:5]:
        text = r["title"] + " " + r["snippet"]
        for match in PROCESS_PATTERN.finditer(text):
            stage = match.group(0).strip().rstrip(".,;")
            normalized = stage.lower()
            if normalized not in seen and len(stage) > 15:
                seen.add(normalized)
                stages.append(stage)
            if len(stages) >= 4:
                break
        if len(stages) >= 4:
            break

    if not stages:
        snippets = [r["snippet"] for r in results[:2] if r["snippet"]]
        if snippets:
            return (
                "Process details (from search):\n"
                + "\n".join(f"• {s[:200]}" for s in snippets)
            )
        return f"No publicly reported interview process found for {company_name} {role}."

    lines = [f"• {s}" for s in stages]
    return "*Reported process stages (Glassdoor/Blind):*\n" + "\n".join(lines)


def get_company_culture_notes(company_name: str) -> str:
    """
    Search DuckDuckGo targeting glassdoor.com reviews for culture notes.
    Returns top 3 snippets.
    """
    query = f'site:glassdoor.com "{company_name}" reviews culture work environment'
    results = _ddgo_search(query)

    if not results:
        query = f'"{company_name}" glassdoor reviews culture work life balance'
        results = _ddgo_search(query)

    if not results:
        return f"No public culture data found for {company_name}."

    snippets = []
    for r in results[:3]:
        if r["snippet"]:
            snippets.append(f"• {r['snippet'][:200]} _(Source: {r['source'] or 'Glassdoor'})_")

    if not snippets:
        return f"No public culture data found for {company_name}."

    return "*Culture notes (Glassdoor):*\n" + "\n".join(snippets)
