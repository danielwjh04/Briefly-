---
name: cover_letter
description: Trigger when user runs /cover to generate a targeted 3-paragraph cover letter from their profile.
---

Trigger when user runs /cover [Company] [Role].

1. Load user profile from memory via `store.get_all()`. If no profile exists, return instructions to set one with /profile.
2. Call `generate_cover_letter(company, role)` from `tools/cover_letter.py`, which calls Agnes via ZenMux.
3. Output must be exactly 3 paragraphs, maximum 200 words total.
4. Paragraph 1 must start with a specific accomplishment from the user's profile. Never start with "I am writing to express my interest" or any generic opener.
5. Paragraph 2 references something concrete about the target company.
6. Paragraph 3 is a call to action.
