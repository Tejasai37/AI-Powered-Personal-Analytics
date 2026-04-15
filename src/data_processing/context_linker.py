"""
data_processing/context_linker.py
---------------------------------
Connects related emails and calendar events based on time proximity 
and keyword similarity. Final step in the Data Structuring layer.
"""

import pandas as pd
from pathlib import Path
from datetime import timedelta
from colorama import Fore, init
import re

init(autoreset=True)

# Directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"

# Constants
LINK_WINDOW_MINUTES = 60


def get_keywords(text: str) -> set:
    """Extracts significant keywords from text for matching."""
    if not isinstance(text, str): return set()
    # Clean and split, remove small common words
    words = re.findall(r'\b\w{4,}\b', text.lower()) 
    stop_words = {'meeting', 'sync', 'call', 'daily', 'weekly', 'huddle', 'update', 'round'}
    return set(words) - stop_words


def run_contextual_linking(user_email: str) -> Path | None:
    """Identifies and links related activities."""
    print(f"\n{Fore.MAGENTA}{'='*55}")
    print(f"{Fore.MAGENTA}  [LINK] CONNECTING RELATED WORK")
    print(f"{Fore.MAGENTA}  Account: {user_email}")
    print(f"{Fore.MAGENTA}{'='*55}\n")

    safe_email = user_email.replace("@", "_at_").replace(".", "_")
    csv_path = DATA_DIR / f"{safe_email}_categorized_activity_log.csv"

    if not csv_path.exists():
        print(f"{Fore.RED}[LINK] No categorized log found for {user_email}")
        return None

    df = pd.read_csv(csv_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    
    # Clean up any missing timestamps
    original_len = len(df)
    df = df.dropna(subset=['timestamp'])
    if len(df) < original_len:
        print(f"{Fore.YELLOW}[LINK] Dropped {original_len - len(df)} activities with missing timestamps.")

    # Initialize link column
    df['linked_context_id'] = ""
    link_count = 0

    print(f"{Fore.CYAN}[LINK] Scanning for connections...")

    # Separate meetings and emails for faster processing
    meetings = df[df['activity_type'] == 'Meeting'].copy()
    emails = df[df['activity_type'].str.contains('Email')].copy()

    for idx, meeting in meetings.iterrows():
        m_time = meeting['timestamp']
        m_keywords = get_keywords(meeting['title'])
        m_id = f"CTX_{idx}_{meeting['timestamp'].strftime('%m%d')}"

        # Find emails in window
        window_start = m_time - timedelta(minutes=LINK_WINDOW_MINUTES)
        window_end = m_time + timedelta(minutes=LINK_WINDOW_MINUTES)
        
        related_emails = emails[
            (emails['timestamp'] >= window_start) & 
            (emails['timestamp'] <= window_end)
        ]

        # Check for keyword overlap
        for e_idx, email in related_emails.iterrows():
            e_keywords = get_keywords(email['title'])
            if m_keywords & e_keywords: # Intersection exists
                # Create a link
                df.at[idx, 'linked_context_id'] = m_id
                df.at[e_idx, 'linked_context_id'] = m_id
                link_count += 1

    # Save
    out_path = DATA_DIR / f"{safe_email}_final_structured_data.csv"
    df.to_csv(out_path, index=False, encoding='utf-8-sig')

    print(f"{Fore.GREEN}[LINK] Contextual Linking Complete -> {out_path.name}")
    print(f"       Found {link_count} connections between emails and meetings.")

    print(f"\n{Fore.GREEN}{'='*55}")
    print(f"{Fore.GREEN}  [DONE] ALL STRUCTURING STEPS COMPLETE")
    print(f"{Fore.GREEN}{'='*55}\n")

    return {
        "path": str(out_path),
        "link_count": link_count
    }
