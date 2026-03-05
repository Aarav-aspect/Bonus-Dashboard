"""
KPI Drilldown Configuration
============================
Controls which KPIs show a "View Details" button in the drilldown modal,
and defines what data (columns) to display in the popup table.

To add a new drilldown:
  1. Add a new entry to KPI_DRILLDOWNS  (key = exact KPI name as it appears on the dashboard)
  2. Set the data_source to point at the backend function that returns the rows
  3. List the columns you want shown in the popup table

Column definition:
  - key       : field name coming from the backend response
  - label     : header text shown in the table
  - type      : "text" | "score" | "bar"
        text  → plain string
        score → numeric with color coding (green >= good, red < bad)
        bar   → thin progress bar (0–max_value)
  - max_value : (only for type="bar") the upper bound for the bar width
"""

KPI_DRILLDOWNS = {

    # ── Drivers with <7 % ────────────────────────────────────────────────
    "Drivers with <7 %": {
        "title": "Drivers",                  # Modal title prefix
        "data_source": "drivers",            # maps to /api/drilldown/drivers
        "columns": [
            {"key": "name",  "label": "Name",  "type": "text"},
            {"key": "score", "label": "Score", "type": "score", "max_value": 10},
            {"key": "score", "label": "",      "type": "bar",   "max_value": 10},
        ],
        "summary_cards": [
            {"key": "total_count",   "label": "Total Drivers", "color": "neutral"},
            {"key": "below_7_count", "label": "Below 7",       "color": "red"},
        ],
    },

    # ── Average Driving Score ────────────────────────────────────────────
    "Average Driving Score": {
        "title": "Drivers",                  # Same modal as above
        "data_source": "drivers",            # reuses /api/drilldown/drivers
        "columns": [
            {"key": "name",  "label": "Name",  "type": "text"},
            {"key": "score", "label": "Score", "type": "score", "max_value": 10},
            {"key": "score", "label": "",      "type": "bar",   "max_value": 10},
        ],
        "summary_cards": [
            {"key": "total_count",   "label": "Total Drivers", "color": "neutral"},
            {"key": "below_7_count", "label": "Below 7",       "color": "red"},
        ],
    },

    # ── Average Review Rating ────────────────────────────────────────────
    "Average Review Rating": {
        "title": "Reviews",
        "data_source": "reviews",            # maps to /api/drilldown/reviews
        "columns": [
            {"key": "sa_number", "label": "SA Number", "type": "text"},
            {"key": "rating",    "label": "Rating",    "type": "score", "max_value": 5},
            {"key": "rating",    "label": "",           "type": "bar",   "max_value": 5},
        ],
        "summary_cards": [
            {"key": "total_count", "label": "Total Reviews", "color": "neutral"},
            {"key": "avg_rating",  "label": "Average",       "color": "blue"},
        ],
    },

    # ── Ops Count % ──────────────────────────────────────────────────────
    "Ops Count %": {
        "title": "Ops",
        "data_source": "ops_list",               # maps to /api/drilldown/ops-list
        "columns": [
            {"key": "name",  "label": "Name",  "type": "text"},
            {"key": "trade", "label": "Trade", "type": "text"},
        ],
        "summary_cards": [
            {"key": "total_count", "label": "Total Ops", "color": "neutral"},
        ],
    },

    # ── Unclosed SA % ────────────────────────────────────────────────────
    "Unclosed SA %": {
        "title": "SAs",
        "data_source": "unclosed_sas",
        "columns": [
            {"key": "appointment_number", "label": "SA Number", "type": "text"},
            {"key": "status",             "label": "Status",    "type": "text"},
        ],
        "summary_cards": [
            {"key": "total_count",    "label": "Total Unclosed", "color": "red"},
        ],
    },

    # ── Callback Jobs % ──────────────────────────────────────────────────
    "Callback Jobs %": {
        "title": "Callback Jobs",
        "data_source": "callback_jobs",
        "columns": [
            {"key": "job_number", "label": "Job Number", "type": "text"},
        ],
        "summary_cards": [
            {"key": "total_count", "label": "Total Callbacks", "color": "red"},
        ],
    },

    # ── Reactive 6+ hours % ──────────────────────────────────────────────
    "Reactive 6+ hours %": {
        "title": "Reactive 6+ Hrs",
        "data_source": "reactive_6plus",
        "columns": [
            {"key": "appointment_number", "label": "SA Number", "type": "text"},
            {"key": "duration",           "label": "Duration (hrs)", "type": "text"},
        ],
        "summary_cards": [
            {"key": "total_count", "label": "Total 6+ Hrs", "color": "red"},
        ],
    },

    # ── TQR (Not Satisfied) Ratio % ──────────────────────────────────────
    "TQR (Not Satisfied) Ratio %": {
        "title": "TQR Not Satisfied",
        "data_source": "tqr_not_satisfied",
        "columns": [
            {"key": "job_name", "label": "Job Name", "type": "text"},
        ],
        "summary_cards": [
            {"key": "total_count", "label": "Not Satisfied", "color": "red"},
        ],
    },

    # ── Late to Site % ────────────────────────────────────────────────────
    "Late to Site %": {
        "title": "Late Engineers",
        "data_source": "late_to_site",
        "columns": [
            {"key": "engineer_name", "label": "Engineer", "type": "text"},
            {"key": "summary",       "label": "Late / Total", "type": "text"},
        ],
        "summary_cards": [
            {"key": "total_late", "label": "Total Late", "color": "red"},
            {"key": "total_sas",  "label": "Total SAs",  "color": "blue"},
        ],
    },

    # ── Cases % ────────────────────────────────────────────────────────
    "Cases %": {
        "title": "Cases",
        "data_source": "cases",
        "columns": [
            {"key": "case_number", "label": "Case Number", "type": "text"},
            {"key": "case_type",   "label": "Case Type", "type": "text"},
        ],
        "summary_cards": [
            {"key": "total_count", "label": "Total Cases", "color": "red"},
        ],
    },
}
