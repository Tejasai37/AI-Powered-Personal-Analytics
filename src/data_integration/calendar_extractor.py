"""
data_integration/calendar_extractor.py
---------------------------------------
Extracts Google Calendar events for the past 1 year.
Saves structured data to data/raw/calendar/
"""

import os
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from tqdm import tqdm
from colorama import Fore, Style, init

init(autoreset=True)

# Output directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "raw" / "calendar"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_time_range():
    """Returns ISO 8601 timestamps for April 1st, 2025 to now (UTC)."""
    now = datetime.now(timezone.utc)
    start_date = datetime(2025, 4, 1, tzinfo=timezone.utc)
    return start_date.isoformat(), now.isoformat()


def extract_event_details(event: dict) -> dict:
    """
    Extracts and structures relevant fields from a raw calendar event.

    Args:
        event (dict): Raw event dict from Google Calendar API.

    Returns:
        dict: Cleaned and structured event data.
    """
    start = event.get("start", {})
    end = event.get("end", {})

    return {
        "id": event.get("id"),
        "title": event.get("summary", "Untitled Event"),
        "description": event.get("description", ""),
        "location": event.get("location", ""),
        "status": event.get("status", ""),
        "start_datetime": start.get("dateTime") or start.get("date", ""),
        "end_datetime": end.get("dateTime") or end.get("date", ""),
        "is_all_day": "date" in start and "dateTime" not in start,
        "recurrence": event.get("recurrence", []),
        "is_recurring": bool(event.get("recurringEventId")),
        "organizer": event.get("organizer", {}).get("email", ""),
        "creator": event.get("creator", {}).get("email", ""),
        "attendees": [
            {
                "email": a.get("email", ""),
                "response": a.get("responseStatus", ""),
                "is_self": a.get("self", False),
            }
            for a in event.get("attendees", [])
        ],
        "attendee_count": len(event.get("attendees", [])),
        "html_link": event.get("htmlLink", ""),
        "calendar_id": event.get("organizer", {}).get("email", "primary"),
        "conference_data": event.get("conferenceData", {}),
        "is_online_meeting": bool(event.get("conferenceData")),
        "created": event.get("created", ""),
        "updated": event.get("updated", ""),
    }


def fetch_all_calendars(service) -> list:
    """
    Fetches list of all calendars accessible by the user.

    Args:
        service: Google Calendar API service object.

    Returns:
        list: List of calendar metadata dicts.
    """
    print(f"{Fore.CYAN}[CALENDAR] Fetching all accessible calendars...")
    calendars_result = service.calendarList().list().execute()
    calendars = calendars_result.get("items", [])
    print(f"{Fore.GREEN}[CALENDAR] Found {len(calendars)} calendar(s).")
    return calendars


def fetch_events_from_calendar(service, calendar_id: str, cal_name: str,
                                time_min: str, time_max: str) -> list:
    """
    Fetches all events from a specific calendar within the given time range.

    Args:
        service: Google Calendar API service object.
        calendar_id (str): The calendar ID to fetch events from.
        cal_name (str): Display name of the calendar (for logging).
        time_min (str): Start of time range (ISO 8601).
        time_max (str): End of time range (ISO 8601).

    Returns:
        list: List of structured event dicts.
    """
    all_events = []
    page_token = None

    print(f"\n{Fore.CYAN}[CALENDAR] Fetching events from: {Fore.WHITE}{cal_name}")

    while True:
        response = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,       # Expand recurring events
            orderBy="startTime",
            maxResults=250,          # Max per page
            pageToken=page_token,
        ).execute()

        events = response.get("items", [])
        all_events.extend([extract_event_details(e) for e in events])

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    print(f"{Fore.GREEN}[CALENDAR] ✅ {len(all_events)} events fetched from '{cal_name}'")
    return all_events


def run_calendar_extraction(creds: Credentials, user_email: str) -> dict:
    """
    Main function to extract all calendar data.
    Saves raw structured data to data/raw/calendar/

    Args:
        creds: Authenticated Google credentials.
        user_email (str): The email address of the user.

    Returns:
        dict: Summary of extraction results.
    """
    print(f"\n{Fore.MAGENTA}{'='*55}")
    print(f"{Fore.MAGENTA}  📅 GOOGLE CALENDAR DATA EXTRACTION")
    print(f"{Fore.MAGENTA}{'='*55}\n")

    service = build("calendar", "v3", credentials=creds)
    time_min, time_max = get_time_range()

    print(f"{Fore.YELLOW}[CALENDAR] Extracting data from:")
    print(f"  Account: {user_email}")
    print(f"  Start  : {time_min}")
    print(f"  End    : {time_max}\n")

    calendars = fetch_all_calendars(service)

    all_events = []
    calendar_summary = []

    for cal in tqdm(calendars, desc="Processing calendars", colour="cyan"):
        cal_id = cal.get("id")
        cal_name = cal.get("summary", "Unknown Calendar")
        cal_access = cal.get("accessRole", "")

        events = fetch_events_from_calendar(service, cal_id, cal_name, time_min, time_max)

        # Tag each event with calendar info
        for event in events:
            event["calendar_name"] = cal_name
            event["calendar_access_role"] = cal_access

        all_events.extend(events)
        calendar_summary.append({
            "calendar_id": cal_id,
            "calendar_name": cal_name,
            "access_role": cal_access,
            "events_extracted": len(events),
        })

    # --- Save results ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_email = user_email.replace("@", "_at_").replace(".", "_")

    # Save all events
    events_file = OUTPUT_DIR / f"{safe_email}_calendar_events_{timestamp}.json"
    with open(events_file, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)

    # Save calendar summary
    summary_file = OUTPUT_DIR / f"{safe_email}_calendar_summary_{timestamp}.json"
    summary = {
        "user_email": user_email,
        "extraction_timestamp": timestamp,
        "time_range": {"from": time_min, "to": time_max},
        "total_events": len(all_events),
        "calendars": calendar_summary,
    }
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n{Fore.GREEN}{'='*55}")
    print(f"{Fore.GREEN}  ✅ CALENDAR EXTRACTION COMPLETE")
    print(f"{Fore.GREEN}{'='*55}")
    print(f"  Total Events     : {Fore.WHITE}{len(all_events)}")
    print(f"  Calendars Scanned: {Fore.WHITE}{len(calendars)}")
    print(f"  Events File      : {Fore.WHITE}{events_file.name}")
    print(f"  Summary File     : {Fore.WHITE}{summary_file.name}")
    print(f"{Fore.GREEN}{'='*55}\n")

    return summary
