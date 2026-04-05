---
name: interview_intel
description: Trigger when generating any pre-interview brief to surface reported questions and culture notes.
---

Trigger when generating any pre-interview brief (always invoked alongside company_research).

1. Call `get_interview_questions(company_name, role)` from `tools/interview_intel.py` — searches Glassdoor and Teamblind, returns up to 5 question-like sentences.
2. Call `get_company_culture_notes(company_name)` — returns top 3 Glassdoor review snippets.
3. Return at most 5 questions. State the source (Glassdoor/Blind).
4. If no public data is found, return "No public interview questions found for [company] [role]" exactly. Do not guess or generate questions.
