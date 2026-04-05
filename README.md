# Briefly — Internship Intelligence Bot

A personal Telegram bot for NUS Singapore students hunting for internships and full-time roles. Send commands to get pre-interview briefings, scan live job listings, track your interview patterns, and generate cover letters — all from Telegram.

---

## What it does

| Command | What it does |
|---|---|
| `/brief [Company] [Role]` | Pre-interview brief: company snapshot, likely questions with suggested answers, and quick prep tips |
| `/debrief` | Step-by-step post-interview logging (saved to memory) |
| `/patterns` | Analyse your logged interviews — ranked weak spots, win rate, and a targeted drill |
| `/jobs [keyword]` | Live job listings from MyCareersFuture (Singapore's official job portal) |
| `/cover [Company] [Role]` | Generate a cover letter tailored to the role |
| `/profile [key=value ...]` | View or update your profile (name, degree, skills, GPA, year) |
| `/clear` | Clear conversation history |

**Photo upload:** Send a screenshot of an interview invitation and the bot will extract the company, role, date, and interviewer — then automatically run a full brief and generate likely interview questions.

---

## Step-by-step setup

### Step 1 — Install Python

If you don't have Python installed:

1. Go to https://www.python.org/downloads/
2. Download Python **3.10 or newer**
3. Run the installer — **tick "Add Python to PATH"** before clicking Install

To verify it worked, open a terminal and run:
```
python --version
```
You should see something like `Python 3.11.x`.

---

### Step 2 — Download this project

Option A — with Git:
```bash
git clone https://github.com/danielwjh04/Briefly-.git
cd Briefly-
```

Option B — without Git:
1. Click the green **Code** button on this GitHub page
2. Click **Download ZIP**
3. Unzip the folder, then open a terminal inside it

---

### Step 3 — Install dependencies

In your terminal (inside the project folder), run:
```bash
pip install -r requirements.txt
```

---

### Step 4 — Create your Telegram bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Follow the prompts — give your bot a name and username
4. BotFather will send you a **bot token** that looks like: `123456789:ABCdef...`
5. Copy and save this token

---

### Step 5 — Get your Telegram chat ID

1. Open Telegram and search for **@userinfobot**
2. Send it `/start`
3. It will reply with your **Id** (a number like `987654321`)
4. Copy and save this number

---

### Step 6 — Get a Zenmux API key

1. Go to https://zenmux.ai and create a free account
2. Navigate to your API keys section
3. Create a new key and copy it

---

### Step 7 — Create your `.env` file

In the project folder, create a file called `.env` (exactly that name, with the dot).

Open it in any text editor (Notepad is fine) and paste this in — replacing the placeholder values with your real ones:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
ZENMUX_API_KEY=your_zenmux_api_key_here
```

Example:
```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_CHAT_ID=987654321
ZENMUX_API_KEY=zx-abc123...
```

Save the file.

---

### Step 8 — Run the bot

```bash
python main.py
```

You should see a message confirming the bot has started. Now open Telegram, find your bot by its username, and send `/start`.

---

## Keeping the bot running

The bot only runs while your terminal is open. If you close it, the bot stops.

To keep it running in the background on your computer, you can use a tool like [pm2](https://pm2.keymetrics.io/) or simply leave the terminal open.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `python: command not found` | Use `python3` instead of `python`, or reinstall Python with PATH ticked |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| Bot does not respond | Double-check your `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env` |
| `Invalid API key` | Check your `ZENMUX_API_KEY` in `.env` |

---

## Project structure (for the curious)

```
Briefly-/
├── main.py                  # Entry point — bot setup and scheduler
├── config.py                # AI client config and system prompt
├── bot/
│   └── telegram_handler.py  # All command and message handlers
├── memory/
│   ├── store.py             # Local memory (profile, interviews, history)
│   └── pattern_tracker.py   # Interview pattern analysis
├── tools/
│   ├── company_research.py  # Company news scraping
│   ├── interview_intel.py   # Interview question intelligence
│   ├── job_scanner.py       # MyCareersFuture API integration
│   └── cover_letter.py      # Cover letter generation
└── skills/                  # Documentation for each tool
```

All data is saved locally in `memory/data.json` — no external database needed.
