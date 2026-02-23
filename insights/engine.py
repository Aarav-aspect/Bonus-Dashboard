# insights/pools/vehicular.py
from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
import math
from datetime import datetime


VEHICULAR_KPIS = [
    "Average Driving Score",
    "Drivers with <7 %",
    "VCR Update %",
]

LOW_SCORE_CUT = 60.0
CONSISTENTLY_LOW_MONTHS = 2


def _is_nan(x: Any) -> bool:
    return isinstance(x, float) and math.isnan(x)


def _is_number(x: Any) -> bool:
    return x is not None and isinstance(x, (int, float)) and (not _is_nan(x))


def _safe_float(x: Any) -> Optional[float]:
    return float(x) if _is_number(x) else None


def _fmt(v: Optional[float], digits: int = 1) -> str:
    n = _safe_float(v)
    return "-" if n is None else f"{n:.{digits}f}"


def _fmt_money(v: Optional[float], digits: int = 0) -> str:
    n = _safe_float(v)
    return "-" if n is None else f"{n:,.{digits}f}"


def _impact_text(kpi: str) -> str:
    return {
        "Average Driving Score": "Lower driving scores can mean higher risk and higher cost over time.",
        "Drivers with <7 %": "More drivers below the safe threshold increases risk and likely increases incidents or maintenance costs.",
        "VCR Update %": "Lower vehicle check completion increases the chance of missed issues and downtime.",
    }.get(kpi, "Vehicular performance is below target and may increase risk and downtime.")


def _action_text(kpi: str) -> Dict[str, str]:
    return {
        "Average Driving Score": {"level": "MEDIUM", "text": "Improve driving behaviour: coaching for the lowest scorers and clear expectations."},
        "Drivers with <7 %": {"level": "HIGH", "text": "Focus on the risky driver group: targeted coaching and follow-ups until they improve."},
        "VCR Update %": {"level": "HIGH", "text": "Increase vehicle checks: make checks mandatory and follow up on missed submissions."},
    }.get(kpi, {"level": "MEDIUM", "text": "Investigate and fix the drivers behind weak vehicular performance."})


def _get_bonus_tuple(result: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[str]]:
    b = (result or {}).get("bonus") or {}
    pot = _safe_float(b.get("pot"))
    mult = _safe_float(b.get("multiplier"))
    val = _safe_float(b.get("bonus_value"))
    band = b.get("current_band") if isinstance(b.get("current_band"), str) else None
    return pot, mult, val, band


def _kpi_month_scores(month_payloads: List[Dict[str, Any]]) -> Dict[str, List[Optional[float]]]:
    out: Dict[str, List[Optional[float]]] = {k: [] for k in VEHICULAR_KPIS}
    for payload in (month_payloads or []):
        scores = (payload or {}).get("kpi_scores") or {}
        for kpi in VEHICULAR_KPIS:
            out[kpi].append(_safe_float(scores.get(kpi)))
    return out


def _low_count(scores: List[Optional[float]]) -> int:
    return int(sum(1 for s in (scores or []) if (_is_number(s) and s < LOW_SCORE_CUT)))


def _first_last_change(series: List[Optional[float]]) -> Optional[float]:
    if not series:
        return None
    a = series[0]
    b = series[-1]
    return (b - a) if (_is_number(a) and _is_number(b)) else None


def _unique_actions(kpis: List[str]) -> List[Dict[str, str]]:
    seen = set()
    out: List[Dict[str, str]] = []
    for kpi in kpis:
        a = _action_text(kpi)
        key = (a.get("level"), a.get("text"))
        if key not in seen:
            seen.add(key)
            out.append(a)
    return out


def build_vehicular_quarterly_insights(
    *,
    trade_group: str,
    trade_filter: str,
    quarter_months: List[str],
    month_payloads: List[Dict[str, Any]],
    quarter_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    month_scores = _kpi_month_scores(month_payloads or [])

    low_counts = {k: _low_count(v) for k, v in month_scores.items()}
    consistently_low = sorted([k for k, c in low_counts.items() if c >= CONSISTENTLY_LOW_MONTHS])

    changes = {k: _first_last_change(v) for k, v in month_scores.items()}
    improved = sorted([k for k in VEHICULAR_KPIS if _is_number(changes.get(k)) and changes[k] > 0])
    worsened = sorted([k for k in VEHICULAR_KPIS if _is_number(changes.get(k)) and changes[k] < 0])

    qres = quarter_result or {}
    q_pool = _safe_float(((qres.get("category_scores") or {}).get("Vehicular")))
    q_overall = _safe_float(qres.get("overall_score"))
    q_pot, q_mult, q_bonus_val, q_band = _get_bonus_tuple(qres)

    window_label = ", ".join(quarter_months) if quarter_months else "the last 3 completed months"

    bonus_sentence = None
    if _is_number(q_bonus_val) or (isinstance(q_band, str) and q_band):
        earned = f"£{_fmt_money(q_bonus_val,0)}" if _is_number(q_bonus_val) else "an unknown amount"
        band_txt = (q_band or "").strip()
        if band_txt:
            bonus_sentence = f"Bonus result for this 3-month period: {band_txt.title()} (you earned {earned})."
        else:
            bonus_sentence = f"Bonus result for this 3-month period: you earned {earned}."

    if consistently_low:
        summary = (
            f"Over {window_label}, vehicle-related measures were repeatedly below target in at least 2 of the 3 months: "
            f"{', '.join(consistently_low)}."
        )
    else:
        summary = f"Over {window_label}, vehicle-related measures did not show any repeated weak areas across the 3 months."

    key_findings: List[str] = []
    key_findings.append(f"Months analysed: {window_label}.")
    key_findings.append(f"Vehicular score for the 3-month period: {_fmt(q_pool,1)} (overall score: {_fmt(q_overall,1)}).")
    if bonus_sentence:
        key_findings.append(bonus_sentence)

    if consistently_low:
        key_findings.append("Below-target areas seen repeatedly across the 3 months:")
        for kpi in consistently_low:
            key_findings.append(f"- {kpi}: {_impact_text(kpi)}")
    else:
        key_findings.append("No vehicular KPI was repeatedly below target across the 3 months.")

    if improved:
        key_findings.append(f"Areas that improved over the 3 months: {', '.join(improved[:3])}.")
    if worsened:
        key_findings.append(f"Areas that got worse over the 3 months: {', '.join(worsened[:3])}.")

    actions = _unique_actions(consistently_low)

    decision_triggers: List[Dict[str, str]] = []
    if len(consistently_low) >= 2:
        decision_triggers.append({
            "title": "Vehicle checks/driving need attention",
            "description": "Two or more vehicle-related measures were below target in at least 2 of the last 3 months.",
        })

    return {
        "generated_at": datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
        "summary": summary,
        "key_findings": key_findings,
        "recommended_actions": actions,
        "decision_triggers": decision_triggers,
        "meta": {
            "trade_group": trade_group,
            "trade_filter": trade_filter,
            "quarter_months": quarter_months,
        },
        "diagnostics": {
            "monthly_scores": month_scores,
            "consistently_low_counts": low_counts,
            "quarter_aggregate": {
                "vehicular_pool_score": q_pool,
                "overall_score": q_overall,
                "bonus": {"pot": q_pot, "multiplier": q_mult, "bonus_value": q_bonus_val, "band": q_band},
            },
        },
    }