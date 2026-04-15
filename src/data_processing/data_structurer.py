"""
data_processing/data_structurer.py
----------------------------------
Converts filtered Calendar and Gmail data into a single, unified activity format.
This is the final step in the Data Processing & Structuring layer.
"""

import pandas as pd
from pathlib import Path
from colorama import Fore, init

init(autoreset=True)

# Directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"


def map_calendar_to_common(df: pd.DataFrame) -> pd.DataFrame:
    """Maps calendar columns to the common activity schema."""
    if df.empty: return pd.DataFrame()
    
    mapping = {
        'start_datetime': 'timestamp',
        'title': 'title',
        'description': 'description',
        'attendees': 'participants',
        'duration_minutes': 'duration'
    }
    
    # Select and rename columns
    unified_df = df.rename(columns=mapping)[list(mapping.values())].copy()
    
    # Set static fields
    unified_df['source'] = 'Calendar'
    unified_df['activity_type'] = 'Meeting'
    unified_df['connection_type'] = 'N/A' # To be refined or pulled from admin/holiday filters
    
    return unified_df


def map_gmail_to_common(df: pd.DataFrame) -> pd.DataFrame:
    """Maps Gmail columns to the common activity schema."""
    if df.empty: return pd.DataFrame()

    mapping = {
        'received_datetime': 'timestamp',
        'subject': 'title',
        'clean_body': 'description',
        'from': 'participants', # Simplification: use sender as primary participant
        'connection_type': 'connection_type'
    }

    # Select and rename
    unified_df = df.rename(columns=mapping)[list(mapping.values())].copy()

    # Set static fields
    unified_df['source'] = 'Gmail'
    unified_df['activity_type'] = df['is_sent'].apply(lambda s: 'Sent Email' if s else 'Received Email')
    unified_df['duration'] = 0 # Emails have zero duration in this simple model

    return unified_df


def run_data_structuring(user_email: str) -> Path | None:
    """Runs the unified structuring process."""
    print(f"\n{Fore.MAGENTA}{'='*55}")
    print(f"{Fore.MAGENTA}  [STRUCT] STRUCTURING UNIFIED ACTIVITY LOG")
    print(f"{Fore.MAGENTA}  Account: {user_email}")
    print(f"{Fore.MAGENTA}{'='*55}\n")

    safe_email = user_email.replace("@", "_at_").replace(".", "_")
    cal_path = DATA_DIR / f"{safe_email}_filtered_calendar.csv"
    gmail_path = DATA_DIR / f"{safe_email}_filtered_gmail.csv"

    # Load data
    try:
        cal_df = pd.read_csv(cal_path) if cal_path.exists() else pd.DataFrame()
        gmail_df = pd.read_csv(gmail_path) if gmail_path.exists() else pd.DataFrame()
    except Exception as e:
        print(f"{Fore.RED}[STRUCT] Error loading data: {e}")
        return None

    print(f"{Fore.CYAN}[STRUCT] Mapping components...")
    unified_cal = map_calendar_to_common(cal_df)
    unified_gmail = map_gmail_to_common(gmail_df)

    # Merge and Sort
    print(f"{Fore.CYAN}[STRUCT] Merging activities...")
    unified_df = pd.concat([unified_cal, unified_gmail], ignore_index=True)
    
    if unified_df.empty:
        print(f"{Fore.YELLOW}[STRUCT] No data found to merge.")
        return None

    # Ensure timestamp is datetime and sort
    unified_df['timestamp'] = pd.to_datetime(unified_df['timestamp'], format='ISO8601', utc=True)
    unified_df = unified_df.sort_values('timestamp')

    # Save
    out_path = DATA_DIR / f"{safe_email}_unified_activity_log.csv"
    unified_df.to_csv(out_path, index=False, encoding='utf-8-sig')

    print(f"{Fore.GREEN}[STRUCT] Unified Log Created -> {out_path.name}")
    print(f"         Total Combined Activities: {len(unified_df)}")
    
    print(f"\n{Fore.GREEN}{'='*55}")
    print(f"{Fore.GREEN}  [DONE] DATA STRUCTURING COMPLETE")
    print(f"{Fore.GREEN}{'='*55}\n")
    
    return out_path
