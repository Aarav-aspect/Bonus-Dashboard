// Insights.jsx (UPDATED)
// - Sends `pool` to backend so backend filters insights
// - Dropdown shows fixed list of pools (matches backend)
// - When "All" is selected, backend returns all pools; panel defaults to Conversion view

import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import { SummarySkeleton } from '../components/Skeleton';
import { fetchMonths, fetchTradeGroups, fetchTradeSubgroups, fetchDashboard } from '../api';
import { Loader2 } from 'lucide-react';
import InsightsPanel from '../components/InsightsPanel';
import { Button } from "@/components/ui/button";

const POOL_OPTIONS = ["All", "Conversion", "Satisfaction", "Productivity", "Procedural", "Vehicular"];

function Insights() {
  const [months, setMonths] = useState([]);
  const [tradeGroups, setTradeGroups] = useState({});
  const [tradeSubgroups, setTradeSubgroups] = useState({});

  const [selectedMonth, setSelectedMonth] = useState("");
  const [selectedGroup, setSelectedGroup] = useState("");
  const [selectedFilter, setSelectedFilter] = useState("All");

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // ✅ page-level pool filter
  const [selectedInsightsPool, setSelectedInsightsPool] = useState("All");

  useEffect(() => {
    async function loadMeta() {
      try {
        const [mdata, gdata, sdata] = await Promise.all([
          fetchMonths(),
          fetchTradeGroups(),
          fetchTradeSubgroups()
        ]);

        setMonths(mdata);
        setTradeGroups(gdata);
        setTradeSubgroups(sdata);

        if (mdata.length > 0) setSelectedMonth(mdata[0]);
        const groups = Object.keys(gdata);
        if (groups.length > 0) setSelectedGroup(groups[0]);
      } catch (err) {
        console.error(err);
        setError("Failed to load application metadata.");
      }
    }
    loadMeta();
  }, []);

  useEffect(() => {
    if (!selectedMonth || !selectedGroup) return;

    async function loadInsights() {
      setLoading(true);
      setError(null);
      try {
        // ✅ pass pool to backend so it returns only that pool (or All)
        const result = await fetchDashboard(
          selectedMonth,
          selectedGroup,
          selectedFilter,
          selectedInsightsPool
        );
        setData(result);
      } catch (err) {
        console.error(err);
        setError("Failed to load insights data.");
      } finally {
        setLoading(false);
      }
    }

    loadInsights();
  }, [selectedMonth, selectedGroup, selectedFilter, selectedInsightsPool]);

  const handleGroupChange = (grp) => {
    setSelectedGroup(grp);
    setSelectedFilter("All");
  };

  // If "All" chosen, show Conversion in the panel by default (UI decision)
  const activeQuarterlyPool = useMemo(() => {
    if (!selectedInsightsPool || selectedInsightsPool === "All") return "Conversion";
    return selectedInsightsPool;
  }, [selectedInsightsPool]);

  const currentSubgroups = tradeSubgroups[selectedGroup] || {};

  if (!selectedMonth) {
    return (
      <div className="flex flex-col gap-4 justify-center items-center h-screen bg-white">
        <Loader2 className="w-10 h-10 text-primary animate-spin" />
        <span className="text-sm font-medium text-muted-foreground animate-pulse">
          Initializing Insights...
        </span>
      </div>
    );
  }

  const insightsObj = data?.insights || {};

  return (
    <div className="min-h-screen bg-white pb-20 relative">
      {loading && data && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/40 backdrop-blur-[2px] pointer-events-none animate-in fade-in duration-300">
          <div className="bg-white p-6 rounded-3xl shadow-2xl border border-border flex flex-col items-center gap-4">
            <Loader2 className="w-10 h-10 text-primary animate-spin" />
            <span className="text-sm font-semibold text-primary">
              Updating your insights...
            </span>
          </div>
        </div>
      )}

      <div className="container mx-auto px-6 py-8">
        <div className="flex justify-end mb-6">
          <Link to="/">
            <Button
              variant="outline"
              className="font-bold border-input hover:border-brand-blue hover:text-brand-blue transition-all"
            >
              ← Back to Dashboard
            </Button>
          </Link>
        </div>

        <Header
          months={months}
          tradeGroups={tradeGroups}
          selectedMonth={selectedMonth}
          selectedGroup={selectedGroup}
          selectedFilter={selectedFilter}
          onMonthChange={setSelectedMonth}
          onGroupChange={handleGroupChange}
          onFilterChange={setSelectedFilter}
          availableSubgroups={currentSubgroups}
        />

        {error && (
          <div className="bg-destructive/15 text-destructive p-5 rounded-2xl mb-10 border border-destructive/20 font-bold flex items-center gap-3">
            <span className="text-xl">⚠️</span>
            {error}
          </div>
        )}

        {loading && !data && (
          <main>
            <SummarySkeleton />
          </main>
        )}

        {data && (
          <main className={`animate-in fade-in duration-500 ${loading ? 'opacity-40 grayscale-[50%] blur-[1px] transition-all duration-300' : ''}`}>
            <div className="flex items-center justify-between gap-4 mb-6">
              <h1 className="text-3xl font-bold">Insights</h1>

              {/* ✅ Pool dropdown */}
              <select
                value={selectedInsightsPool}
                onChange={(e) => setSelectedInsightsPool(e.target.value)}
                className="border border-gray-200 rounded-xl px-3 py-2 text-sm bg-white shadow-sm"
              >
                {POOL_OPTIONS.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>

            <InsightsPanel
              insights={insightsObj}
              data={data}
              poolName={activeQuarterlyPool}
            />
          </main>
        )}
      </div>
    </div>
  );
}

export default Insights;