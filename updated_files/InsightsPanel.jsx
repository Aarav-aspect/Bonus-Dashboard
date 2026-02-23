// InsightsPanel.jsx (UPDATED)
// - Works with pool filter coming from the backend (api.py sends pool-filtered insights)
// - Uses the new backend "change_text" strings when present (simple wording)
// - Falls back safely if a pool doesn't exist

import React, { useMemo } from "react";
import { AlertTriangle, CheckCircle2 } from "lucide-react";

const Badge = ({ children, tone = "gray" }) => {
  const tones = {
    gray: "bg-gray-50 border-gray-200 text-gray-700",
    red: "bg-red-50 border-red-200 text-red-700",
    amber: "bg-amber-50 border-amber-200 text-amber-700",
    green: "bg-emerald-50 border-emerald-200 text-emerald-700",
    blue: "bg-blue-50 border-blue-200 text-blue-700",
  };
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold border ${
        tones[tone] || tones.gray
      }`}
    >
      {children}
    </span>
  );
};

const SectionCard = ({ title, icon, children }) => (
  <div className="rounded-2xl border border-gray-200 bg-white overflow-hidden">
    <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-3">
      <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
        {icon}
      </div>
      <div className="font-bold text-gray-900">{title}</div>
    </div>
    <div className="p-5">{children}</div>
  </div>
);

const FindingRow = ({ idx, text }) => (
  <div className="flex items-start gap-3 py-3 border-b border-gray-100 last:border-b-0">
    <div className="shrink-0 w-7 h-7 rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-700 text-xs font-extrabold">
      {idx}
    </div>
    <div className="text-sm text-gray-700 leading-relaxed">{text}</div>
  </div>
);

const ActionRow = ({ level = "MEDIUM", text }) => {
  const tone =
    level === "HIGH"
      ? "bg-red-50 border-red-200 text-red-800"
      : level === "LOW"
      ? "bg-emerald-50 border-emerald-200 text-emerald-800"
      : "bg-amber-50 border-amber-200 text-amber-900";

  const badgeTone =
    level === "HIGH" ? "red" : level === "LOW" ? "green" : "amber";

  return (
    <div className={`rounded-xl border px-4 py-3 flex items-start gap-3 ${tone}`}>
      <Badge tone={badgeTone}>{level}</Badge>
      <div className="text-sm font-medium leading-relaxed">{text}</div>
    </div>
  );
};

const TriggerRow = ({ title, description }) => (
  <div className="rounded-xl border border-gray-200 bg-white px-4 py-3">
    <div className="flex items-start gap-3">
      <CheckCircle2 className="w-5 h-5 text-emerald-600 mt-0.5" />
      <div>
        <div className="font-semibold text-gray-900 text-sm">{title}</div>
        {description ? (
          <div className="text-xs text-gray-600 mt-1">{description}</div>
        ) : null}
      </div>
    </div>
  </div>
);

export default function InsightsPanel({ insights, data, poolName = "Conversion" }) {
  if (!data && !insights) return null;

  const effectivePool = poolName || "Conversion";

  const qRoot = insights?.quarterly || {};
  const qPools = qRoot?.pools || {};

  // If API filtered to a single pool, qPools may only have that key.
  // Pick the requested pool if present, else pick the first available pool, else {}.
  const qPool = useMemo(() => {
    if (qPools?.[effectivePool]) return qPools[effectivePool];
    const keys = Object.keys(qPools || {});
    if (keys.length) return qPools[keys[0]];
    return {};
  }, [qPools, effectivePool]);

  // meta
  const metaMonth =
    qRoot?.meta?.month ||
    insights?.meta?.month ||
    data?.meta?.month ||
    "-";

  const metaTradeGroup =
    qRoot?.meta?.trade_group ||
    insights?.meta?.trade_group ||
    data?.meta?.trade_group ||
    "-";

  const metaFilter =
    qRoot?.meta?.trade_filter ||
    insights?.meta?.trade_filter ||
    data?.meta?.trade_filter ||
    "-";

  const analysedMonths = useMemo(() => {
    const arr =
      qPool?.meta?.quarter_months ||
      qRoot?.meta?.quarter_months ||
      [];
    return Array.isArray(arr) ? arr : [];
  }, [qPool, qRoot]);

  const analysedLabel = analysedMonths.length
    ? analysedMonths.join(", ")
    : "Last 3 completed months";

  const generatedAt = qPool?.generated_at || qPool?.generatedAt || "-";

  const summary =
    qPool?.summary ||
    "Quarterly insights are not available yet.";

  const keyFindings = useMemo(() => {
    const kf = qPool?.key_findings || qPool?.keyFindings;
    return Array.isArray(kf) ? kf : [];
  }, [qPool]);

  const actions = useMemo(() => {
    const ra = qPool?.recommended_actions || qPool?.recommendedActions;
    return Array.isArray(ra) ? ra : [];
  }, [qPool]);

  const triggers = useMemo(() => {
    const dt = qPool?.decision_triggers || qPool?.decisionTriggers;
    return Array.isArray(dt) ? dt : [];
  }, [qPool]);

  return (
    <div className="mt-6 space-y-6">
      <SectionCard
        title={`3-Month Analysis — ${effectivePool}`}
        icon={<AlertTriangle className="w-5 h-5" />}
      >
        <div className="text-xs text-gray-500 mb-3">
          Generated {generatedAt} • Anchor month: {metaMonth} • {metaTradeGroup} • {metaFilter}
        </div>

        <div className="mb-3">
          <Badge tone="blue">Months analysed: {analysedLabel}</Badge>
        </div>

        <div className="text-sm text-gray-700 leading-relaxed">
          {summary}
        </div>
      </SectionCard>

      {/* Key Findings */}
      <div className="rounded-2xl border border-gray-200 bg-white overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 font-bold text-gray-900">
          Key Findings
        </div>
        <div className="px-5">
          {keyFindings.length ? (
            keyFindings.map((t, i) => (
              <FindingRow key={`kf-${i}`} idx={i + 1} text={t} />
            ))
          ) : (
            <div className="py-5 text-sm text-gray-500">
              No key findings available yet.
            </div>
          )}
        </div>
      </div>

      {/* Recommended Actions */}
      <div className="rounded-2xl border border-gray-200 bg-white overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 font-bold text-gray-900">
          Recommended Actions
        </div>
        <div className="p-5 space-y-3">
          {actions.length ? (
            actions.map((a, i) => (
              <ActionRow
                key={`act-${i}`}
                level={(a?.level || a?.priority || "MEDIUM").toUpperCase()}
                text={a?.text || a?.message || String(a)}
              />
            ))
          ) : (
            <div className="text-sm text-gray-500">
              No actions available yet.
            </div>
          )}
        </div>
      </div>

      {/* Decision Triggers */}
      <div className="rounded-2xl border border-red-200 bg-red-50/60 overflow-hidden">
        <div className="px-5 py-4 border-b border-red-200 flex items-center gap-2 font-bold text-red-900">
          <AlertTriangle className="w-5 h-5 text-red-600" />
          Decision Triggers
        </div>
        <div className="p-5 space-y-3">
          {triggers.length ? (
            triggers.map((t, i) => (
              <TriggerRow
                key={`tr-${i}`}
                title={t?.title || String(t)}
                description={t?.description || t?.detail || ""}
              />
            ))
          ) : (
            <div className="text-sm text-red-800/80">
              No triggers activated.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}