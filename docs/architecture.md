# Technical Architecture Guide

This document details the internal logic and processing rules of the AI-Powered Personal Analytics Agent.

---

## 1. Authentication & Identity Layer
- **OAuth 2.0**: Uses `google-auth-oauthlib` for user authorization.
- **Identity Scope**: Added `userinfo.email` to the flow to uniquely identify the user. This ensures that in a multi-user environment, data is never mixed.
- **Token Management**: `token.json` stores long-lived refresh tokens. If scopes change, the token must be deleted to re-trigger the consent screen.

## 2. Extraction & Export Layer
- **Date Range**: Hardcoded to start from **April 1st, 2025**.
- **Calendar Logic**: Fetches all available calendars (Primary, Shared, and Holidays).
- **Gmail Logic**: Uses a custom query (`after:2025/04/01`) to limit API payload.
- **Safe Export**: Converts nested JSON objects (like attendees and labels) into flattened strings for CSV compatibility.

## 3. Processing & Structuring Layer
This is the "Intelligence" layer of the system.

### A. Noise Filtering (`noise_filter.py`)
Identifies non-human communication and clutter:
- **Bot/Tool Filtering**: Specifically targets `Fireflies.ai`, `tl;dv`, `Zoho`, and `Skill Wallet`.
- **System Categories**: Flags Gmail-categorized `UPDATES` and `PROMOTIONS` as noise.
- **Calendar Cleanup**: Removes "Out of Office" and "Working Location" blocks.

### B. Activity Categorizer (`activity_categorizer.py`)
Uses a rule-based engine to prioritize activities:
- **Recruitment**: Keywords like `Interview`, `Technical Round`.
- **Learning**: Keywords like `AWS`, `Python`, `Training`.
- **Leadership**: Keywords like `Strategy`, `Huddle`, `Coaching`.

### C. Context Linker (`context_linker.py`)
Constructs a narrative of the user's day:
- **Logic**: If an email is received/sent within **60 minutes** of a meeting AND shares **keywords** with the meeting title, it is linked.
- **Result**: Every linked activity receives a `linked_context_id`.

## 4. Final Data Schema
The final output (`final_structured_data.csv`) contains:
- `timestamp`: Unified ISO8601 start time.
- `source`: Calendar | Gmail.
- `activity_type`: Meeting | Sent Email | Received Email.
- `title`: Subject or Event Name.
- `description`: Filtered body content.
- `participants`: Unified list of responders/senders.
- `category`: The assigned professional bucket.
- `linked_context_id`: The bridge between related work items.

---
*Documentation v1.1 - April 2026*
