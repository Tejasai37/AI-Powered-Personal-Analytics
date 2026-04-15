"""
data_processing/noise_filter.py
-------------------------------
Identifies and filters out "noise" (bots, newsletters, system notifications) 
from the cleaned datasets. Creates high-signal filtered files for AI analysis.
"""

import pandas as pd
from pathlib import Path
from colorama import Fore, init

init(autoreset=True)

# Directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"

# Noise Patterns
BOT_KEYWORDS = [
    "noreply", "no-reply", "fireflies.ai", "tldv.io", 
    "zohopeople", "zohomeeting", "zohowebinar", "Skill Wallet"
]
NEWSLETTER_KEYWORDS = ["Newsletter", "Digest", "Weekly Update", "Daily Briefing", "YS Buzz"]
CALENDAR_NOISE_TITLES = ["Out of office", "Working from", "Holiday", "OOO", "Vacation"]


def filter_calendar_noise(user_email: str) -> Path | None:
    """Flags and filters calendar noise."""
    safe_email = user_email.replace("@", "_at_").replace(".", "_")
    csv_path = DATA_DIR / f"{safe_email}_clean_calendar.csv"
    
    if not csv_path.exists():
        print(f"{Fore.RED}[FILTER] No clean calendar CSV found for {user_email}")
        return None

    print(f"{Fore.CYAN}[FILTER] Filtering Calendar Noise: {csv_path.name}")
    df = pd.read_csv(csv_path)

    def is_calendar_noise(row):
        title = str(row['title']).lower()
        if row['status'] == 'cancelled': return True
        if any(noise.lower() in title for noise in CALENDAR_NOISE_TITLES): return True
        return False

    df['is_noise'] = df.apply(is_calendar_noise, axis=1)
    
    # Save the full tagged version and a filtered version
    out_path = DATA_DIR / f"{safe_email}_filtered_calendar.csv"
    df[df['is_noise'] == False].to_csv(out_path, index=False, encoding='utf-8-sig')

    print(f"{Fore.GREEN}[FILTER] Calendar Filtered -> {out_path.name}")
    signal_count = len(df[df['is_noise'] == False])
    noise_count = len(df[df['is_noise'] == True])
    print(f"         Signal: {signal_count} rows | Noise: {noise_count} rows")
    return {
        "path": out_path,
        "signal_count": signal_count,
        "noise_count": noise_count
    }


def filter_gmail_noise(user_email: str) -> Path | None:
    """Flags and filters Gmail noise (bots, newsletters, system updates)."""
    safe_email = user_email.replace("@", "_at_").replace(".", "_")
    csv_path = DATA_DIR / f"{safe_email}_clean_gmail.csv"

    if not csv_path.exists():
        print(f"{Fore.RED}[FILTER] No clean gmail CSV found for {user_email}")
        return None

    print(f"{Fore.CYAN}[FILTER] Filtering Gmail Noise: {csv_path.name}")
    df = pd.read_csv(csv_path)

    def is_gmail_noise(row):
        sender = str(row['from']).lower()
        subject = str(row['subject']).lower()
        labels = str(row['labels']).upper()
        
        # 1. Bot check
        if any(bot.lower() in sender for bot in BOT_KEYWORDS): return True
        
        # 2. Newsletter check
        if any(ns.lower() in subject for ns in NEWSLETTER_KEYWORDS): return True
        
        # 3. Automatic Updates check (unless marked as SENT by user)
        if not row['is_sent']:
            if "CATEGORY_UPDATES" in labels or "CATEGORY_PROMOTIONS" in labels:
                return True
        
        return False

    df['is_noise'] = df.apply(is_gmail_noise, axis=1)

    # Save filtered version
    out_path = DATA_DIR / f"{safe_email}_filtered_gmail.csv"
    df[df['is_noise'] == False].to_csv(out_path, index=False, encoding='utf-8-sig')

    print(f"{Fore.GREEN}[FILTER] Gmail Filtered -> {out_path.name}")
    signal_count = len(df[df['is_noise'] == False])
    noise_count = len(df[df['is_noise'] == True])
    print(f"         Signal: {signal_count} rows | Noise: {noise_count} rows")
    return {
        "path": out_path,
        "signal_count": signal_count,
        "noise_count": noise_count
    }


def run_noise_filtering(user_email: str) -> dict:
    """Runs the noise filtering suite."""
    print(f"\n{Fore.MAGENTA}{'='*55}")
    print(f"{Fore.MAGENTA}  [FILTER] NOISE REDUCTION ENGINE")
    print(f"{Fore.MAGENTA}  Account: {user_email}")
    print(f"{Fore.MAGENTA}{'='*55}\n")

    cal_res = filter_calendar_noise(user_email)
    print()
    gmail_res = filter_gmail_noise(user_email)

    print(f"\n{Fore.GREEN}{'='*55}")
    print(f"{Fore.GREEN}  [DONE] NOISE REDUCTION COMPLETE")
    print(f"{Fore.GREEN}{'='*55}\n")

    return {
        "calendar_path": str(cal_res["path"]) if cal_res else None,
        "calendar_signal_count": cal_res["signal_count"] if cal_res else 0,
        "calendar_noise_count": cal_res["noise_count"] if cal_res else 0,
        "gmail_path": str(gmail_res["path"]) if gmail_res else None,
        "gmail_signal_count": gmail_res["signal_count"] if gmail_res else 0,
        "gmail_noise_count": gmail_res["noise_count"] if gmail_res else 0
    }
