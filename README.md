# AI-Powered Personal Analytics Agent

An intelligent data agent that aggregates, cleans, and structures Google Calendar and Gmail data into a unified professional activity log. This system prepares high-signal data for AI-driven productivity analysis.

---

## 🚀 Overview

This agent automates the "Heavy Lifting" of personal data integration. It connects to your Google Account, pulls a year's worth of history, strips away the noise (bots, newsletters, cancellations), and builds a chronological "Work Identity" map.

### Core Features
- **Multi-Account Support**: Automatically tags and organizes data based on the authenticated user.
- **Noise Reduction Engine**: Filters out 50%+ of inbox clutter (Fireflies, tl;dv, system updates).
- **Professional Categorizer**: Using keyword heuristics to label activities as *Recruitment*, *Leadership*, *L&D*, etc.
- **Contextual Linking**: Automatically connects related emails to their corresponding calendar meetings.
- **Execution Reporting**: Generates a detailed Markdown report after every run.

---

## 🛠️ Setup & Installation

### 1. Environment
- **Python**: 3.10+
- **Dependencies**: `pip install -r requirements.txt`

### 2. Google Cloud Config
1. Create a project in [Google Cloud Console](https://console.cloud.google.com/).
2. Enable **Google Calendar API** and **Gmail API**.
3. Create an **OAuth 2.0 Client ID** (Desktop Application).
4. Download the `credentials.json` and place it in the project root.

### 3. Execution
Simply run the master orchestration script:
```powershell
python main.py
```
*Note: On first run, a browser window will open for you to authorize the application.*

---

## 🏗️ Technical Architecture (The 10-Step Pipeline)

| Step | Layer | Description |
|---|---|---|
| **1-3** | **Integration** | Auth, Calendar Extraction, and Gmail Extraction (April 2025 - Now). |
| **4** | **Integration** | Exporting raw JSON data to structured CSV format. |
| **5** | **Processing** | Simple Cleaning (Deduplication, Holiday removal, Date standardization). |
| **6** | **Processing** | **Noise Filtering**: Flagging bots, newsletters, and promo-clutter. |
| **7** | **Structuring** | **Unification**: Merging Mail and Calendar into one common schema. |
| **8** | **Structuring** | **Categorization**: Assigning professional labels (Recruitment, L&D, etc). |
| **9** | **Structuring** | **Context Linking**: Pairing emails with relevant meetings via time+keywords. |
| **10** | **Reporting** | Generating a human-readable execution summary in `data/reports/`. |

---

## 📂 Project Structure

- **`src/`**: Source code partitioned by layer.
  - `auth/`: OAuth flow and identity logic.
  - `data_integration/`: API extractors and CSV exporters.
  - `data_processing/`: The "Intelligence" modules (Filtering, Categorizing).
  - `utils/`: Report generation and helpers.
- **`data/`**: Storage (excluded from Git).
  - `raw/`: Untouched API responses (JSON).
  - `processed/`: Intermediate and final CSV logs.
  - `reports/`: Execution Markdown reports.

---

## 📄 Key Outputs
- **Unified Master Log**: `[email]_final_structured_data.csv`
- **Execution Summary**: `data/reports/report_[email]_[timestamp].md`

---
*Created as part of the AI-Powered Personal Analytics Project.*
