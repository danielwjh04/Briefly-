---
name: job_scanner
description: Trigger when user runs /jobs to search live Singapore job listings on MyCareersFuture.
---

Trigger when user runs /jobs with a keyword argument.

1. Call `search_jobs(keyword)` from `tools/job_scanner.py` using MyCareersFuture API v2.
2. Call `format_jobs_for_telegram(jobs)` to format results.
3. Each result must include: job title, company name, salary range (or "Not specified"), and direct listing URL.
4. Return up to 10 results. If the API returns nothing, say "No listings found on MyCareersFuture for [keyword]."
5. Never fabricate job listings or URLs.
