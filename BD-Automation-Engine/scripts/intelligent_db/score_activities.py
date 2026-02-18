"""
Score activities by sentiment and hiring signals.
Keyword-based analysis of note_text from 30K+ activity records.
"""
import re
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "data" / "unified_federal_contracts.db"

POSITIVE_KEYWORDS = [
    r"\binterested\b", r"\bengaged\b", r"\bexcited\b", r"\bgreat\s+(?:call|meeting|conversation)\b",
    r"\bfollow\s*up\b", r"\bscheduled?\b", r"\bapproved\b", r"\bgreen\s*light\b",
    r"\bwants?\s+to\s+(?:meet|discuss|talk)\b", r"\bpositive\b", r"\bstrong\s+(?:fit|match|interest)\b",
    r"\breceptive\b", r"\bbudget\s+(?:approved|available|allocated)\b",
    r"\baction\s+items?\b", r"\bnext\s+steps?\b", r"\bpartnering?\b",
]

NEGATIVE_KEYWORDS = [
    r"\bnot\s+interested\b", r"\bno\s+(?:budget|funding|need|response)\b",
    r"\bdeclined?\b", r"\brejected?\b", r"\bcancelled?\b", r"\bpassed?\b",
    r"\bincumbent\s+(?:strong|locked|preferred)\b", r"\bno\s+(?:answer|response)\b",
    r"\bvoicemail\b", r"\bleft\s+(?:message|vm)\b", r"\bunresponsive\b",
    r"\bprotested?\b", r"\bdelayed?\b", r"\bslipped?\b", r"\bfrozen?\b",
]

HIRING_KEYWORDS = [
    r"\bhiring\b", r"\bopen\s+req(?:uisition)?s?\b", r"\bbackfill\b",
    r"\bheadcount\b", r"\bramp(?:ing)?\s+up\b", r"\bnew\s+(?:positions?|hires?|openings?)\b",
    r"\bstaffing\b", r"\brecruiting\b", r"\bonboarding\b",
    r"\b\d+\s+(?:positions?|openings?|slots?|reqs?)\b", r"\bgrow(?:th|ing)\b",
    r"\bexpanding\b", r"\baugment(?:ation|ing)?\b",
]


def ensure_columns(conn):
    """Add sentiment/hiring columns if they don't exist."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(activities)")
    cols = {row[1] for row in cursor.fetchall()}

    if "sentiment_score" not in cols:
        cursor.execute("ALTER TABLE activities ADD COLUMN sentiment_score REAL")
    if "has_hiring_signal" not in cols:
        cursor.execute("ALTER TABLE activities ADD COLUMN has_hiring_signal INTEGER DEFAULT 0")
    if "priority" not in cols:
        cursor.execute("ALTER TABLE activities ADD COLUMN priority TEXT")
    conn.commit()


def score_text(text):
    """Score text for sentiment (-1 to 1) and hiring signals."""
    if not text:
        return 0.0, False

    pos_count = sum(1 for p in POSITIVE_KEYWORDS if re.search(p, text, re.IGNORECASE))
    neg_count = sum(1 for p in NEGATIVE_KEYWORDS if re.search(p, text, re.IGNORECASE))
    hiring = any(re.search(p, text, re.IGNORECASE) for p in HIRING_KEYWORDS)

    total = pos_count + neg_count
    if total == 0:
        sentiment = 0.0
    else:
        sentiment = round((pos_count - neg_count) / total, 2)

    return sentiment, hiring


def run(db_path=None):
    """Run activity scoring."""
    db_path = db_path or DB_PATH
    print("Activity Scoring")
    print(f"  Database: {db_path}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    ensure_columns(conn)

    cursor.execute("SELECT id, note_text, comments, action, about FROM activities")
    activities = cursor.fetchall()

    scored = 0
    hiring_count = 0

    for aid, note_text, comments, action, about in activities:
        text = " ".join(filter(None, [note_text, comments, action, about]))
        if not text.strip():
            continue

        sentiment, has_hiring = score_text(text)

        if sentiment > 0.3:
            priority = "high"
        elif sentiment > 0:
            priority = "medium"
        elif sentiment < -0.3:
            priority = "low"
        else:
            priority = "neutral"

        # Hiring signals boost priority
        if has_hiring and priority != "high":
            priority = "high"

        cursor.execute("""
            UPDATE activities
            SET sentiment_score = ?, has_hiring_signal = ?, priority = ?
            WHERE id = ?
        """, (sentiment, 1 if has_hiring else 0, priority, aid))

        scored += 1
        if has_hiring:
            hiring_count += 1

    conn.commit()
    conn.close()

    print(f"  Scored: {scored}/{len(activities)} activities")
    print(f"  Hiring signals detected: {hiring_count}")


if __name__ == "__main__":
    run()
