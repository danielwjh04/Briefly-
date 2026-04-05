import asyncio
import logging
import re
from io import BytesIO

from config import client, MODEL, SYSTEM_PROMPT
from memory import store
from memory.pattern_tracker import analyse_patterns, format_pattern_report
from tools.company_research import get_company_news
from tools.job_scanner import search_jobs, format_jobs_for_telegram
from tools.cover_letter import generate_cover_letter

logger = logging.getLogger(__name__)

# In-memory debrief session state keyed by Telegram user_id
debrief_sessions: dict[int, dict] = {}

# In-memory question sessions keyed by Telegram user_id
# { user_id: { "questions": [...], "company": "...", "role": "..." } }
question_sessions: dict[int, dict] = {}

DEBRIEF_QUESTIONS = [
    "1/5 — What *company* and *role* did you interview for?",
    "2/5 — What *question types* came up? (e.g. behavioural, system design, algorithms, SQL)",
    "3/5 — Which questions did you *struggle with*? Be specific.",
    "4/5 — What went *well*?",
    "5/5 — What's the *outcome* so far? (pending / rejected / offer / next round)",
]

DEBRIEF_KEYS = ["company_role", "question_types", "struggled_with", "went_well", "outcome"]

HELP_TEXT = r"""*InternBrief* — NUS internship prep agent

*Commands:*
/brief \[Company\] \[Role\] — Pre-interview brief with company news, GitHub activity, and interview intel
/debrief — Log an interview step-by-step
/patterns — Analyse your weak interview categories and get a drill
/jobs \[keyword\] — Search live listings on MyCareersFuture
/cover \[Company\] \[Role\] — Generate a 3-paragraph cover letter
/profile — View or update your profile
/clear — Clear conversation history

*Profile setup example:*
`/profile name=Jane Tan degree=Computer Science skills=Python,SQL,React gpa=4.2 year=3`
"""


def _call_agnes(messages: list[dict]) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=2048,
            temperature=0.4,
            timeout=60,
        )
        content = response.choices[0].message.content
        if content is None:
            logger.error("Agnes returned null content. Finish reason: %s", response.choices[0].finish_reason)
            return "Agnes returned an empty response. The model may have been filtered or hit a limit."
        return content.strip()
    except Exception as e:
        logger.error("Agnes API call failed: %s", e)
        return f"Agnes API error: {e}"


def _split_message(text: str, limit: int = 4000) -> list[str]:
    """Split text into chunks under `limit` chars, breaking on newlines then spaces."""
    chunks = []
    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = text.rfind(" ", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at].rstrip())
        text = text[split_at:].lstrip()
    if text:
        chunks.append(text)
    return chunks


async def _safe_reply(message, text: str) -> None:
    """Send a reply, splitting on Telegram's 4096-char limit and falling back to plain text on Markdown errors."""
    for chunk in _split_message(text):
        try:
            await message.reply_text(chunk, parse_mode="Markdown")
        except Exception:
            try:
                await message.reply_text(chunk)
            except Exception as e:
                logger.error("Failed to send reply chunk: %s", e)


async def handle_start(update, context):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def handle_help(update, context):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def handle_brief(update, context):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: `/brief [Company] [Role]`\nExample: `/brief Grab Software Engineer`",
            parse_mode="Markdown",
        )
        return

    company = args[0]
    role = " ".join(args[1:])
    await update.message.reply_text(
        f"Researching *{company}* for *{role}*...",
        parse_mode="Markdown",
    )

    loop = asyncio.get_event_loop()
    news = await loop.run_in_executor(None, get_company_news, company)

    # Check if user has prior interviews for weak spots section
    data = store.get_all()
    interviews = data.get("interviews", [])
    weak_spots_context = "\n\nNO_INTERVIEW_HISTORY"
    if interviews:
        analysis = analyse_patterns()
        if analysis["weak_spots"]:
            weak_spots_context = "\n\nUser weak spots from interview history:\n" + "\n".join(
                f"- {w['category']}: {w['struggle_count']} struggles"
                for w in analysis["weak_spots"]
            )

    prompt = (
        f"Generate a pre-interview brief for:\nCompany: {company}\nRole: {role}\n\n"
        f"COMPANY NEWS:\n{news}"
        f"{weak_spots_context}\n\n"
        f"Follow the BRIEF FORMAT exactly. Max 600 words. Use Telegram markdown."
    )

    history = store.get_conversation_history()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": prompt}]

    brief = await loop.run_in_executor(None, _call_agnes, messages)

    store.append_conversation("user", prompt)
    store.append_conversation("assistant", brief)
    store.log_application(company, role)

    await _safe_reply(update.message, brief)


async def handle_debrief(update, context):
    user_id = update.effective_user.id
    debrief_sessions[user_id] = {"step": 0, "answers": {}}
    await update.message.reply_text(
        "*Starting interview debrief* — answer each question to save your session.\n\n"
        + DEBRIEF_QUESTIONS[0],
        parse_mode="Markdown",
    )


async def handle_debrief_step(update, context):
    user_id = update.effective_user.id
    session = debrief_sessions.get(user_id)
    if not session:
        return False

    step = session["step"]
    answer = update.message.text.strip()
    key = DEBRIEF_KEYS[step]
    session["answers"][key] = answer
    session["step"] += 1

    if session["step"] < len(DEBRIEF_QUESTIONS):
        await update.message.reply_text(
            DEBRIEF_QUESTIONS[session["step"]], parse_mode="Markdown"
        )
    else:
        # Save to memory
        answers = session["answers"]
        company_role = answers.get("company_role", "Unknown")
        parts = company_role.split(" ", 1)
        company = parts[0]
        role = parts[1] if len(parts) > 1 else "Unknown"

        notes = {
            "question_types": answers.get("question_types", ""),
            "struggled_with": answers.get("struggled_with", ""),
            "went_well": answers.get("went_well", ""),
            "outcome": answers.get("outcome", "pending"),
        }
        store.log_interview(company, role, notes)
        del debrief_sessions[user_id]

        await update.message.reply_text(
            f"*Debrief saved* for *{company}* — {role}.\n"
            "Run /patterns to see your interview trends.",
            parse_mode="Markdown",
        )

    return True


async def handle_patterns(update, context):
    analysis = analyse_patterns()
    report = format_pattern_report(analysis)
    await _safe_reply(update.message, report)


async def handle_jobs(update, context):
    if not context.args:
        await update.message.reply_text(
            "Usage: `/jobs [keyword]`\nExample: `/jobs software engineer`",
            parse_mode="Markdown",
        )
        return

    keyword = " ".join(context.args)
    await update.message.reply_text(
        f"Searching MyCareersFuture for *{keyword}*...", parse_mode="Markdown"
    )

    loop = asyncio.get_event_loop()
    jobs = await loop.run_in_executor(None, search_jobs, keyword)
    result = format_jobs_for_telegram(jobs)

    await update.message.reply_text(result, parse_mode="Markdown")


async def handle_cover(update, context):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: `/cover [Company] [Role]`\nExample: `/cover GovTech Product Manager`",
            parse_mode="Markdown",
        )
        return

    company = args[0]
    role = " ".join(args[1:])
    await update.message.reply_text(
        f"Generating cover letter for *{company}* — {role}...", parse_mode="Markdown"
    )

    loop = asyncio.get_event_loop()
    letter = await loop.run_in_executor(None, generate_cover_letter, company, role)

    await _safe_reply(update.message, letter)


async def handle_profile(update, context):
    args = context.args
    data = store.get_all()
    profile = data.get("profile", {})

    if not args:
        if not profile:
            await update.message.reply_text(
                "No profile set.\n\nUsage: `/profile key=value key2=value2`\n"
                "Example: `/profile name=Jane degree=CS skills=Python,SQL gpa=4.2 year=3`",
                parse_mode="Markdown",
            )
        else:
            lines = [f"*{k}:* {v}" for k, v in profile.items()]
            await update.message.reply_text(
                "*Your Profile:*\n" + "\n".join(lines), parse_mode="Markdown"
            )
        return

    updates = {}
    for arg in args:
        if "=" in arg:
            k, _, v = arg.partition("=")
            updates[k.strip()] = v.strip()

    if not updates:
        await update.message.reply_text(
            "Invalid format. Use `key=value` pairs.\nExample: `/profile name=Jane gpa=4.2`",
            parse_mode="Markdown",
        )
        return

    store.update_profile(updates)
    lines = [f"*{k}:* {v}" for k, v in updates.items()]
    await update.message.reply_text(
        "*Profile updated:*\n" + "\n".join(lines), parse_mode="Markdown"
    )


async def handle_clear(update, context):
    store.clear_conversation()
    await update.message.reply_text("Conversation history cleared.")


def _ocr_image(image_bytes: bytes) -> str:
    """Run EasyOCR on image bytes and return extracted text."""
    import easyocr
    import numpy as np
    from PIL import Image

    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img_array = np.array(img)
    reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    results = reader.readtext(img_array, detail=0, paragraph=True)
    return "\n".join(results)


def _parse_interview_fields_regex(ocr_text: str) -> dict:
    """Extract interview fields from OCR text using regex patterns."""
    text = ocr_text

    details = {
        "company": None,
        "role": None,
        "interview_date": None,
        "interview_time": None,
        "interviewer_name": None,
        "other_details": None,
    }

    # Role: prefer explicit "Role:" label (requires colon, so it won't match
    # the word "position" in body sentences like "...position at Grab...")
    role_match = re.search(r'\brole\s*:\s*([^\n]+)', text, re.IGNORECASE)
    if role_match:
        details["role"] = role_match.group(1).strip(" -–—")
    else:
        # Fall back to "applying to the X position" sentence pattern
        applying_match = re.search(
            r'applying to the\s+(.+?)\s+position\b', text, re.IGNORECASE
        )
        if applying_match:
            details["role"] = applying_match.group(1).strip()

    # Company: extract from "position at [Company]" — stop at first non-alpha
    # char (handles OCR artefacts like "Grab_" or "Grab.")
    company_match = re.search(
        r'\bposition at\s+([A-Za-z][A-Za-z0-9]*(?:\s[A-Z][A-Za-z0-9]*){0,2})',
        text,
    )
    if company_match:
        details["company"] = company_match.group(1).strip()
    else:
        labelled = re.search(r'\bcompany\s*:\s*([^\n]+)', text, re.IGNORECASE)
        if labelled:
            details["company"] = labelled.group(1).strip()

    # Date: prefer "Date: Wednesday, 16 April 2025" label format.
    # The labelled pattern requires a day-of-week OR bare date after "Date:".
    date_match = re.search(
        r'\bdate\s*:\s*([A-Za-z]+,?\s+\d{1,2}\s+[A-Za-z]+\s+\d{4})',
        text, re.IGNORECASE,
    )
    if not date_match:
        # Prefer dates that include a day-of-week (more likely to be the
        # interview date than the email's sent-date header)
        date_match = re.search(
            r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)'
            r',?\s+\d{1,2}\s+[A-Za-z]+\s+\d{4}\b',
            text, re.IGNORECASE,
        )
    if not date_match:
        # Last resort: any bare date — skips 1-2 digit day-only numbers
        date_match = re.search(
            r'\b(\d{1,2}\s+[A-Za-z]{3,}\s+\d{4})\b', text
        )
    if date_match:
        details["interview_date"] = date_match.group(1).strip()

    # Time: e.g. "2:00 PM – 3:00 PM SGT"
    time_match = re.search(
        r'(\d{1,2}:\d{2}\s*(?:AM|PM)\s*[-–—]\s*\d{1,2}:\d{2}\s*(?:AM|PM)'
        r'(?:\s+[A-Z]{2,4})?)',
        text, re.IGNORECASE,
    )
    if time_match:
        details["interview_time"] = time_match.group(1).strip()

    # Interviewer: labelled field
    interviewer_match = re.search(
        r'\binterviewer\s*:\s*([^\n]+)', text, re.IGNORECASE
    )
    if interviewer_match:
        details["interviewer_name"] = interviewer_match.group(1).strip()

    # Format / other details
    format_match = re.search(r'\bformat\s*:\s*([^\n]+)', text, re.IGNORECASE)
    if format_match:
        details["other_details"] = format_match.group(1).strip()

    return details


async def handle_photo(update, context):
    """Handle uploaded interview invitation screenshot."""
    await update.message.reply_text(
        "Scanning your interview invitation... extracting details.",
        parse_mode="Markdown",
    )

    # Download highest-res photo
    photo = update.message.photo[-1]
    file = await photo.get_file()
    buf = BytesIO()
    await file.download_to_memory(buf)

    # Run OCR in thread (CPU-bound)
    loop = asyncio.get_event_loop()
    try:
        ocr_text = await loop.run_in_executor(None, _ocr_image, buf.getvalue())
    except Exception as e:
        await update.message.reply_text(f"OCR failed: {e}")
        return

    if not ocr_text.strip():
        await update.message.reply_text("Could not read any text from the image. Please try a clearer screenshot.")
        return

    # Parse interview fields from OCR text using regex
    details = _parse_interview_fields_regex(ocr_text)

    company = details.get("company") or "Unknown"
    role = details.get("role") or "Unknown"
    interview_date = details.get("interview_date")
    interview_time = details.get("interview_time")
    interviewer = details.get("interviewer_name")
    other = details.get("other_details")

    # Confirm extracted details to user
    summary_lines = [f"*Extracted from your invitation:*", f"Company: *{company}*", f"Role: *{role}*"]
    if interview_date:
        summary_lines.append(f"Date: {interview_date}" + (f" at {interview_time}" if interview_time else ""))
    if interviewer:
        summary_lines.append(f"Interviewer: {interviewer}")
    if other:
        summary_lines.append(f"Notes: {other}")
    await update.message.reply_text("\n".join(summary_lines), parse_mode="Markdown")

    # Log the application with interview date if found
    date_str = None
    if interview_date and interview_time:
        date_str = f"{interview_date} {interview_time}"
    elif interview_date:
        date_str = interview_date
    store.log_application(company, role, interview_date=date_str)

    # Run full brief pipeline
    await update.message.reply_text(
        f"Running full brief for *{company}* — *{role}*...",
        parse_mode="Markdown",
    )
    news = await loop.run_in_executor(None, get_company_news, company)

    data = store.get_all()
    interviews = data.get("interviews", [])
    weak_spots_context = "\n\nNO_INTERVIEW_HISTORY"
    if interviews:
        analysis = analyse_patterns()
        if analysis["weak_spots"]:
            weak_spots_context = "\n\nUser weak spots from interview history:\n" + "\n".join(
                f"- {w['category']}: {w['struggle_count']} struggles"
                for w in analysis["weak_spots"]
            )

    brief_prompt = (
        f"Generate a pre-interview brief for:\nCompany: {company}\nRole: {role}\n\n"
        f"COMPANY NEWS:\n{news}"
        f"{weak_spots_context}\n\n"
        f"Follow the BRIEF FORMAT exactly. Max 600 words. Use Telegram markdown."
    )

    history = store.get_conversation_history()
    brief_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": brief_prompt}]
    brief = await loop.run_in_executor(None, _call_agnes, brief_messages)
    store.append_conversation("user", brief_prompt)
    store.append_conversation("assistant", brief)

    await _safe_reply(update.message, brief)


async def handle_question_answer(update, context, user_id: int) -> bool:
    """Handle numeric reply to question list. Returns True if handled."""
    session = question_sessions.get(user_id)
    if not session:
        return False

    text = update.message.text.strip()
    if not re.match(r"^\d+$", text):
        return False

    idx = int(text) - 1
    questions = session["questions"]
    if idx < 0 or idx >= len(questions):
        await update.message.reply_text(
            f"Please reply with a number between 1 and {len(questions)}."
        )
        return True

    question = questions[idx]
    company = session["company"]
    role = session["role"]

    answer_prompt = (
        f"The user is preparing for a {role} interview at {company}. "
        f"Generate a strong, structured answer for this question:\n\n\"{question}\"\n\n"
        f"Format your response as:\n"
        f"*Q{idx+1}: {question}*\n\n"
        f"Here is a strong answer framework for a {company} {role} interview:\n\n"
        f"[Opening statement, key points, any {company}-specific angle if relevant, closing line]\n\n"
        f"Keep it under 200 words. Use Telegram markdown."
    )

    loop = asyncio.get_event_loop()
    answer = await loop.run_in_executor(
        None, _call_agnes, [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": answer_prompt}]
    )

    await _safe_reply(update.message, answer)
    await update.message.reply_text(
        "Reply with another number for a different question, or /brief [Company] [Role] to start fresh."
    )
    return True


async def handle_message(update, context):
    user_id = update.effective_user.id

    # Route to debrief flow if session active
    if user_id in debrief_sessions:
        handled = await handle_debrief_step(update, context)
        if handled:
            return

    # Route numeric replies to question answer flow
    if user_id in question_sessions:
        handled = await handle_question_answer(update, context, user_id)
        if handled:
            return

    user_text = update.message.text.strip()
    history = store.get_conversation_history()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": user_text}]

    loop = asyncio.get_event_loop()
    reply = await loop.run_in_executor(None, _call_agnes, messages)

    store.append_conversation("user", user_text)
    store.append_conversation("assistant", reply)

    await _safe_reply(update.message, reply)


async def send_reminder_brief(app, company: str, role: str, chat_id: int):
    """Generate and send a reminder brief for an upcoming interview."""
    loop = asyncio.get_event_loop()
    news = await loop.run_in_executor(None, get_company_news, company)

    prompt = (
        f"REMINDER: Interview within 24 hours!\n"
        f"Generate a pre-interview brief for:\nCompany: {company}\nRole: {role}\n\n"
        f"COMPANY NEWS:\n{news}\n\n"
        f"Follow the BRIEF FORMAT exactly. Max 600 words. Use Telegram markdown."
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    brief = await loop.run_in_executor(None, _call_agnes, messages)

    full_text = f"*Interview Reminder — {company} ({role})*\n\n{brief}"
    for chunk in _split_message(full_text):
        try:
            await app.bot.send_message(chat_id=chat_id, text=chunk, parse_mode="Markdown")
        except Exception:
            await app.bot.send_message(chat_id=chat_id, text=chunk)
