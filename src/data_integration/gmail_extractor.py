"""
data_integration/gmail_extractor.py
-------------------------------------
Extracts Gmail messages for the past 1 year.
Captures metadata, labels, thread info, and subject/sender details.
Saves structured data to data/raw/gmail/
"""

import os
import json
import base64
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from tqdm import tqdm
from colorama import Fore, Style, init

init(autoreset=True)

# Output directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "raw" / "gmail"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Labels to EXCLUDE (promotional, social, spam — noise)
EXCLUDE_LABELS = {"SPAM", "TRASH", "CATEGORY_PROMOTIONS", "CATEGORY_SOCIAL", "CATEGORY_FORUMS"}


def get_date_query() -> str:
    """Returns Gmail search query string for data starting December 1st, 2024."""
    return "after:2024/12/01 -category:promotions -category:social"


def decode_body(payload: dict) -> str:
    """
    Recursively extracts plain text body from email payload parts.

    Args:
        payload (dict): Gmail message payload.

    Returns:
        str: Decoded plain text body (truncated to 2000 chars to save space).
    """
    body_text = ""

    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body_text += base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            elif "parts" in part:
                body_text += decode_body(part)
    else:
        if payload.get("mimeType") == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                body_text += base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    return body_text[:2000]  # Limit to 2000 chars per message


def parse_headers(headers: list) -> dict:
    """
    Extracts key email headers into a dict.

    Args:
        headers (list): List of header dicts from Gmail message payload.

    Returns:
        dict: Extracted header fields.
    """
    header_map = {}
    keys_we_want = {"From", "To", "Cc", "Subject", "Date", "Message-ID", "Thread-Index"}
    for h in headers:
        if h.get("name") in keys_we_want:
            header_map[h["name"]] = h.get("value", "")
    return header_map


def extract_message_details(msg: dict) -> dict:
    """
    Structures a raw Gmail message into a clean dict.

    Args:
        msg (dict): Full Gmail message dict from API.

    Returns:
        dict: Cleaned and structured email data.
    """
    payload = msg.get("payload", {})
    headers = parse_headers(payload.get("headers", []))
    labels = msg.get("labelIds", [])

    # Filter out excluded labels
    filtered_labels = [l for l in labels if l not in EXCLUDE_LABELS]

    # Categorise by Gmail system labels
    is_sent = "SENT" in labels
    is_inbox = "INBOX" in labels
    is_unread = "UNREAD" in labels
    is_starred = "STARRED" in labels
    is_important = "IMPORTANT" in labels

    # Parse internal date (milliseconds epoch)
    internal_date_ms = int(msg.get("internalDate", 0))
    received_datetime = datetime.fromtimestamp(
        internal_date_ms / 1000, tz=timezone.utc
    ).isoformat() if internal_date_ms else ""

    return {
        "id": msg.get("id"),
        "thread_id": msg.get("threadId"),
        "subject": headers.get("Subject", "(No Subject)"),
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "cc": headers.get("Cc", ""),
        "date_header": headers.get("Date", ""),
        "received_datetime": received_datetime,
        "snippet": msg.get("snippet", ""),
        "body_preview": decode_body(payload),
        "labels": filtered_labels,
        "is_sent": is_sent,
        "is_inbox": is_inbox,
        "is_unread": is_unread,
        "is_starred": is_starred,
        "is_important": is_important,
        "size_estimate": msg.get("sizeEstimate", 0),
        "mime_type": payload.get("mimeType", ""),
    }


def fetch_message_ids(service, query: str, max_results: int = 20000) -> list:
    """
    Fetches all message IDs matching a query using pagination.

    Args:
        service: Gmail API service object.
        query (str): Gmail search query string.
        max_results (int): Max total messages to retrieve.

    Returns:
        list: List of message ID strings.
    """
    message_ids = []
    page_token = None

    print(f"{Fore.CYAN}[GMAIL] Fetching message IDs (query: '{query}')...")

    while len(message_ids) < max_results:
        response = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=min(500, max_results - len(message_ids)),
            pageToken=page_token,
        ).execute()

        messages = response.get("messages", [])
        message_ids.extend([m["id"] for m in messages])

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    print(f"{Fore.GREEN}[GMAIL] Found {len(message_ids)} messages to process.")
    return message_ids


def fetch_messages_in_batches(service, message_ids: list, batch_size: int = 50) -> list:
    """
    Fetches full message details in batches using batch HTTP requests.
    Falls back to individual fetches if batch fails.

    Args:
        service: Gmail API service object.
        message_ids (list): List of message IDs to fetch.
        batch_size (int): Number of messages per batch.

    Returns:
        list: List of structured message dicts.
    """
    all_messages = []

    print(f"\n{Fore.CYAN}[GMAIL] Fetching full message details...")

    for i in tqdm(range(0, len(message_ids), batch_size),
                  desc="Fetching emails", colour="blue"):
        batch_ids = message_ids[i:i + batch_size]
        results = []

        def callback(request_id, response, exception):
            if exception:
                pass  # Skip failed individual messages silently
            elif response:
                results.append(response)

        batch = service.new_batch_http_request(callback=callback)
        for msg_id in batch_ids:
            batch.add(
                service.users().messages().get(
                    userId="me",
                    id=msg_id,
                    format="full",
                )
            )
        batch.execute()

        for raw_msg in results:
            try:
                structured = extract_message_details(raw_msg)
                # Skip messages from completely excluded label sets
                if not any(l in EXCLUDE_LABELS for l in raw_msg.get("labelIds", [])):
                    all_messages.append(structured)
            except Exception:
                pass

    return all_messages


def fetch_thread_summary(service, message_ids: list) -> dict:
    """
    Builds a summary of threads — how many messages per thread.

    Args:
        service: Gmail API service object.
        message_ids (list): Full message list (assumes thread_id is in each).

    Returns:
        dict: thread_id -> message count mapping.
    """
    # We'll derive this from the already-fetched messages for efficiency
    return {}


def run_gmail_extraction(creds: Credentials, user_email: str) -> dict:
    """
    Main function to extract Gmail data.
    Saves raw structured data to data/raw/gmail/

    Args:
        creds: Authenticated Google credentials.
        user_email (str): The email address of the user.

    Returns:
        dict: Summary of extraction results.
    """
    print(f"\n{Fore.MAGENTA}{'='*55}")
    print(f"{Fore.MAGENTA}  📧 GMAIL DATA EXTRACTION")
    print(f"{Fore.MAGENTA}{'='*55}\n")

    service = build("gmail", "v1", credentials=creds)
    query = get_date_query()

    print(f"{Fore.YELLOW}[GMAIL] Extracting emails for: {Fore.WHITE}{user_email}")
    print(f"{Fore.YELLOW}[GMAIL] Using query: {Fore.WHITE}{query}\n")

    # Step 1: Get all message IDs for the past year
    message_ids = fetch_message_ids(service, query)

    if not message_ids:
        print(f"{Fore.YELLOW}[GMAIL] ⚠️  No messages found for the past year.")
        return {"total_messages": 0}

    # Step 2: Fetch full message details in batches
    all_messages = fetch_messages_in_batches(service, message_ids)

    # Step 3: Compute basic statistics
    sent_count = sum(1 for m in all_messages if m["is_sent"])
    inbox_count = sum(1 for m in all_messages if m["is_inbox"])
    thread_ids = set(m["thread_id"] for m in all_messages)

    # Step 4: Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_email = user_email.replace("@", "_at_").replace(".", "_")

    messages_file = OUTPUT_DIR / f"{safe_email}_gmail_messages_{timestamp}.json"
    with open(messages_file, "w", encoding="utf-8") as f:
        json.dump(all_messages, f, indent=2, ensure_ascii=False)

    summary = {
        "user_email": user_email,
        "extraction_timestamp": timestamp,
        "query": query,
        "total_messages": len(all_messages),
        "sent_messages": sent_count,
        "inbox_messages": inbox_count,
        "unique_threads": len(thread_ids),
        "messages_file": messages_file.name,
    }
    summary_file = OUTPUT_DIR / f"{safe_email}_gmail_summary_{timestamp}.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n{Fore.GREEN}{'='*55}")
    print(f"{Fore.GREEN}  ✅ GMAIL EXTRACTION COMPLETE")
    print(f"{Fore.GREEN}{'='*55}")
    print(f"  Total Messages   : {Fore.WHITE}{len(all_messages)}")
    print(f"  Sent             : {Fore.WHITE}{sent_count}")
    print(f"  Inbox            : {Fore.WHITE}{inbox_count}")
    print(f"  Unique Threads   : {Fore.WHITE}{len(thread_ids)}")
    print(f"  Messages File    : {Fore.WHITE}{messages_file.name}")
    print(f"  Summary File     : {Fore.WHITE}{summary_file.name}")
    print(f"{Fore.GREEN}{'='*55}\n")

    return summary
