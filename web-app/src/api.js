const API_BASE = ""; // Relative paths for production usage (served by same backend)

export async function fetchTradeGroups() {
    const res = await fetch(`${API_BASE}/meta/trade-groups`, {
        credentials: "include"
    });
    if (!res.ok) throw new Error("Failed to fetch trade groups");
    return res.json();
}

export async function fetchTradeSubgroups() {
    const res = await fetch(`${API_BASE}/meta/trade-subgroups`, {
        credentials: "include"
    });
    if (!res.ok) throw new Error("Failed to fetch trade subgroups");
    return res.json();
}

export async function fetchMonths() {
    const res = await fetch(`${API_BASE}/meta/months`, {
        credentials: "include"
    });
    if (!res.ok) throw new Error("Failed to fetch months");
    return res.json();
}

export async function fetchDashboard(month, tradeGroup, tradeFilter) {
    const res = await fetch(`${API_BASE}/api/dashboard`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
            month,
            trade_group: tradeGroup,
            trade_filter: tradeFilter === "All" ? null : tradeFilter,
        }),
    });
    if (!res.ok) throw new Error("Failed to fetch dashboard data");
    return res.json();
}

export async function fetchBonusPots() {
    const res = await fetch(`${API_BASE}/config/bonus-pots`, {
        credentials: "include"
    });
    if (!res.ok) throw new Error("Failed to fetch bonus pots");
    return res.json();
}

export async function saveBonusPots(pots) {
    const res = await fetch(`${API_BASE}/config/bonus-pots`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(pots),
    });
    if (!res.ok) throw new Error("Failed to save bonus pots");
    return res.json();
}

export async function fetchKPIConfig() {
    const res = await fetch(`${API_BASE}/config/kpi-config`, {
        credentials: "include"
    });
    if (!res.ok) throw new Error("Failed to fetch KPI config");
    return res.json();
}

export async function saveKPIConfig(config) {
    const res = await fetch(`${API_BASE}/config/kpi-config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error("Failed to save KPI config");
    return res.json();
}

export async function updateDynamicThreshold(kpiName, tradeGroup, thresholds) {
    const res = await fetch(`${API_BASE}/config/thresholds/dynamic/${encodeURIComponent(kpiName)}?trade_group=${encodeURIComponent(tradeGroup)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(thresholds),
    });
    if (!res.ok) throw new Error("Failed to update dynamic threshold");
    return res.json();
}

export async function updateDynamicThresholdAll(kpiName, thresholds) {
    const res = await fetch(`${API_BASE}/config/thresholds/dynamic/${encodeURIComponent(kpiName)}/all`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(thresholds),
    });
    if (!res.ok) throw new Error("Failed to update dynamic threshold for all groups");
    return res.json();
}

// ------------------------------------------------------------------
// AUTH API
// ------------------------------------------------------------------

export async function fetchSession() {
    const res = await fetch(`${API_BASE}/api/auth/session`, {
        credentials: "include"
    });
    if (!res.ok) return null;
    return res.json(); // Returns { user: { ... } } or { user: null }
}

export async function signOut() {
    const res = await fetch(`${API_BASE}/api/auth/signout`, {
        method: "POST",
        credentials: "include"
    });

    if (res.ok) {
        const data = await res.json();
        // Redirect to Microsoft logout for full SSO signout
        if (data.logout_url) {
            window.location.href = data.logout_url;
            return;
        }
    }

    // Fallback: redirect to login
    window.location.href = "/";
}

export async function fetchDriverScores(tradeGroup, tradeFilter = "All") {
    const res = await fetch(`${API_BASE}/api/drilldown/drivers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ trade_group: tradeGroup, trade_filter: tradeFilter }),
    });
    if (!res.ok) throw new Error("Failed to fetch driver scores");
    return res.json();
}

export async function fetchDrilldownConfig() {
    const res = await fetch(`${API_BASE}/config/drilldown`, {
        credentials: "include"
    });
    if (!res.ok) throw new Error("Failed to fetch drilldown config");
    return res.json();
}

export async function fetchReviewDetails(tradeGroup, month, tradeFilter = "All") {
    const res = await fetch(`${API_BASE}/api/drilldown/reviews`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ trade_group: tradeGroup, month, trade_filter: tradeFilter }),
    });
    if (!res.ok) throw new Error("Failed to fetch review details");
    return res.json();
}

export async function fetchOpsList(tradeGroup, tradeFilter = "All") {
    const res = await fetch(`${API_BASE}/api/drilldown/ops-list`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ trade_group: tradeGroup, trade_filter: tradeFilter }),
    });
    if (!res.ok) throw new Error("Failed to fetch ops list");
    return res.json();
}

export async function fetchUnclosedSAs(tradeGroup, month, tradeFilter = "All") {
    const res = await fetch(`${API_BASE}/api/drilldown/unclosed-sas`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ trade_group: tradeGroup, month, trade_filter: tradeFilter }),
    });
    if (!res.ok) throw new Error("Failed to fetch unclosed SAs");
    return res.json();
}

export async function fetchCallbackJobs(tradeGroup, month, tradeFilter = "All") {
    const res = await fetch(`${API_BASE}/api/drilldown/callback-jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ trade_group: tradeGroup, month, trade_filter: tradeFilter }),
    });
    if (!res.ok) throw new Error("Failed to fetch callback jobs");
    return res.json();
}

export async function fetchReactive6Plus(tradeGroup, month, tradeFilter = "All") {
    const res = await fetch(`${API_BASE}/api/drilldown/reactive-6plus`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ trade_group: tradeGroup, month, trade_filter: tradeFilter }),
    });
    if (!res.ok) throw new Error("Failed to fetch reactive 6+ data");
    return res.json();
}

export async function fetchTqrNotSatisfied(tradeGroup, month, tradeFilter = "All") {
    const res = await fetch(`${API_BASE}/api/drilldown/tqr-not-satisfied`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ trade_group: tradeGroup, month, trade_filter: tradeFilter }),
    });
    if (!res.ok) throw new Error("Failed to fetch TQR not satisfied data");
    return res.json();
}

export async function fetchLateToSite(tradeGroup, month, tradeFilter = "All") {
    const res = await fetch(`${API_BASE}/api/drilldown/late-to-site`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ trade_group: tradeGroup, month, trade_filter: tradeFilter }),
    });
    if (!res.ok) throw new Error("Failed to fetch late to site data");
    return res.json();
}

export async function fetchCases(tradeGroup, month, tradeFilter = "All") {
    const res = await fetch(`${API_BASE}/api/drilldown/cases`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ trade_group: tradeGroup, month, trade_filter: tradeFilter }),
    });
    if (!res.ok) throw new Error("Failed to fetch cases");
    return res.json();
}
