import requests
from bs4 import BeautifulSoup

DDGO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def get_company_news(company_name: str) -> str:
    """
    Search DuckDuckGo HTML for recent company news.
    Returns top 4 results as a formatted string: title, snippet, source.
    """
    query = f"{company_name} company news 2024 2025"
    url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"

    try:
        resp = requests.get(url, headers=DDGO_HEADERS, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        return f"News search failed: {e}"

    soup = BeautifulSoup(resp.text, "html.parser")
    results = soup.select(".result__body")

    if not results:
        return f"No recent news found for {company_name}."

    output_lines = []
    for result in results[:4]:
        title_el = result.select_one(".result__title")
        snippet_el = result.select_one(".result__snippet")
        source_el = result.select_one(".result__url")

        title = title_el.get_text(strip=True) if title_el else "No title"
        snippet = snippet_el.get_text(strip=True) if snippet_el else "No snippet"
        source = source_el.get_text(strip=True) if source_el else "Unknown source"

        output_lines.append(f"• *{title}*\n  {snippet}\n  _Source: {source}_")

    return "\n\n".join(output_lines)


def get_github_activity(company_github_handle: str) -> str:
    """
    Fetch public repos for a GitHub org/user handle.
    Returns active repos and languages seen.
    """
    if not company_github_handle:
        return "No GitHub handle provided."

    url = f"https://api.github.com/orgs/{company_github_handle}/repos?sort=updated&per_page=10"
    headers = {"Accept": "application/vnd.github+json"}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 404:
            # Try user endpoint if org not found
            url = f"https://api.github.com/users/{company_github_handle}/repos?sort=updated&per_page=10"
            resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 404:
            return f"No public GitHub profile found for handle: {company_github_handle}"
        resp.raise_for_status()
    except requests.RequestException as e:
        return f"GitHub API request failed: {e}"

    repos = resp.json()
    if not repos:
        return f"No public repositories found for {company_github_handle}."

    languages = set()
    repo_lines = []
    for repo in repos[:5]:
        name = repo.get("name", "unknown")
        lang = repo.get("language")
        stars = repo.get("stargazers_count", 0)
        description = repo.get("description") or "No description"
        if lang:
            languages.add(lang)
        repo_lines.append(f"• `{name}` ({lang or 'unknown lang'}, ⭐{stars}) — {description[:80]}")

    lang_summary = ", ".join(sorted(languages)) if languages else "unknown"
    header = f"*Active repos (top 5):*\n" + "\n".join(repo_lines)
    footer = f"\n*Languages seen:* {lang_summary}"
    return header + footer
