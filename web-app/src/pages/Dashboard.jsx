import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/layout/Header';
import PerformanceSummary from '../components/dashboard/PerformanceSummary';
import CategoryBlock from '../components/dashboard/CategoryBlock';
import { SummarySkeleton, CategorySkeleton } from '../components/common/Skeleton';
import { fetchMonths, fetchTradeGroups, fetchTradeSubgroups, fetchDashboard, fetchKPIConfig, fetchDrilldownConfig } from '../api';
import { colors } from '../constants/colors';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import InitialLoader from '../components/common/InitialLoader';

function Dashboard() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [months, setMonths] = useState([]);
    const [tradeGroups, setTradeGroups] = useState({});
    const [tradeSubgroups, setTradeSubgroups] = useState({});
    const [kpiConfig, setKpiConfig] = useState({});
    const [drilldownConfig, setDrilldownConfig] = useState({});

    const [selectedMonth, setSelectedMonth] = useState("");
    const [selectedGroup, setSelectedGroup] = useState("");
    const [selectedFilter, setSelectedFilter] = useState("All");

    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);


    useEffect(() => {
        async function loadMeta() {
            try {
                const [mdata, gdata, sdata, kdata, ddata] = await Promise.all([
                    fetchMonths(),
                    fetchTradeGroups(),
                    fetchTradeSubgroups(),
                    fetchKPIConfig(),
                    fetchDrilldownConfig()
                ]);

                setMonths(mdata);
                setTradeGroups(gdata);
                setTradeSubgroups(sdata);
                setKpiConfig(kdata);
                setDrilldownConfig(ddata);

                if (mdata.length > 0) {
                    setSelectedMonth(mdata[0]);
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
                setError("Failed to load dashboard data.");
            } finally {
                setLoading(false);
            }
        }

        loadDashboard();
    }, [selectedMonth, selectedGroup, selectedFilter]);


    const handleGroupChange = (grp) => {
        setSelectedGroup(grp);
        setSelectedFilter("All");
    };

    if (!selectedMonth || loading && !data) return <InitialLoader text="Preparing Your Dashboard..." />;
    if (loading) return <InitialLoader text="Updating your data..." />;

    const currentSubgroups = tradeSubgroups[selectedGroup] || {};

    return (
        <div className="min-h-screen bg-white pb-20 relative">


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
                    showMonthFilter={false}
                />

                {error && (
                    <div className="bg-destructive/15 text-destructive p-5 rounded-2xl mb-10 border border-destructive/20 font-bold flex items-center gap-3">
                        <span className="text-xl">⚠️</span>
                        {error}
                    </div>
                )}



                {data && (
                    <main className={`animate-in fade-in duration-500 ${loading ? 'opacity-40 grayscale-[50%] blur-[1px] transition-all duration-300' : ''}`}>
                        <PerformanceSummary
                            overallScore={data.overall_score}
                            bonus={data.bonus}
                            liveCollections={data.live_collections}
                            liveLabour={data.live_labour}
                            liveMaterials={data.live_materials}
                        />

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 items-start">

                            {/* Column 1 */}
                            <div className="flex flex-col gap-8">
                                {data.categories["Conversion"] && (
                                    <CategoryBlock
                                        title="Conversion"
                                        kpis={data.categories["Conversion"]}
                                        kpiScores={data.kpi_scores}
                                        categoryScore={data.category_scores["Conversion"]}
                                        bonusPot={data.bonus?.bonus_value || 0}
                                        basePot={data.bonus?.pot || 0}
                                        overallScore={data.overall_score}
                                        kpiConfig={kpiConfig}
                                        activeTrade={selectedFilter}
                                        tradeGroup={selectedGroup}
                                        drilldownConfig={drilldownConfig}
                                        selectedMonth={selectedMonth}
                                    />
                                )}
                                {data.categories["Procedural"] && (
                                    <CategoryBlock
                                        title="Procedural"
                                        kpis={data.categories["Procedural"]}
                                        kpiScores={data.kpi_scores}
                                        categoryScore={data.category_scores["Procedural"]}
                                        bonusPot={data.bonus?.bonus_value || 0}
                                        basePot={data.bonus?.pot || 0}
                                        overallScore={data.overall_score}
                                        kpiConfig={kpiConfig}
                                        activeTrade={selectedFilter}
                                        tradeGroup={selectedGroup}
                                        drilldownConfig={drilldownConfig}
                                        selectedMonth={selectedMonth}
                                    />
                                )}
                            </div>

                            {/* Column 2 */}
                            <div className="flex flex-col gap-8">
                                {data.categories["Satisfaction"] && (
                                    <CategoryBlock
                                        title="Satisfaction"
                                        kpis={data.categories["Satisfaction"]}
                                        kpiScores={data.kpi_scores}
                                        categoryScore={data.category_scores["Satisfaction"]}
                                        bonusPot={data.bonus?.bonus_value || 0}
                                        basePot={data.bonus?.pot || 0}
                                        overallScore={data.overall_score}
                                        kpiConfig={kpiConfig}
                                        activeTrade={selectedFilter}
                                        tradeGroup={selectedGroup}
                                        drilldownConfig={drilldownConfig}
                                        selectedMonth={selectedMonth}
                                    />
                                )}
                                {data.categories["Vehicular"] && (
                                    <CategoryBlock
                                        title="Vehicular"
                                        kpis={data.categories["Vehicular"]}
                                        kpiScores={data.kpi_scores}
                                        categoryScore={data.category_scores["Vehicular"]}
                                        bonusPot={data.bonus?.bonus_value || 0}
                                        basePot={data.bonus?.pot || 0}
                                        overallScore={data.overall_score}
                                        kpiConfig={kpiConfig}
                                        activeTrade={selectedFilter}
                                        tradeGroup={selectedGroup}
                                        drilldownConfig={drilldownConfig}
                                        selectedMonth={selectedMonth}
                                    />
                                )}
                            </div>

                            {/* Column 3 */}
                            <div className="flex flex-col gap-8">
                                {data.categories["Productivity"] && (
                                    <CategoryBlock
                                        title="Productivity"
                                        kpis={data.categories["Productivity"]}
                                        kpiScores={data.kpi_scores}
                                        categoryScore={data.category_scores["Productivity"]}
                                        bonusPot={data.bonus?.bonus_value || 0}
                                        basePot={data.bonus?.pot || 0}
                                        overallScore={data.overall_score}
                                        kpiConfig={kpiConfig}
                                        activeTrade={selectedFilter}
                                        tradeGroup={selectedGroup}
                                        drilldownConfig={drilldownConfig}
                                        selectedMonth={selectedMonth}
                                    />
                                )}
                            </div>

                        </div>
                    </main>
                )}
            </div>
        </div>
    );
}

export default Dashboard;
