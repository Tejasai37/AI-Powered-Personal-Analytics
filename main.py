"""
main.py
--------
Entry point for the AI-Powered Personal Analytics Agent.
Runs the full Data Integration Layer:
  1. Authenticates with Google via OAuth 2.0
  2. Extracts Google Calendar events (past 1 year)
  3. Extracts Gmail messages   (past 1 year)
  4. Saves structured raw data to data/raw/
"""

import sys
import json
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.auth.google_auth import authenticate, get_user_email
from src.data_integration.calendar_extractor import run_calendar_extraction
from src.data_integration.gmail_extractor import run_gmail_extraction
from src.data_integration.csv_exporter import run_csv_export
from src.data_processing.simple_preprocessing import run_simple_preprocessing
from src.data_processing.noise_filter import run_noise_filtering
from src.data_processing.data_structurer import run_data_structuring
from src.data_processing.activity_categorizer import run_activity_categorization
from src.data_processing.context_linker import run_contextual_linking
from src.utils.report_generator import generate_markdown_report


def print_banner():
    print(f"\n{Fore.CYAN}{'='*55}")
    print(f"{Fore.CYAN}   [AI] AI-POWERED PERSONAL ANALYTICS AGENT")
    print(f"{Fore.CYAN}        Data Integration Layer v1.0")
    print(f"{Fore.CYAN}{'='*55}\n")


def save_master_summary(calendar_summary: dict, gmail_summary: dict):
    """Saves a combined extraction summary to data/raw/extraction_summary.json"""
    output_dir = Path("data") / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    master = {
        "calendar": calendar_summary,
        "gmail": gmail_summary,
    }

    summary_path = output_dir / "extraction_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)

    print(f"{Fore.CYAN}[MAIN] Master summary saved → {summary_path}")


def main():
    print_banner()

    # ── Step 1: Authenticate ──────────────────────────────────
    print(f"{Fore.YELLOW}[STEP 1/10] Authenticating with Google...\n")
    try:
        creds = authenticate()
        user_email = get_user_email(creds)
    except Exception as e:
        print(f"{Fore.RED}[ERROR] {e}")
        sys.exit(1)

    # ── Step 2: Extract Calendar Data ────────────────────────
    print(f"{Fore.YELLOW}[STEP 2/10] Extracting Google Calendar data...\n")
    calendar_summary = run_calendar_extraction(creds, user_email)

    # ── Step 3: Extract Gmail Data ───────────────────────────
    print(f"{Fore.YELLOW}[STEP 3/10] Extracting Gmail data...\n")
    gmail_summary = run_gmail_extraction(creds, user_email)

    # ── Step 4: Export to CSV ───────────────────────────────
    print(f"{Fore.YELLOW}[STEP 4/10] Exporting data to CSV...\n")
    csv_summary = run_csv_export(user_email)

    # ── Step 5: Simple Preprocessing ────────────────────────
    print(f"{Fore.YELLOW}[STEP 5/10] Running simple preprocessing...\n")
    proc_summary = run_simple_preprocessing(user_email)

    # ── Step 6: Noise Filtering ─────────────────────────────
    print(f"{Fore.YELLOW}[STEP 6/10] Filtering noise from data...\n")
    filter_summary = run_noise_filtering(user_email)

    # ── Step 7: Data Structuring ────────────────────────────
    print(f"{Fore.YELLOW}[STEP 7/10] Structuring unified data log...\n")
    structure_summary = run_data_structuring(user_email)

    # ── Step 8: Activity Categorization ─────────────────────
    print(f"{Fore.YELLOW}[STEP 8/10] Categorizing activities for analytics...\n")
    cat_summary = run_activity_categorization(user_email)

    # ── Step 9: Contextual Linking ──────────────────────────
    print(f"{Fore.YELLOW}[STEP 9/10] Linking related work contexts...\n")
    link_summary = run_contextual_linking(user_email)

    # ── Save master summary ──────────────────────────────────
    save_master_summary(calendar_summary, gmail_summary)

    # ── Step 10: Generate Markdown Report ─────────────────────
    print(f"{Fore.YELLOW}[STEP 10/10] Generating execution report...\n")
    report_data = {
        "calendar": calendar_summary,
        "gmail": gmail_summary,
        "preprocessing": proc_summary,
        "filter": filter_summary,
        "categorization": cat_summary,
        "cat_distribution_md": cat_summary.get("distribution_md", ""),
        "linking": link_summary,
        "final_file_name": Path(link_summary.get("path", "")).name
    }
    report_path = generate_markdown_report(user_email, report_data)

    # ── Final report ─────────────────────────────────────────
    print(f"\n{Fore.GREEN}{'='*55}")
    print(f"{Fore.GREEN}  [DONE] DATA INTEGRATION COMPLETE!")
    print(f"{Fore.GREEN}{'='*55}")
    print(f"  [CAL]  Calendar Events   : {Fore.WHITE}{calendar_summary.get('total_events', 0)}")
    print(f"  [MAIL] Emails Extracted  : {Fore.WHITE}{gmail_summary.get('total_messages', 0)}")
    print(f"  [JSON] Raw JSON          : {Fore.WHITE}data/raw/")
    print(f"  [CSV]  Processed CSV     : {Fore.WHITE}data/processed/")
    print(f"  [CLEAN] Cleaned Data     : {Fore.WHITE}data/processed/ (prefixed 'clean_')")
    print(f"  [SIGNAL] Filtered Signal : {Fore.WHITE}data/processed/ (prefixed 'filtered_')")
    print(f"  [MASTER] Unified Log    : {Fore.WHITE}data/processed/ (unified_activity_log.csv)")
    print(f"  [FINAL]  Structured Data: {Fore.WHITE}data/processed/ (final_structured_data.csv)")
    print(f"  [REPORT] Markdown Report : {Fore.WHITE}{report_path}")
    print(f"{Fore.GREEN}{'='*55}")
    print(f"\n{Fore.CYAN}[OK] Your data is ready! Check the Markdown report for details.\n")


if __name__ == "__main__":
    main()
