"""
data_processing/simple_preprocessing.py
----------------------------------------
Performs basic cleaning and standardization on exported CSV data.
Initial layer of the Data Processing & Structuring phase.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from colorama import Fore, init

init(autoreset=True)

# Directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"

# Constants
INTERNAL_DOMAIN = "thesmartbridge.com"


def find_latest_csv(user_email: str, prefix: str) -> Path | None:
    """Finds the most recent CSV for a user with a specific prefix (calendar or gmail)."""
    safe_email = user_email.replace("@", "_at_").replace(".", "_")
    pattern = f"{safe_email}_{prefix}_events_*.csv" if "calendar" in prefix else f"{safe_email}_{prefix}_messages_*.csv"
    
    files = sorted(DATA_DIR.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    return files[0] if files else None


def preprocess_calendar(user_email: str) -> Path | None:
    """Cleans calendar data: deduplication, holiday removal, date standardization."""
    csv_path = find_latest_csv(user_email, "calendar")
    if not csv_path:
        print(f"{Fore.RED}[PROC] No calendar CSV found for {user_email}")
        return None

    print(f"{Fore.CYAN}[PROC] Cleaning Calendar: {csv_path.name}")
    df = pd.read_csv(csv_path)

    # 1. Deduplication
    original_count = len(df)
    df = df.drop_duplicates(subset=['event_id', 'start_datetime'])
    
    # 2. Filter out Holiday calendars
    df = df[~df['calendar_name'].str.contains("Holidays", case=False, na=False)]
    df = df[~df['organizer'].str.contains("holiday@group.v.calendar", case=False, na=False)]

    # 3. Date Standardization
    df['start_datetime'] = pd.to_datetime(df['start_datetime'], format='ISO8601', utc=True, errors='coerce')
    df['end_datetime'] = pd.to_datetime(df['end_datetime'], format='ISO8601', utc=True, errors='coerce')

    # 4. Fill Duration if missing
    mask = df['duration_minutes'].isna() & df['start_datetime'].notna() & df['end_datetime'].notna()
    df.loc[mask, 'duration_minutes'] = (df['end_datetime'] - df['start_datetime']).dt.total_seconds() / 60

    # Save
    safe_email = user_email.replace("@", "_at_").replace(".", "_")
    out_path = DATA_DIR / f"{safe_email}_clean_calendar.csv"
    df.to_csv(out_path, index=False, encoding='utf-8-sig')
    
    print(f"{Fore.GREEN}[PROC] Calendar Cleaned -> {out_path.name}")
    removed_count = original_count - len(df)
    print(f"       Remaining Rows: {len(df)} (Removed {removed_count} rows)")
    return {
        "path": out_path,
        "remaining_rows": len(df),
        "removed_count": removed_count
    }


def preprocess_gmail(user_email: str) -> Path | None:
    """Cleans Gmail data: body merging, internal/external labeling."""
    csv_path = find_latest_csv(user_email, "gmail")
    if not csv_path:
        print(f"{Fore.RED}[PROC] No Gmail CSV found for {user_email}")
        return None

    print(f"{Fore.CYAN}[PROC] Cleaning Gmail: {csv_path.name}")
    df = pd.read_csv(csv_path)

    # 1. Body Cleaning
    # If body_preview is empty, use snippet
    df['clean_body'] = df['body_preview'].fillna(df['snippet']).fillna('')
    df['clean_body'] = df['clean_body'].str.replace(r'\r\n', '\n', regex=True)

    # 2. Internal vs External logic
    def is_internal(sender_field):
        if pd.isna(sender_field): return False
        return INTERNAL_DOMAIN.lower() in sender_field.lower()

    df['connection_type'] = df['from'].apply(lambda x: 'Internal' if is_internal(x) else 'External')

    # 3. Standardize dates
    df['received_datetime'] = pd.to_datetime(df['received_datetime'], format='ISO8601', utc=True, errors='coerce')

    # Save
    safe_email = user_email.replace("@", "_at_").replace(".", "_")
    out_path = DATA_DIR / f"{safe_email}_clean_gmail.csv"
    df.to_csv(out_path, index=False, encoding='utf-8-sig')

    print(f"{Fore.GREEN}[PROC] Gmail Cleaned -> {out_path.name}")
    print(f"       Remaining Rows: {len(df)}")
    return {
        "path": out_path,
        "remaining_rows": len(df)
    }


def run_simple_preprocessing(user_email: str) -> dict:
    """Runs the simple preprocessing suite."""
    print(f"\n{Fore.MAGENTA}{'='*55}")
    print(f"{Fore.MAGENTA}  [PROC] RUNNING SIMPLE PREPROCESSING")
    print(f"{Fore.MAGENTA}  Account: {user_email}")
    print(f"{Fore.MAGENTA}{'='*55}\n")

    cal_res = preprocess_calendar(user_email)
    print()
    gmail_res = preprocess_gmail(user_email)

    print(f"\n{Fore.GREEN}{'='*55}")
    print(f"{Fore.GREEN}  [DONE] PREPROCESSING COMPLETE")
    print(f"{Fore.GREEN}{'='*55}\n")

    return {
        "calendar_path": str(cal_res["path"]) if cal_res else None,
        "calendar_removed_count": cal_res["removed_count"] if cal_res else 0,
        "gmail_path": str(gmail_res["path"]) if gmail_res else None,
        "gmail_remaining_rows": gmail_res["remaining_rows"] if gmail_res else 0
    }
