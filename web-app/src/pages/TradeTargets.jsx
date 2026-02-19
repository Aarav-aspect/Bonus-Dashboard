import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchMonths, fetchTradeGroups, fetchTradeSubgroups, fetchKPIConfig, fetchBonusPots, fetchDashboard } from '../api';
import Header from '../components/Header';
import { useAuth } from '../context/AuthContext';

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";

// Simple three-band model used to explain
// how the bonus pot changes with overall performance.
const BONUS_BANDS = [
    {
        id: 'below',
        label: 'Below targets',
        badge: 'Gap',
        badgeFull: 'Below targets',
        min: 0,
        max: 59,
        adjustment: -0.3,
        color: 'text-destructive', // brand.error
        bg: 'bg-destructive/10',     // brand.error.subtle
        borderColor: 'border-destructive/20'
    },
    {
        id: 'meets',
        label: 'Meets targets',
        badge: 'Target',
        badgeFull: 'Meets targets',
        min: 60,
        max: 79,
        adjustment: 0,
        color: 'text-yellow-600', // brand.warning
        bg: 'bg-yellow-50',     // brand.warning.subtle
        borderColor: 'border-yellow-200'
    },
    {
        id: 'exceeds',
        label: 'Exceeds targets',
        badge: 'Stretch',
        badgeFull: 'Exceeds targets',
        min: 80,
        max: 100,
        adjustment: 0.15,
        color: 'text-support-green', // brand.support.green
        bg: 'bg-green-50',
        borderColor: 'border-green-200'
    }
];

const formatCurrency = (value) => {
    if (value == null || isNaN(value)) return '£0';
    return value.toLocaleString('en-GB', {
        style: 'currency',
        currency: 'GBP',
        maximumFractionDigits: 0
    });
};

const TradeTargets = () => {
    const [months, setMonths] = useState([]);
    const [tradeGroups, setTradeGroups] = useState({});
    const [kpiConfig, setKpiConfig] = useState({});
    const [bonusPots, setBonusPots] = useState({});
    const [tradeSubgroups, setTradeSubgroups] = useState({});
    const [selectedMonth, setSelectedMonth] = useState("");
    const [selectedGroup, setSelectedGroup] = useState("");
    const [selectedFilter, setSelectedFilter] = useState("All");
    const [performanceData, setPerformanceData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeScoreTab, setActiveScoreTab] = useState("");

    useEffect(() => {
        async function loadMeta() {
            try {
                const [m, g, s, kpis, pots] = await Promise.all([
                    fetchMonths(),
                    fetchTradeGroups(),
                    fetchTradeSubgroups(),
                    fetchKPIConfig(),
                    fetchBonusPots()
                ]);
                setMonths(m);
                setTradeGroups(g);
                setTradeSubgroups(s);
                setKpiConfig(kpis);
                setBonusPots(pots);

                if (m.length > 0) {
                    setSelectedMonth(m[0]); // Default to latest month (current)
                }

                const groups = Object.keys(g);
                if (groups.length > 0) setSelectedGroup(groups[0]);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        }
        loadMeta();
    }, []);

    useEffect(() => {
        if (!selectedMonth || !selectedGroup) return;

        async function loadPerformance() {
            try {
                const result = await fetchDashboard(selectedMonth, selectedGroup, selectedFilter);
                setPerformanceData(result);
            } catch (err) {
                console.error("Failed to load performance data", err);
            }
        }
        loadPerformance();
    }, [selectedMonth, selectedGroup, selectedFilter]);

    const handleGroupChange = (grp) => {
        setSelectedGroup(grp);
        setSelectedFilter("All");
    };

    // Calculate dynamic hints based on performance data
    const getDynamicNote = (bandId) => {
        if (!performanceData || !performanceData.category_scores) {
            return bandId === 'below' ? 'Calculating your baseline...' : 'Loading recommendations...';
        }

        const scores = performanceData.category_scores;
        // Find categories that can be improved
        const sortedCats = Object.entries(scores)
            .filter(([_, score]) => score < 95) // Focus on categories with room for significant growth
            .sort((a, b) => a[1] - b[1]);

        if (bandId === 'below') return 'Where you are today.';

        if (sortedCats.length === 0) return 'You are at maximum performance across all categories!';

        const topImprovement = sortedCats[0][0];
        const nextImprovement = sortedCats.length > 1 ? sortedCats[1][0] : null;

        if (bandId === 'meets') {
            return `Reach this by improving ${topImprovement}${nextImprovement ? ' and ' + nextImprovement : ''}.`;
        }

        if (bandId === 'exceeds') {
            return `Max out ${topImprovement} to unlock the full bonus pot.`;
        }

        return '';
    };

    if (loading) return (
        <div className="min-h-screen flex items-center justify-center bg-white">
            <div className="text-muted-foreground font-bold animate-pulse">Loading Targets...</div>
        </div>
    );

    const basePotForSelectedGroup = bonusPots[selectedGroup] || 0;
    const currentScore = performanceData?.overall_score || 0;
    const currentBand = BONUS_BANDS.find(b => currentScore >= b.min && currentScore <= b.max) || BONUS_BANDS[0];
    const currentBonusValue = performanceData?.bonus?.bonus_value || (basePotForSelectedGroup * (1 + currentBand.adjustment));

    // Group KPIs by category (manual mapping matches Dashboard)
    const categories = {
        "Conversion": ["Estimate Production / Reactive Leads %", "Estimate Conversion %", "FOC Conversion Rate %", "Average Converted Estimate Value (£)"],
        "Procedural": ["TQR Ratio %", "TQR (Not Satisfied) Ratio %", "Unclosed SA %", "Reactive 6+ hours %"],
        "Satisfaction": ["Average Review Rating", "Review Ratio %", "Engineer Satisfaction %", "Cases %", "Engineer Retention %"],
        "Vehicular": ["Average Driving Score", "Drivers with <7 %", "VCR Update %"],
        "Productivity": ["Ops Count %", "Sales Target Achievement %", "Monthly Working Time (hrs)", "Callback Jobs %", "SA Attended", "Average Site Value (£)", "Late to Site %", "Absence %"]
    };

    const getThresholds = (kpiName) => {
        const cfg = kpiConfig[kpiName];
        if (!cfg) return null;

        if (cfg.dynamic && cfg.dynamic.thresholds_by_trade) {
            // Dynamic KPI
            let matchingTrade = null;

            // If we have a specific subgroup filter, try to find a representative trade for it
            if (selectedFilter !== "All") {
                const subgroupTrades = (tradeSubgroups[selectedGroup] && tradeSubgroups[selectedGroup][selectedFilter]) || [];
                matchingTrade = subgroupTrades.find(t => t in cfg.dynamic.thresholds_by_trade);
            }

            // Fallback or if "All" is selected: use first matching trade from the whole group
            if (!matchingTrade) {
                const tradeTrades = tradeGroups[selectedGroup] || [];
                matchingTrade = tradeTrades.find(t => t in cfg.dynamic.thresholds_by_trade);
            }

            if (matchingTrade) {
                const thresholds = cfg.dynamic.thresholds_by_trade[matchingTrade];
                const scores = cfg.dynamic.scores;
                return thresholds.map((t, i) => ({
                    min: t,
                    score: scores[i]
                }));
            }
            return "Dynamic / Multiple targets";
        }

        // Static
        return cfg.thresholds;
    };

    const scoreCategories = Object.entries(categories);

    return (
        <div className="min-h-screen bg-white pb-20 font-sans">
            <div className="container mx-auto px-6 py-8">

                {/* Unified Header */}
                <Header
                    months={months}
                    tradeGroups={tradeGroups}
                    selectedMonth={selectedMonth}
                    selectedGroup={selectedGroup}
                    selectedFilter={selectedFilter}
                    onMonthChange={setSelectedMonth}
                    onGroupChange={handleGroupChange}
                    onFilterChange={setSelectedFilter}
                    availableSubgroups={tradeSubgroups[selectedGroup] || {}}
                />

                <h1 className="text-3xl font-black text-foreground tracking-tight mb-8">
                    Target Overview
                </h1>




                {/* Three Scenarios Section */}
                <div className="mb-12">
                    {/* Intro Strip */}
                    <div className="px-6 py-4 bg-muted border border-black/5 border-b-0 rounded-t-2xl text-base font-medium text-foreground">
                        You are currently in the <strong className={currentBand.color}>{currentBand.label}</strong> band with a payout of <strong>{formatCurrency(currentBonusValue)}</strong>.
                    </div>

                    {/* Scenario Cards */}
                    <Card className="grid grid-cols-1 md:grid-cols-3 gap-0 overflow-hidden rounded-b-2xl rounded-t-none border-black/5 shadow-sm">
                        {BONUS_BANDS.map((band, idx) => {
                            const payout = basePotForSelectedGroup * (1 + band.adjustment);
                            const isCurrent = currentBand.id === band.id;

                            return (
                                <div key={band.id} className={`p-8 bg-white flex flex-col gap-4 relative ${idx !== 2 ? 'border-r border-black/5' : ''}`}>
                                    <div className="flex justify-between items-center">
                                        <h3 className="text-xl font-black text-foreground">
                                            {band.label}
                                        </h3>
                                        {isCurrent ? (
                                            <span className="text-[11px] font-bold px-3 py-1 rounded-full bg-foreground text-white uppercase tracking-wider">
                                                Current band
                                            </span>
                                        ) : (
                                            <span className={`text-[11px] font-bold px-3 py-1 rounded-full ${band.bg} ${band.color} uppercase tracking-wider`}>
                                                {band.badge} band
                                            </span>
                                        )}
                                    </div>

                                    <div className="text-sm text-muted-foreground font-medium">
                                        Score range: {band.min}–{band.max}%
                                    </div>

                                    <div className="flex flex-col gap-1">
                                        <div className="text-sm text-muted-foreground">
                                            Adjustment: <strong className={band.color}>{band.adjustment === 0 ? '0%' : `${band.adjustment > 0 ? '+' : ''}${(band.adjustment * 100).toFixed(0)}%`}</strong>
                                        </div>
                                        <div className="text-3xl font-black text-foreground">
                                            {formatCurrency(payout)}
                                        </div>
                                    </div>

                                    <p className={`text-xs mt-2 italic font-medium leading-relaxed ${isCurrent ? 'text-muted-foreground' : band.color}`}>
                                        {getDynamicNote(band.id)}
                                    </p>
                                </div>
                            );
                        })}
                    </Card>
                </div>

                {/* Score Breakdown Section */}
                <div className="mt-16">
                    <div className="mb-8 flex flex-col gap-2">
                        <div className="flex items-center gap-2">
                            <h2 className="text-2xl font-black text-foreground tracking-tight">
                                Score Breakdown for
                            </h2>
                            <Select value={activeScoreTab} onValueChange={setActiveScoreTab}>
                                <SelectTrigger className="w-auto min-w-[200px] h-10 px-0 border-0 bg-transparent text-2xl font-black text-brand-blue shadow-none focus:ring-0">
                                    <SelectValue placeholder="Pick a category" />
                                </SelectTrigger>
                                <SelectContent className="bg-white border-black/5 shadow-lg rounded-xl">
                                    <SelectItem value="All" className="font-bold text-foreground">All Categories</SelectItem>
                                    {Object.keys(categories).map(cat => (
                                        <SelectItem key={cat} value={cat} className="font-bold text-foreground">{cat}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        <p className="text-muted-foreground font-medium">
                            {activeScoreTab === "All"
                                ? "Overview of all KPI scoring thresholds."
                                : `Detailed KPI scoring thresholds for the ${activeScoreTab} category.`}
                        </p>
                    </div>

                    <div className="flex flex-col gap-8">
                        {scoreCategories
                            .filter(([cat]) => activeScoreTab === "All" || cat === activeScoreTab)
                            .map(([catName, kpis]) => (
                                <Card key={catName} className="shadow-sm border-black/5 overflow-hidden rounded-2xl">
                                    <div className="px-6 py-5 bg-white border-b border-black/5 flex items-center justify-between">
                                        <h3 className="text-base font-black text-foreground uppercase tracking-widest">
                                            {catName} Details
                                        </h3>
                                        <span className="text-xs font-bold text-muted-foreground">
                                            {kpis.length} KPIs
                                        </span>
                                    </div>

                                    <div className="overflow-x-auto">
                                        <table className="w-full text-left border-collapse min-w-[700px]">
                                            <thead>
                                                <tr className="bg-white border-b-2 border-muted">
                                                    <th className="px-6 py-5 text-xs font-bold text-muted-foreground uppercase tracking-wider w-[30%]">
                                                        KPI Name
                                                    </th>
                                                    {[100, 80, 60, 40, 20, 0].map(score => (
                                                        <th key={score} className="px-2 py-5 text-xs font-bold text-muted-foreground uppercase tracking-wider text-center">
                                                            {score} Pts
                                                        </th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {kpis.map((kpi, index) => {
                                                    const cfg = kpiConfig[kpi];
                                                    const direction = cfg ? (cfg.direction === 'higher_is_better' ? 'Higher ↑' : 'Lower ↓') : '';
                                                    const thresholds = getThresholds(kpi);

                                                    return (
                                                        <tr key={kpi} className="border-b border-black/5 last:border-0 hover:bg-muted/5 transition-colors">
                                                            <td className="px-6 py-5 align-middle">
                                                                <div className="font-bold text-foreground text-sm mb-1">{kpi}</div>
                                                                <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
                                                                    {direction}
                                                                </div>
                                                            </td>
                                                            {[100, 80, 60, 40, 20, 0].map((score, idx) => {
                                                                let cellContent = "-";
                                                                let cellClass = "text-muted-foreground bg-transparent";

                                                                if (Array.isArray(thresholds)) {
                                                                    const match = thresholds.find(t => t.score === score);
                                                                    if (match) {
                                                                        const isHighScore = score >= 80;
                                                                        const isMedScore = score >= 60;

                                                                        // Tailwind color mapping
                                                                        if (isHighScore) cellClass = "bg-green-100 text-green-700 border border-green-200";
                                                                        else if (isMedScore) cellClass = "bg-amber-50 text-amber-700 border border-amber-200";
                                                                        else if (score > 0) cellClass = "bg-red-50 text-red-700 border border-red-200";
                                                                        else cellClass = "bg-gray-50 text-gray-500 border border-gray-200";

                                                                        cellContent = match.min !== undefined ? `≥ ${match.min}` : (match.max !== undefined ? `≤ ${match.max}` : '');
                                                                        if (cellContent === '') cellContent = 'Any';
                                                                    }
                                                                } else if (thresholds && typeof thresholds === 'string') {
                                                                    cellContent = idx === 0 ? thresholds : "";
                                                                }

                                                                return (
                                                                    <td key={score} className="px-2 py-3 text-center align-middle">
                                                                        {cellContent !== '-' && cellContent !== '' ? (
                                                                            <span className={`inline-flex items-center justify-center min-w-[70px] px-2.5 py-1.5 rounded-lg text-xs font-bold leading-none ${cellClass}`}>
                                                                                {cellContent}
                                                                            </span>
                                                                        ) : (
                                                                            <span className="text-gray-200 text-xl font-light">·</span>
                                                                        )}
                                                                    </td>
                                                                );
                                                            })}
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                </Card>
                            ))}
                    </div>
                </div>

            </div>
        </div>
    );
};

export default TradeTargets;
