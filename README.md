# InternBrief

A personal Telegram bot for NUS Singapore students hunting for internships and full-time roles. InternBrief runs intelligence tools before and after interviews — generating structured briefings, tracking interview patterns, scanning live job listings, and drafting cover letters.

---

## Features

| Command | What it does |
|---|---|
| `/brief [Company] [Role]` | Pre-interview brief: company snapshot, role-specific topics, likely questions with suggested answers, and quick prep |
| `/debrief` | Step-by-step post-interview logging (5 questions, saved to memory) |
| `/patterns` | Analyse your logged interviews — ranked weak spots, win rate, and a targeted drill |
| `/jobs [keyword]` | Live job listings from MyCareersFuture (Singapore's official job portal) |
| `/cover [Company] [Role]` | 3-paragraph cover letter starting from a specific accomplishment |
| `/profile [key=value ...]` | View or update your profile (name, degree, skills, GPA, year) |
| `/clear` | Clear conversation history |

**Photo upload:** Send a screenshot of an interview invitation and the bot will OCR it, extract company/role/date/interviewer, log the application, run a full brief, and generate likely interview questions you can drill through.

**Scheduled jobs:**
- Hourly check: sends a reminder brief for any interview within the next 24 hours
- Every Monday at 8am SGT: sends your weekly pattern report

---

## Setup

### Prerequisites

- Python 3.10+
- A Telegram bot token (create one via [@BotFather](https://t.me/BotFather))
- A [Zenmux](https://zenmux.ai) API key (used to call the Agnes 1.5 Pro model)
- Your Telegram chat ID (get it from [@userinfobot](https://t.me/userinfobot))

### Installation

```bash
git clone <repo-url>
cd intern-brief
pip install -r requirements.txt
```

### Environment variables

Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_numeric_chat_id
ZENMUX_API_KEY=your_zenmux_api_key
```

### Run

```bash
python main.py
```

---

## Project Structure

```
intern-brief/
├── main.py                  # Entry point — bot setup, scheduler, handlers
├── config.py                # OpenAI-compatible client (Zenmux/Agnes), system prompt
├── bot/
│   └── telegram_handler.py  # All command and message handlers
├── memory/
│   ├── store.py             # JSON-backed memory (profile, interviews, conversation history)
│   └── pattern_tracker.py   # Interview pattern analysis
├── tools/
│   ├── company_research.py  # Web scraping for company news
│   ├── interview_intel.py   # Interview question intelligence
│   ├── job_scanner.py       # MyCareersFuture API integration
│   └── cover_letter.py      # Cover letter generation
└── skills/                  # SKILL.md docs for each tool
```

---

## Memory

All data is persisted locally in `memory/data.json` — no external database required. This includes:
- Your profile (name, degree, skills, GPA, year)
- Logged applications and interviews
- Conversation history (rolling context window)

---

## Model

InternBrief uses **Agnes 1.5 Pro** via the Zenmux API, accessed through an OpenAI-compatible client. The system prompt enforces strict output rules: no fabricated company data, Telegram markdown formatting, and structured brief formats for every command.
