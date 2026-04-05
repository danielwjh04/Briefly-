---
name: company_research
description: Trigger when generating any pre-interview brief or when user mentions an upcoming interview with a specific company.
---

Trigger when user runs /brief or mentions an upcoming interview with a named company.

1. Call `get_company_news(company_name)` from `tools/company_research.py` — returns top 4 news results with title, snippet, and source.
2. Call `get_github_activity(company_github_handle)` using the company name lowercased with spaces removed as the handle.
3. Never fabricate results. If a function returns no data, pass that message through verbatim.
4. Return both results to the brief generator. Do not summarise or interpret before passing.
