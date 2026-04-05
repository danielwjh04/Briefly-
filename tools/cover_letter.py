from config import client, MODEL
from memory.store import get_all

COVER_LETTER_PROMPT = """Generate a professional cover letter with exactly 3 paragraphs and a maximum of 200 words total.

Rules:
- Paragraph 1: Start with a specific accomplishment from the user's profile. Never start with "I am writing to express my interest" or any variation.
- Paragraph 2: Explain why this specific company, referencing something concrete about them (product, mission, recent news if provided).
- Paragraph 3: Short call to action. No filler.
- No subject line, no salutation, no sign-off — body paragraphs only.
- Do not exceed 200 words.
- Use plain text, no markdown."""


def generate_cover_letter(company: str, role: str) -> str:
    """
    Load user profile from memory and generate a 3-paragraph cover letter
    using Agnes via ZenMux.
    """
    data = get_all()
    profile = data.get("profile", {})

    if not profile:
        return (
            "No profile found. Please set up your profile first with /profile.\n"
            "Example: /profile name=Your Name degree=Computer Science skills=Python,SQL gpa=4.5"
        )

    profile_text = "\n".join(f"{k}: {v}" for k, v in profile.items())

    user_message = (
        f"Write a cover letter for the following position:\n"
        f"Company: {company}\n"
        f"Role: {role}\n\n"
        f"User profile:\n{profile_text}"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": COVER_LETTER_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=2048,
            temperature=0.7,
        )
        content = response.choices[0].message.content
        if content is None:
            return "Cover letter generation failed: Agnes returned an empty response."
        return content.strip()
    except Exception as e:
        return f"Cover letter generation failed: {e}"
