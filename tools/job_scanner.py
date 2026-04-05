import re
import requests


def _trim_desc(text: str, limit: int = 200) -> str:
    if len(text) <= limit:
        return text
    # Try to cut at last sentence end within limit
    cut = text[:limit]
    last_stop = max(cut.rfind(". "), cut.rfind(".\n"))
    if last_stop > 80:
        return cut[:last_stop + 1]
    return cut.rstrip() + "..."


def _strip_html(text: str) -> str:
    # Replace block-level tags with a space so words don't merge
    text = re.sub(r"<(p|li|h[1-6]|div|br)[^>]*>", " ", text, flags=re.IGNORECASE)
    # Remove remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Collapse multiple spaces/newlines
    text = re.sub(r"\s+", " ", text)
    return text.strip()

MCF_API_URL = "https://api.mycareersfuture.gov.sg/v2/jobs"

MCF_HEADERS = {
    "User-Agent": "InternBrief/1.0 (NUS student job search agent)",
    "Accept": "application/json",
}


def search_jobs(keyword: str, limit: int = 10) -> list[dict]:
    """
    Search MyCareersFuture API v2 for live job listings.
    Returns list of dicts: title, company, salary, url, description.
    """
    params = {
        "search": keyword,
        "limit": limit,
        "page": 0,
    }

    try:
        resp = requests.get(MCF_API_URL, params=params, headers=MCF_HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        return [{"error": f"MyCareersFuture API request failed: {e}"}]

    data = resp.json()
    raw_jobs = data.get("results", [])

    if not raw_jobs:
        return []

    jobs = []
    for job in raw_jobs:
        salary_min = job.get("salary", {}).get("minimum")
        salary_max = job.get("salary", {}).get("maximum")
        if salary_min and salary_max:
            salary = f"SGD {salary_min:,} – {salary_max:,}/month"
        elif salary_min:
            salary = f"SGD {salary_min:,}+/month"
        else:
            salary = "Not specified"

        uuid = job.get("uuid", "")
        url = f"https://www.mycareersfuture.gov.sg/job/{uuid}" if uuid else "https://www.mycareersfuture.gov.sg"

        jobs.append({
            "title": job.get("title", "Unknown Title"),
            "company": job.get("postedCompany", {}).get("name", "Unknown Company"),
            "salary": salary,
            "url": url,
            "description": _trim_desc(_strip_html(job.get("description") or "")),
        })

    return jobs


def format_jobs_for_telegram(jobs: list[dict]) -> str:
    """Format job results for Telegram markdown."""
    if not jobs:
        return "No listings found on MyCareersFuture for that keyword."

    if jobs and "error" in jobs[0]:
        return jobs[0]["error"]

    lines = []
    for job in jobs:
        lines.append(
            f"*{job['title']}* — {job['company']}\n"
            f"Salary: {job['salary']}\n"
            f"{job['description']}\n"
            f"{job['url']}"
        )

    return "\n\n".join(lines)
