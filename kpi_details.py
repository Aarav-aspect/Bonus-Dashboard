def enrich_kpis(kpis, raw_metrics):
    """Enrich KPI dictionary with detail objects for frontend drilldowns."""
    enriched = kpis.copy()

    # 1. Estimate Production / Reactive Leads %
    if "Estimate Production / Reactive Leads %" in enriched:
        val = enriched["Estimate Production / Reactive Leads %"]
        enriched["Estimate Production / Reactive Leads %"] = {
            "value": val,
            "numerator": raw_metrics.get("estimate_production_count", 0),
            "denominator": raw_metrics.get("reactive_leads_count", 0),
            "numerator_label": "Estimates Raised (by Engineers)",
            "denominator_label": "Reactive Leads Closed"
        }

    # 2. Estimate Conversion %
    if "Estimate Conversion %" in enriched:
        val = enriched["Estimate Conversion %"]
        enriched["Estimate Conversion %"] = {
            "value": val,
            "numerator": raw_metrics.get("converted_fp_wo_count", 0),
            "denominator": raw_metrics.get("total_fp_wo_count", 0),
            "numerator_label": "Converted Estimates",
            "denominator_label": "Total Estimates Raised"
        }

    # 3. FOC Conversion Rate %
    if "FOC Conversion Rate %" in enriched:
        val = enriched["FOC Conversion Rate %"]
        enriched["FOC Conversion Rate %"] = {
            "value": val,
            "numerator": raw_metrics.get("raised_from_foc_count", 0),
            "denominator": raw_metrics.get("foc_jobs_count", 0),
            "numerator_label": "Converted Jobs raised from FOC",
            "denominator_label": "Attended FOC/£60 Estimates"
        }

    # 4. Average Converted Estimate Value (£)
    if "Average Converted Estimate Value (£)" in enriched:
        val = enriched["Average Converted Estimate Value (£)"]
        enriched["Average Converted Estimate Value (£)"] = {
            "value": val,
            "numerator": raw_metrics.get("total_converted_estimate_value", 0),
            "denominator": raw_metrics.get("converted_estimate_count", 0),
            "numerator_label": "Total Value",
            "denominator_label": "Converted Counts"
        }

    # 5. Average Review Rating
    if "Average Review Rating" in enriched:
        val = enriched["Average Review Rating"]
        enriched["Average Review Rating"] = {
            "value": val,
            "numerator": raw_metrics.get("count_reviews_prev", 0),
            "denominator": None,
            "numerator_label": "Total Reviews (Prev Month)",
            "denominator_label": None,
            "result_label": "ARR"
        }

    # 6. Review Ratio %
    if "Review Ratio %" in enriched:
        val = enriched["Review Ratio %"]
        enriched["Review Ratio %"] = {
            "value": val,
            "numerator": raw_metrics.get("count_reviews_prev", 0),
            "denominator": raw_metrics.get("count_attended_prev", 0),
            "numerator_label": "Reviews (Prev Month)",
            "denominator_label": "Completed Jobs (Prev Month)"
        }

    # 7. Engineer Satisfaction %
    if "Engineer Satisfaction %" in enriched:
        val = enriched["Engineer Satisfaction %"]
        count = raw_metrics.get("engineer_survey_count", 0)
        avg = raw_metrics.get("engineer_satisfaction_avg", 0) or 0
        enriched["Engineer Satisfaction %"] = {
            "value": val,
            "numerator": avg * count,
            "denominator": count,
            "numerator_label": "Total Score",
            "denominator_label": "Surveys"
        }

    # 8. Cases %
    if "Cases %" in enriched:
        val = enriched["Cases %"]
        enriched["Cases %"] = {
            "value": val,
            "numerator": raw_metrics.get("cases_count", 0),
            "denominator": raw_metrics.get("total_jobs_prev", 0),
            "numerator_label": "Cases",
            "denominator_label": "Total Jobs (Prev Month)"
        }

    # 9. Ops Count %
    if "Ops Count %" in enriched:
        val = enriched["Ops Count %"]
        enriched["Ops Count %"] = {
            "value": val,
            "numerator": raw_metrics.get("ops_count", 0),
            "denominator": raw_metrics.get("ops_target", 0),
            "numerator_label": "Total Ops",
            "denominator_label": "Target Ops"
        }

    # 10. Sales Target Achievement %
    if "Sales Target Achievement %" in enriched:
        val = enriched["Sales Target Achievement %"]
        enriched["Sales Target Achievement %"] = {
            "value": val,
            "numerator": raw_metrics.get("invoice_sales", 0),
            "denominator": raw_metrics.get("sales_target", 0),
            "numerator_label": "Invoice Sales",
            "denominator_label": "Sales Target"
        }

    # 11. Callback Jobs %
    if "Callback Jobs %" in enriched:
        val = enriched["Callback Jobs %"]
        enriched["Callback Jobs %"] = {
            "value": val,
            "numerator": raw_metrics.get("callback_jobs_count", 0),
            "denominator": raw_metrics.get("total_jobs", 0),
            "numerator_label": "Callbacks",
            "denominator_label": "Total Attended Jobs"
        }

    # 12. Average Site Value (£)
    if "Average Site Value (£)" in enriched:
        val = enriched["Average Site Value (£)"]
        enriched["Average Site Value (£)"] = {
            "value": val,
            "numerator": raw_metrics.get("total_charge", 0),
            "denominator": raw_metrics.get("site_count", 0),
            "numerator_label": "Total Charge",
            "denominator_label": "Unique Sites"
        }

    # 13. Late to Site %
    if "Late to Site %" in enriched:
        val = enriched["Late to Site %"]
        enriched["Late to Site %"] = {
            "value": val,
            "numerator": raw_metrics.get("late_count", 0),
            "denominator": raw_metrics.get("service_appts", 0),
            "numerator_label": "Late Visits",
            "denominator_label": "Total Appts"
        }

    # 14. SA Attended (Performance)
    if "SA Attended" in enriched:
        val = enriched["SA Attended"]
        enriched["SA Attended"] = {
            "value": val,
            "numerator": None,
            "denominator": None,
            "numerator_label": None,
            "denominator_label": None
        }

    # ── Vehicular ──────────────────────────────────────────────────────────────

    # 15. Average Driving Score (plain average — no fraction breakdown)
    if "Average Driving Score" in enriched:
        val = enriched["Average Driving Score"]
        enriched["Average Driving Score"] = {
            "value": val,
            "numerator": raw_metrics.get("driver_count", 0),
            "denominator": None,
            "numerator_label": "Drivers in Trade Group",
            "denominator_label": None,
        }

    # 16. Drivers with <7
    if "Drivers with <7" in enriched:
        val = enriched["Drivers with <7"]
        enriched["Drivers with <7"] = {
            "value": val,
            "numerator": raw_metrics.get("drivers_below_7_count", 0),
            "denominator": raw_metrics.get("driver_count", 0),
            "numerator_label": "Drivers Scoring < 7",
            "denominator_label": "Total Drivers",
        }

    # 17. VCR Update %
    if "VCR Update %" in enriched:
        val = enriched["VCR Update %"]
        enriched["VCR Update %"] = {
            "value": val,
            "numerator": raw_metrics.get("vcr_count", 0),
            "denominator": raw_metrics.get("vcr_target", 0),
            "numerator_label": "VCR Forms Submitted",
            "denominator_label": "Target (Ops × 2 biweekly)",
        }

    # ── Procedural ─────────────────────────────────────────────────────────────

    # 18. TQR Ratio %
    if "TQR Ratio %" in enriched:
        val = enriched["TQR Ratio %"]
        enriched["TQR Ratio %"] = {
            "value": val,
            "numerator": raw_metrics.get("tqr_total_count", 0),
            "denominator": raw_metrics.get("total_jobs", 0),
            "numerator_label": "Jobs with TQR",
            "denominator_label": "Total Attended Jobs",
        }

    # 19. TQR (Not Satisfied) Ratio %
    if "TQR (Not Satisfied) Ratio %" in enriched:
        val = enriched["TQR (Not Satisfied) Ratio %"]
        enriched["TQR (Not Satisfied) Ratio %"] = {
            "value": val,
            "numerator": raw_metrics.get("tqr_not_satisfied_count", 0),
            "denominator": raw_metrics.get("tqr_total_count", 0),
            "numerator_label": "TQR — Not Satisfied",
            "denominator_label": "Total TQR Jobs",
        }

    # 20. Unclosed SA %
    if "Unclosed SA %" in enriched:
        val = enriched["Unclosed SA %"]
        enriched["Unclosed SA %"] = {
            "value": val,
            "numerator": raw_metrics.get("unclosed_sa_count", 0),
            "denominator": raw_metrics.get("unclosed_sa_total", 0),
            "numerator_label": "Unclosed Appointments",
            "denominator_label": "Total Appts (excl. today)",
        }

    # 21. Reactive 6+ hours %
    if "Reactive 6+ hours %" in enriched:
        val = enriched["Reactive 6+ hours %"]
        enriched["Reactive 6+ hours %"] = {
            "value": val,
            "numerator": raw_metrics.get("jobs_6_plus_total", 0),
            "denominator": raw_metrics.get("reactive_jobs_count", 0),
            "numerator_label": "Reactive Jobs ≥ 6 hrs",
            "denominator_label": "Total Reactive Jobs",
        }

    # 22. Engineer Retention %
    if "Engineer Retention %" in enriched:
        val = enriched["Engineer Retention %"]
        enriched["Engineer Retention %"] = {
            "value": val,
            "numerator": raw_metrics.get("ops_count", 0),
            "denominator": raw_metrics.get("ops_baseline", 0),
            "numerator_label": "Current Ops",
            "denominator_label": "Baseline Ops (Start of Month)"
        }

    return enriched
