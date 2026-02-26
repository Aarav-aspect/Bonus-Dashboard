import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/layout/Header';
import PerformanceSummary from '../components/dashboard/PerformanceSummary';
import CategoryBlock from '../components/dashboard/CategoryBlock';
import { SummarySkeleton, CategorySkeleton } from '../components/common/Skeleton';
import { fetchMonths, fetchTradeGroups, fetchTradeSubgroups, fetchDashboard } from '../api';
import { Loader2, TrendingUp } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import PerformanceTrend from '../components/dashboard/PerformanceTrend';
import InitialLoader from '../components/common/InitialLoader';

function HistoricPerformance() {
    const { user } = useAuth();
    const [months, setMonths] = useState([]);
    const [tradeGroups, setTradeGroups] = useState({});
    const [tradeSubgroups, setTradeSubgroups] = useState({});

    const [selectedMonth, setSelectedMonth] = useState("");
    const [selectedGroup, setSelectedGroup] = useState("");
    const [selectedFilter, setSelectedFilter] = useState("All");

    const [data, setData] = useState(null);
    const [trendData, setTrendData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [trendLoading, setTrendLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        async function loadMeta() {
            try {
                const [mdata, gdata, sdata] = await Promise.all([
                    fetchMonths(),
                    fetchTradeGroups(),
                    fetchTradeSubgroups()
                ]);

                // Filter out the current month for the Historic view
                const historicMonths = mdata.slice(1);
                setMonths(historicMonths);
                setTradeGroups(gdata);
                setTradeSubgroups(sdata);

                // Default to the most recent historic month
                if (historicMonths.length > 0) {
                    setSelectedMonth(historicMonths[0]);
                }

                // If user has an assigned group, prioritize it.
                // Otherwise fall back to the first available group.
                if (user?.assigned_group && gdata[user.assigned_group]) {
                    setSelectedGroup(user.assigned_group);
                } else {
                    const groups = Object.keys(gdata);
                    if (groups.length > 0) setSelectedGroup(groups[0]);
                }

                // If user has an assigned trade, pre-select it as well.
                if (user?.assigned_trade) {
                    setSelectedFilter(user.assigned_trade);
                }

            } catch (err) {
                console.error(err);
                setError("Failed to load application metadata.");
            }
        }
        loadMeta();
    }, [user]);

    useEffect(() => {
        if (!selectedMonth || !selectedGroup) return;

        async function loadDashboard() {
            setLoading(true);
            setError(null);
            try {
                const result = await fetchDashboard(selectedMonth, selectedGroup, selectedFilter);
                setData(result);
            } catch (err) {
                console.error(err);
                setError("Failed to load historic data.");
            } finally {
                setLoading(false);
            }
        }

        loadDashboard();
    }, [selectedMonth, selectedGroup, selectedFilter]);

    // Load Trend Data
    useEffect(() => {
        if (months.length === 0 || !selectedGroup) return;

        async function loadTrend() {
            setTrendLoading(true);
            try {
                // Fetch last 12 months for the trend, in chronological order (oldest to newest)
                const monthsToFetch = [...months].slice(0, 12).reverse();
                const results = await Promise.all(
                    monthsToFetch.map(m => fetchDashboard(m, selectedGroup, selectedFilter))
                );

                const formatted = results.map((res, i) => ({
                    month: monthsToFetch[i],
                    "Bonus Percentage (%)": res.overall_score || 0
                }));

                setTrendData(formatted);
            } catch (err) {
                console.error("Trend load failed", err);
            } finally {
                setTrendLoading(false);
            }
        }
        loadTrend();
    }, [months, selectedGroup, selectedFilter]);

    const handleGroupChange = (grp) => {
        setSelectedGroup(grp);
        setSelectedFilter("All");
    };

    if (!selectedMonth) return <InitialLoader text="Accessing Archives..." />;

    const currentSubgroups = tradeSubgroups[selectedGroup] || {};

    return (
        <div className="min-h-screen bg-white pb-20 relative font-sans">
            {/* Global Refetch Spinner */}
            {loading && data && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/40 backdrop-blur-[2px] pointer-events-none animate-in fade-in duration-300">
                    <div className="bg-white p-6 rounded-3xl shadow-2xl border border-black/5 flex flex-col items-center gap-4">
                        <Loader2 className="w-10 h-10 text-primary animate-spin" />
                        <span className="text-sm font-semibold text-primary">Updating data...</span>
                    </div>
                </div>
            )}

            <div className="container mx-auto px-6 py-8">
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
                    showMonthFilter={true}
                />

                <div className="flex items-center gap-4 mb-8">
                    <h1 className="text-3xl font-black text-foreground tracking-tight">
                        Historic Performance
                    </h1>
                    <div className="bg-brand-blue/10 text-brand-blue px-3 py-1 rounded-full text-xs font-black uppercase tracking-widest">
                        Archive
                    </div>
                </div>

                {error && (
                    <div className="bg-destructive/15 text-destructive p-5 rounded-2xl mb-10 border border-destructive/20 font-bold flex items-center gap-3">
                        <span className="text-xl">⚠️</span>
                        {error}
                    </div>
                )}

                {loading && !data && (
                    <main>
                        <SummarySkeleton />
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 items-start">
                            {[...Array(5)].map((_, i) => <CategorySkeleton key={i} />)}
                        </div>
                    </main>
                )}

                {data && (
                    <main className={`animate-in fade-in duration-500 ${loading ? 'opacity-40 grayscale-[50%] blur-[1px] transition-all duration-300' : ''}`}>

                        {/* Performance Trend Chart */}
                        <div className="mb-10">
                            <PerformanceTrend
                                data={trendData}
                                loading={trendLoading}
                                onMonthSelect={(m) => setSelectedMonth(m)}
                            />
                        </div>

                        <PerformanceSummary
                            overallScore={data.overall_score}
                            bonus={data.bonus}
                            showTitle={false}
                        />

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 items-start">
                            {/* Logical groupings based on category names */}
                            {["Conversion", "Procedural", "Satisfaction", "Vehicular", "Productivity"].map(catName => (
                                data.categories[catName] && (
                                    <CategoryBlock
                                        key={catName}
                                        title={catName}
                                        kpis={data.categories[catName]}
                                        kpiScores={data.kpi_scores}
                                        categoryScore={data.category_scores[catName]}
                                        bonusPot={data.bonus?.bonus_value || 0}
                                        basePot={data.bonus?.pot || 0}
                                        overallScore={data.overall_score}
                                    />
                                )
                            ))}
                        </div>
                    </main>
                )}
            </div>
        </div>
    );
}

export default HistoricPerformance;
