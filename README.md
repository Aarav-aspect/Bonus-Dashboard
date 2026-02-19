# TGM Bonus Dashboard

A modern, full-stack performance dashboard for tracking Trade Group Managers' bonuses, KPIs, and targets. Built with **FastAPI** (Python) and **React** (Vite).

## 🚀 Features

-   **Interactive Dashboard**: Real-time visualization of KPI performance.
-   **KPI Documentation**: Detailed [KPI Diary](KPI_DIARY.md) explaining all metrics.
-   **Dynamic Thresholds**: Adjustable targets for different trade groups.
-   **Bonus Calculation**: Automated bonus computations based on complex logic.
-   **Modern UI**: Glass-morphism design with responsive components.

## 🛠️ Tech Stack

-   **Backend**: Python, FastAPI, Pandas, Salesforce API
-   **Frontend**: React, Vite, Tailwind CSS, Lucide Icons
-   **Data Sources**: Salesforce, Webfleet

## 📋 Prerequisites

-   **Python 3.9+**
-   **Node.js 18+**

## ⚡ Quick Start

### 1. Backend Setup

```bash
# Navigate to project root
cd "TGM bonus"

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

### 2. Frontend Setup

```bash
# Navigate to web app directory
cd web-app

# Install dependencies
npm install

# Run the dev server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) to view the app.

## 📁 Project Structure

```
TGM bonus/
├── KPI_DIARY.md        # Comprehensive KPI documentation
├── api.py              # FastAPI entry point
├── backend.py          # Core logic & data fetching
├── queries.py          # Centralized SOQL queries
├── targets.py          # KPI calculation logic
├── tests/              # Test & debug scripts
├── web-app/            # React Frontend
│   ├── src/
│   │   ├── pages/      # Dashboard views
│   │   ├── components/ # Reusable UI components
│   └── ...
└── ...
```
