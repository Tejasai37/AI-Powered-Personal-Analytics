"""
auth/google_auth.py
-------------------
Handles OAuth 2.0 authentication for Google APIs.
Manages token creation, refresh, and secure storage.
"""

import os
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from colorama import Fore, Style, init

init(autoreset=True)

# Define the scopes required for Gmail and Google Calendar
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # project root: src/auth -> src -> root
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"


def authenticate() -> Credentials:
    """
    Authenticates the user via OAuth 2.0 using installed app flow.
    - If a valid token exists, it is reused.
    - If the token is expired, it is refreshed automatically.
    - If no token exists, the user is prompted via browser to log in.

    Returns:
        google.oauth2.credentials.Credentials: Authenticated credentials object.
    """
    creds = None

    # Load existing token if available
    if TOKEN_FILE.exists():
        print(f"{Fore.CYAN}[AUTH] Loading existing token from {TOKEN_FILE.name}...")
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # If credentials are invalid or expired, refresh or re-authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print(f"{Fore.YELLOW}[AUTH] Token expired. Refreshing...")
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"\n{Fore.RED}[ERROR] credentials.json not found at: {CREDENTIALS_FILE}\n"
                    "Please download it from Google Cloud Console → APIs & Services → Credentials."
                )

            print(f"{Fore.YELLOW}[AUTH] No valid token found. Starting OAuth 2.0 flow...")
            print(f"{Fore.YELLOW}[AUTH] A browser window will open for you to log in and grant permissions.\n")

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        print(f"{Fore.GREEN}[AUTH] Token saved to {TOKEN_FILE.name}")

    print(f"{Fore.GREEN}[AUTH] Authentication successful!\n")
    return creds


def get_user_email(creds: Credentials) -> str:
    """
    Fetches the primary email address of the authenticated user.

    Args:
        creds: Authenticated Google credentials.

    Returns:
        str: User email address.
    """
    print(f"{Fore.CYAN}[AUTH] Identifying user account...")
    service = build("oauth2", "v2", credentials=creds)
    user_info = service.userinfo().get().execute()
    email = user_info.get("email", "unknown_user")
    print(f"{Fore.GREEN}[AUTH] Connected as: {Fore.WHITE}{email}\n")
    return email
