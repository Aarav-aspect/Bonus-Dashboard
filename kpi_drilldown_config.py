"""KPI Drilldown Configuration."""

KPI_DRILLDOWNS = {

    "Drivers with <7": {
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

    "VCR Update %": {
        "title": "VCR Submissions",
        "data_source": "vcr_update",         # maps to /api/drilldown/vcr-update
        "columns": [
            {"key": "name",        "label": "Name",       "type": "text"},
            {"key": "submissions", "label": "Submitted",  "type": "text"},
            {"key": "target",      "label": "Target",     "type": "text"},
        ],
        "summary_cards": [
            {"key": "total_count", "label": "Total Drivers", "color": "neutral"},
        ],
    },

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
    
    "Engineer Retention %": {
        "title": "Ops",
        "data_source": "ops_list",
        "columns": [
            {"key": "name",  "label": "Name",  "type": "text"},
            {"key": "trade", "label": "Trade", "type": "text"},
            {"key": "region", "label": "Region", "type": "text"},
        ],
        "summary_cards": [
            {"key": "total_count", "label": "Current Ops", "color": "neutral"},
        ],
    },

    "Satisfaction Form Update %": {
        "title": "Satisfaction Forms",
        "data_source": "satisfaction_form_update",
        "columns": [
            {"key": "name",      "label": "Engineer",  "type": "text"},
            {"key": "trade",     "label": "Trade",     "type": "text"},
            {"key": "region",    "label": "Region",    "type": "text"},
            {"key": "submitted", "label": "Submitted", "type": "text"},
        ],
        "summary_cards": [
            {"key": "total_count",     "label": "Total Engineers", "color": "neutral"},
            {"key": "submitted_count", "label": "Submitted",       "color": "green"},
        ],
    },
}
