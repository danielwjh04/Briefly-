import json
import os
from datetime import datetime, timezone

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

_DEFAULT = {
    "profile": {},
    "interviews": [],
    "applications": [],
    "conversation_history": [],
}

MAX_CONVERSATION_TURNS = 20


def _load() -> dict:
    if not os.path.exists(DATA_FILE):
        _save(_DEFAULT.copy())
        return _DEFAULT.copy()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_all() -> dict:
    return _load()


def update_profile(data: dict) -> None:
    store = _load()
    store["profile"].update(data)
    _save(store)


def log_interview(company: str, role: str, notes: dict) -> None:
    store = _load()
    entry = {
        "company": company,
        "role": role,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **notes,
    }
    store["interviews"].append(entry)
    _save(store)


def log_application(company: str, role: str, interview_date: str = None) -> None:
    store = _load()
    entry = {
        "company": company,
        "role": role,
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "interview_date": interview_date,
    }
    store["applications"].append(entry)
    _save(store)


def get_upcoming_interviews() -> list:
    store = _load()
    now = datetime.now(timezone.utc)
    upcoming = []
    for app in store.get("applications", []):
        interview_date = app.get("interview_date")
        if not interview_date:
            continue
        try:
            dt = datetime.fromisoformat(interview_date)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            diff = (dt - now).total_seconds()
            if 0 <= diff <= 86400:
                upcoming.append(app)
        except (ValueError, TypeError):
            continue
    return upcoming


def get_conversation_history() -> list:
    store = _load()
    return store.get("conversation_history", [])


def append_conversation(role: str, content: str) -> None:
    store = _load()
    history = store.get("conversation_history", [])
    history.append({"role": role, "content": content})
    # Keep last MAX_CONVERSATION_TURNS turns (each turn = user + assistant = 2 entries)
    if len(history) > MAX_CONVERSATION_TURNS * 2:
        history = history[-(MAX_CONVERSATION_TURNS * 2):]
    store["conversation_history"] = history
    _save(store)


def clear_conversation() -> None:
    store = _load()
    store["conversation_history"] = []
    _save(store)
