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

    # ── Add more drilldowns below ────────────────────────────────────────
    # Example (uncomment and adapt when ready):
    #
    # "VCR Update %": {
    #     "title": "VCR Submissions",
    #     "data_source": "vcr",              # you'd create /api/drilldown/vcr
    #     "columns": [
    #         {"key": "name",       "label": "Engineer",     "type": "text"},
    #         {"key": "submitted",  "label": "Submitted",    "type": "score", "max_value": 4},
    #         {"key": "submitted",  "label": "",             "type": "bar",   "max_value": 4},
    #     ],
    #     "summary_cards": [
    #         {"key": "total_count",    "label": "Total Engineers", "color": "neutral"},
    #         {"key": "complete_count", "label": "Complete",        "color": "green"},
    #     ],
    # },
}
