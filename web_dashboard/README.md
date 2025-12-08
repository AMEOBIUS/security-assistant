# Security Assistant Web Dashboard

A lightweight web dashboard for visualizing security scan results.

## Features

- List recent scans
- View scan statistics
- Real-time updates (via API)

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the backend:
   ```bash
   cd backend
   python main.py
   ```

3. Open the frontend:
   Open `frontend/index.html` in your browser.

## Architecture

- **Backend**: FastAPI
- **Frontend**: Vue.js (via CDN) + Tailwind CSS
- **Storage**: Reads directly from `security-reports/` directory
