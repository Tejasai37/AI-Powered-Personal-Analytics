"""
data_processing/activity_categorizer.py
----------------------------------------
Assigns categories to unified activities based on metadata and keyword matching.
Enables higher-level analytics for the AI and reporting layers.
"""

import pandas as pd
from pathlib import Path
from colorama import Fore, init

init(autoreset=True)

# Directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"

# Categorization Logic
CATEGORY_RULES = {
    'Recruitment': ['interview', 'technical round', 'hiring', 'technical round', 'candidate', 'intern round'],
    'Leadership': ['leadership', 'huddle', 'strategy', 'coaching', 'ceo', 'cto', 'management'],
    'Learning & Development': ['python', 'aws', 'skill', 'accelerator', 'learning', 'training', 'certification', 'clf-c02'],
    'Sync & Meetings': ['sync up', 'daily sync', 'standup', 'catch up', 'weekly sync', 'coordination'],
    'Project Work': ['internship', 'program', 'apsche', 'module', 'content review', 'project assignment'],
    'Admin & Operations': ['review', 'uploading', 'report', 'admin', 'documentation', 'operational']
}

DEFAULT_CATEGORY = "General Work"


def assign_category(row):
    """Matches keywords in title and description to assign a category."""
    title = str(row['title']).lower()
    description = str(row['description']).lower()
    full_text = f"{title} {description}"

    for category, keywords in CATEGORY_RULES.items():
        if any(keyword.lower() in full_text for keyword in keywords):
            return category
            
    # Default categorization based on source if no keywords match
    if row['source'] == 'Calendar':
        return "Uncategorized Meeting"
    return "Uncategorized Email"


def run_activity_categorization(user_email: str) -> Path | None:
    """Runs the activity categorization process."""
    print(f"\n{Fore.MAGENTA}{'='*55}")
    print(f"{Fore.MAGENTA}  [TAG] CATEGORIZING ACTIVITIES")
    print(f"{Fore.MAGENTA}  Account: {user_email}")
    print(f"{Fore.MAGENTA}{'='*55}\n")

    safe_email = user_email.replace("@", "_at_").replace(".", "_")
    csv_path = DATA_DIR / f"{safe_email}_unified_activity_log.csv"

    if not csv_path.exists():
        print(f"{Fore.RED}[TAG] No unified activity log found for {user_email}")
        return None

    print(f"{Fore.CYAN}[TAG] Loading Unified Log...")
    df = pd.read_csv(csv_path)

    print(f"{Fore.CYAN}[TAG] Applying Categorization Rules...")
    df['category'] = df.apply(assign_category, axis=1)

    # Save
    out_path = DATA_DIR / f"{safe_email}_categorized_activity_log.csv"
    df.to_csv(out_path, index=False, encoding='utf-8-sig')

    print(f"{Fore.GREEN}[TAG] Categorization Complete -> {out_path.name}")
    
    # Generate Distribution Summary
    dist = df['category'].value_counts()
    dist_md = "\n".join([f"- **{cat}**: {count}" for cat, count in dist.items()])
    
    print(f"\n{Fore.YELLOW}--- Category Distribution ---")
    for cat, count in dist.items():
        print(f"  {cat:<25}: {count}")

    print(f"\n{Fore.GREEN}{'='*55}")
    print(f"{Fore.GREEN}  [DONE] CATEGORIZATION COMPLETE")
    print(f"{Fore.GREEN}{'='*55}\n")

    return {
        "path": str(out_path),
        "distribution_md": dist_md,
        "total_categorized": len(df)
    }
