# insights/engine.py
from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from insights.pools.conversion import build_conversion_quarterly_insights
from insights.pools.productivity import build_productivity_quarterly_insights
from insights.pools.vehicular import build_vehicular_quarterly_insights
from insights.pools.satisfaction import build_satisfaction_quarterly_insights
from insights.pools.procedural import build_procedural_quarterly_insights

logger = logging.getLogger(__name__)

# Engine Logic
def build_all_quarterly_insights(
    trade_group: str,
    trade_filter: str,
    quarter_months: List[str],
    month_payloads: List[Dict[str, Any]],
    quarter_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compile insights for all performance pools."""
    
    # Run each pool's insight builder
    args = {
        "trade_group": trade_group,
        "trade_filter": trade_filter,
        "quarter_months": quarter_months,
        "month_payloads": month_payloads,
        "quarter_result": quarter_result,
    }

    try:
        return {
            "conversion": build_conversion_quarterly_insights(**args),
            "productivity": build_productivity_quarterly_insights(**args),
            "vehicular": build_vehicular_quarterly_insights(**args),
            "satisfaction": build_satisfaction_quarterly_insights(**args),
            "procedural": build_procedural_quarterly_insights(**args),
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
    except Exception as e:
        logger.error(f"Error building aggregate insights: {e}", exc_info=True)
        return {"error": str(e)}