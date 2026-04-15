"""
data_integration/csv_exporter.py
----------------------------------
Converts raw JSON extractions into clean CSV files.
Saves to data/processed/

Output files:
    - calendar_events.csv   : One row per calendar event
    - gmail_messages.csv    : One row per email message
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from colorama import Fore, init

init(autoreset=True)

# Directories
BASE_DIR    = Path(__file__).resolve().parent.parent.parent
RAW_DIR     = BASE_DIR / "data" / "raw"
OUTPUT_DIR  = BASE_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

def find_latest_file(folder: Path, pattern: str) -> Path | None:
    """Returns the most recently created file matching a glob pattern."""
    files = sorted(folder.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    return files[0] if files else None


def load_json(path: Path) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────────────────────────────────────
# Calendar CSV Export
# ──────────────────────────────────────────────────────────

def export_calendar_csv(user_email: str) -> Path | None:
    """
    Reads the latest calendar_events JSON for the user and exports a flat CSV.
    Nested fields (attendees, recurrence, conference_data) are simplified.
    """
    safe_email = user_email.replace("@", "_at_").replace(".", "_")
    json_file = find_latest_file(RAW_DIR / "calendar", f"{safe_email}_calendar_events_*.json")
    if not json_file:
        print(f"{Fore.RED}[CSV] No calendar JSON found for {user_email} in data/raw/calendar/")
        return None

    print(f"{Fore.CYAN}[CSV] Reading: {json_file.name}")
    events = load_json(json_file)

    if not events:
        print(f"{Fore.YELLOW}[CSV] No calendar events to export.")
        return None

    rows = []
    for e in events:
        # Calculate duration in minutes
        duration_mins = None
        try:
            if e.get("start_datetime") and e.get("end_datetime") and "T" in e["start_datetime"]:
                start = datetime.fromisoformat(e["start_datetime"].replace("Z", "+00:00"))
                end   = datetime.fromisoformat(e["end_datetime"].replace("Z", "+00:00"))
                duration_mins = int((end - start).total_seconds() / 60)
        except Exception:
            pass

        # Flatten attendees to a comma-separated email list
        attendee_emails = ", ".join(
            a.get("email", "") for a in e.get("attendees", []) if a.get("email")
        )

        rows.append({
            "event_id"          : e.get("id", ""),
            "title"             : e.get("title", ""),
            "calendar_name"     : e.get("calendar_name", ""),
            "start_datetime"    : e.get("start_datetime", ""),
            "end_datetime"      : e.get("end_datetime", ""),
            "duration_minutes"  : duration_mins,
            "is_all_day"        : e.get("is_all_day", False),
            "is_recurring"      : e.get("is_recurring", False),
            "is_online_meeting" : e.get("is_online_meeting", False),
            "status"            : e.get("status", ""),
            "organizer"         : e.get("organizer", ""),
            "creator"           : e.get("creator", ""),
            "attendee_count"    : e.get("attendee_count", 0),
            "attendees"         : attendee_emails,
            "location"          : e.get("location", ""),
            "description"       : (e.get("description") or "")[:500],  # cap at 500 chars
            "created"           : e.get("created", ""),
            "updated"           : e.get("updated", ""),
        })

    df = pd.DataFrame(rows)

    # Sort by start_datetime
    df["start_datetime"] = pd.to_datetime(df["start_datetime"], format='ISO8601', utc=True, errors="coerce")
    df = df.sort_values("start_datetime")
    df["start_datetime"] = df["start_datetime"].astype(str)

    # Create unique filename with timestamp and email
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"{safe_email}_calendar_events_{timestamp}.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")  # utf-8-sig for Excel compatibility

    print(f"{Fore.GREEN}[CSV] Calendar CSV saved  -> {out_path}")
    print(f"{Fore.GREEN}       Rows: {len(df)} events | Columns: {len(df.columns)}")
    return out_path


# ──────────────────────────────────────────────────────────
# Gmail CSV Export
# ──────────────────────────────────────────────────────────

def export_gmail_csv(user_email: str) -> Path | None:
    """
    Reads the latest gmail_messages JSON for the user and exports a flat CSV.
    """
    safe_email = user_email.replace("@", "_at_").replace(".", "_")
    json_file = find_latest_file(RAW_DIR / "gmail", f"{safe_email}_gmail_messages_*.json")
    if not json_file:
        print(f"{Fore.RED}[CSV] No Gmail JSON found for {user_email} in data/raw/gmail/")
        return None

    print(f"{Fore.CYAN}[CSV] Reading: {json_file.name}")
    messages = load_json(json_file)

    if not messages:
        print(f"{Fore.YELLOW}[CSV] No emails to export.")
        return None

    rows = []
    for m in messages:
        rows.append({
            "message_id"       : m.get("id", ""),
            "thread_id"        : m.get("thread_id", ""),
            "subject"          : m.get("subject", ""),
            "from"             : m.get("from", ""),
            "to"               : m.get("to", ""),
            "cc"               : m.get("cc", ""),
            "received_datetime": m.get("received_datetime", ""),
            "is_sent"          : m.get("is_sent", False),
            "is_inbox"         : m.get("is_inbox", False),
            "is_unread"        : m.get("is_unread", False),
            "is_starred"       : m.get("is_starred", False),
            "is_important"     : m.get("is_important", False),
            "labels"           : ", ".join(m.get("labels", [])),
            "snippet"          : m.get("snippet", ""),
            "body_preview"     : (m.get("body_preview") or "")[:500],
            "size_estimate"    : m.get("size_estimate", 0),
            "mime_type"        : m.get("mime_type", ""),
        })

    df = pd.DataFrame(rows)

    # Sort by received_datetime
    df["received_datetime"] = pd.to_datetime(df["received_datetime"], format='ISO8601', utc=True, errors="coerce")
    df = df.sort_values("received_datetime")
    df["received_datetime"] = df["received_datetime"].astype(str)

    # Create unique filename with timestamp and email
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"{safe_email}_gmail_messages_{timestamp}.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"{Fore.GREEN}[CSV] Gmail CSV saved     -> {out_path}")
    print(f"{Fore.GREEN}       Rows: {len(df)} emails | Columns: {len(df.columns)}")
    return out_path


# ──────────────────────────────────────────────────────────
# Main export runner
# ──────────────────────────────────────────────────────────

def run_csv_export(user_email: str) -> dict:
    """
    Runs both calendar and Gmail CSV exports for a specific user.
    Returns paths of generated files.
    """
    print(f"\n{Fore.MAGENTA}{'='*55}")
    print(f"{Fore.MAGENTA}  [CSV] EXPORTING DATA TO CSV FORMAT")
    print(f"{Fore.MAGENTA}  Account: {user_email}")
    print(f"{Fore.MAGENTA}{'='*55}\n")

    cal_path   = export_calendar_csv(user_email)
    print()
    gmail_path = export_gmail_csv(user_email)

    print(f"\n{Fore.GREEN}{'='*55}")
    print(f"{Fore.GREEN}  [DONE] CSV EXPORT COMPLETE")
    print(f"{Fore.GREEN}{'='*55}")
    print(f"  Output folder: {Fore.WHITE}{OUTPUT_DIR}")
    print(f"{Fore.GREEN}{'='*55}\n")

    return {
        "calendar_csv": str(cal_path) if cal_path else None,
        "gmail_csv"   : str(gmail_path) if gmail_path else None,
    }
