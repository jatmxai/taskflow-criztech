"""Smart parser for natural-language task input.

Examples:
    "Buy milk tomorrow !high"        -> title="Buy milk", due=tomorrow, priority="high"
    "Ship feature friday !!"         -> title="Ship feature", due=next Friday, priority="high"
    "Review PR by 12/25 !low"        -> title="Review PR", due=Dec 25, priority="low"
    "Meeting today"                  -> title="Meeting", due=today
"""

import re
from datetime import date, timedelta

PRIORITY_MAP = {
    "high": "high", "h": "high", "!!": "high", "!!!": "high",
    "medium": "medium", "med": "medium", "m": "medium",
    "low": "low", "l": "low",
}

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def parse_task_input(text: str):
    """Returns (clean_title, priority, due_date)."""
    priority = "medium"
    due_date = None
    today = date.today()

    # Priority shorthand
    m = re.search(r"\s!(high|med|medium|low|h|m|l)\b", text, re.IGNORECASE)
    if m:
        priority = PRIORITY_MAP[m.group(1).lower()]
        text = (text[:m.start()] + text[m.end():]).strip()
    else:
        m = re.search(r"\s(!!!|!!)(?:\s|$)", text)
        if m:
            priority = "high"
            text = (text[:m.start()] + text[m.end():]).strip()

    # Date keywords (longest first to avoid partial matches)
    matched = False
    keyword_dates = [
        (r"\bday after tomorrow\b", 2),
        (r"\btomorrow\b", 1),
        (r"\btoday\b", 0),
        (r"\btonight\b", 0),
        (r"\bnext week\b", 7),
    ]
    for pat, offset in keyword_dates:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            due_date = today + timedelta(days=offset)
            text = (text[:m.start()] + text[m.end():]).strip()
            matched = True
            break
    if not matched:
        m = re.search(r"\bin (\d+) days?\b", text, re.IGNORECASE)
        if m:
            due_date = today + timedelta(days=int(m.group(1)))
            text = (text[:m.start()] + text[m.end():]).strip()
            matched = True

    # Weekdays (next occurrence)
    if not matched:
        for i, name in enumerate(WEEKDAYS):
            m = re.search(rf"\b{name}\b", text, re.IGNORECASE)
            if m:
                days_ahead = (i - today.weekday()) % 7 or 7
                due_date = today + timedelta(days=days_ahead)
                text = (text[:m.start()] + text[m.end():]).strip()
                matched = True
                break

    # Numeric dates: YYYY-MM-DD or MM/DD or M/D
    if not matched:
        m = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", text)
        if m:
            try:
                due_date = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                text = (text[:m.start()] + text[m.end():]).strip()
                matched = True
            except ValueError:
                pass
    if not matched:
        m = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", text)
        if m:
            try:
                month = int(m.group(1))
                day = int(m.group(2))
                year = today.year
                if m.group(3):
                    y = int(m.group(3))
                    year = y if y > 99 else 2000 + y
                due_date = date(year, month, day)
                if due_date < today and not m.group(3):
                    due_date = date(year + 1, month, day)
                text = (text[:m.start()] + text[m.end():]).strip()
            except ValueError:
                pass

    # Strip prefix tokens like "by", "on", "due", "@" left dangling
    text = re.sub(r"\b(by|on|due|at)\s*$", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s+", " ", text).strip()

    return text, priority, due_date
