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
