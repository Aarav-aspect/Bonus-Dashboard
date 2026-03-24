import React, { useState, useEffect, useRef } from 'react';
import KPICard from '../common/KPICard';
import Modal from '../common/Modal';
import DriversDetailModal from '../drilldown/DriversDetailModal';
import ReviewsDetailModal from '../drilldown/ReviewsDetailModal';
import OpsListModal from '../drilldown/OpsListModal';
import UnclosedSAsModal from '../drilldown/UnclosedSAsModal';
import CallbackJobsModal from '../drilldown/CallbackJobsModal';
import Reactive6PlusModal from '../drilldown/Reactive6PlusModal';
import TqrNotSatisfiedModal from '../drilldown/TqrNotSatisfiedModal';
import LateToSiteModal from '../drilldown/LateToSiteModal';
import CasesModal from '../drilldown/CasesModal';
import VcrDetailModal from '../drilldown/VcrDetailModal';
import SatisfactionFormModal from '../drilldown/SatisfactionFormModal';
import { Card } from "@/components/ui/card"
import {
    Car,
    ClipboardCheck,
    TrendingUp,
    Smile,
    Zap,
    Activity,
    Equal,
    Users,
    Loader2
} from 'lucide-react';
import { fetchDriverScores, fetchReviewDetails, fetchOpsList, fetchUnclosedSAs, fetchCallbackJobs, fetchReactive6Plus, fetchTqrNotSatisfied, fetchLateToSite, fetchCases, fetchSatisfactionFormUpdate } from '../../api';

// Mirrors targets.py BONUS_SCORE_BANDS for client-side slab calculation
const BONUS_SCORE_BANDS = [
    { min: 90, max: 101, multiplier: 0.30 },
    { min: 80, max: 90, multiplier: 0.20 },
    { min: 70, max: 80, multiplier: 0.10 },
    { min: 60, max: 70, multiplier: -0.10 },
    { min: 50, max: 60, multiplier: -0.20 },
    { min: 40, max: 50, multiplier: -0.30 },
    { min: 30, max: 40, multiplier: -0.40 },
    { min: 20, max: 30, multiplier: -0.50 },
    { min: 10, max: 20, multiplier: -0.60 },
];

function getSlabMultiplier(score) {
    const band = BONUS_SCORE_BANDS.find(b => score >= b.min && score < b.max);
    return band ? band.multiplier : -0.60;
}

const CategoryBlock = ({ title, kpis, kpiScores, categoryScore, bonusPot = 0, basePot = 0, overallScore = 1, kpiConfig = null, activeTrade = null, tradeGroup = null, drilldownConfig = {}, selectedMonth = null, selectedRegion = "All" }) => {

    // Resolve thresholds for a KPI — handles both static and dynamic (trade-based) configs.
    const resolveThresholds = (kpiName) => {
        if (!kpiConfig || !kpiConfig[kpiName]) return null;
        const cfg = kpiConfig[kpiName];

        // Static KPI: has a top-level thresholds array
        if (cfg.thresholds) return cfg.thresholds;

        // Dynamic KPI: thresholds_by_trade keyed by trade name
        if (cfg.dynamic?.type === 'trade_based') {
            const byTrade = cfg.dynamic.thresholds_by_trade || {};
            const scores = cfg.dynamic.scores || [];

            // Try the active trade first. 
            // If "All" is selected, use the tradeGroup (e.g. "HVac & Electrical") as the key.
            // Fall back to the first available trade if neither matches.
            let tradeKey = (activeTrade && activeTrade !== 'All' && byTrade[activeTrade]) ? activeTrade : null;
            if (!tradeKey && tradeGroup && byTrade[tradeGroup]) {
                tradeKey = tradeGroup;
            }
            if (!tradeKey) {
                tradeKey = Object.keys(byTrade)[0];
            }

            const tradeThresholds = byTrade[tradeKey];
            if (!tradeThresholds) return null;

            const direction = cfg.direction;
            return scores.map((score, i) => {
                const val = tradeThresholds[i];
                return direction === 'higher_is_better' ? { score, min: val } : { score, max: val };
            });
        }

        return null;
    };
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedKpiDrilldown, setSelectedKpiDrilldown] = useState(null);
    const [driversModalOpen, setDriversModalOpen] = useState(false);
    const [driversData, setDriversData] = useState(null);
    const [driversLoading, setDriversLoading] = useState(false);
    const scrollContainerRef = useRef(null);

    // Auto-scroll to "You Are Here"
    useEffect(() => {
        if (selectedKpiDrilldown && kpiConfig && scrollContainerRef.current) {
            const resolved = resolveThresholds(selectedKpiDrilldown.name);
            if (!resolved) return;
            const thresholds = resolved.sort((a, b) => b.score - a.score);
            const direction = (kpiConfig[selectedKpiDrilldown.name] || {}).direction;
            let currentTierIndex = -1;

            if (selectedKpiDrilldown.value !== null) {
                currentTierIndex = thresholds.findIndex(t => {
                    if (direction === "higher_is_better") {
                        return selectedKpiDrilldown.value >= (t.min ?? -Infinity);
                    } else {
                        return selectedKpiDrilldown.value <= (t.max ?? Infinity);
                    }
                });

                // If no threshold is met (worse than the lowest tier), fallback to the lowest score bucket
                if (currentTierIndex === -1 && thresholds.length > 0) {
                    currentTierIndex = thresholds.length - 1;
                }
            }

            if (currentTierIndex !== -1 && scrollContainerRef.current.children) {
                const targetCard = scrollContainerRef.current.children[currentTierIndex];
                if (targetCard) {
                    // Small delay to allow animation to start/layout to settle
                    setTimeout(() => {
                        targetCard.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
                    }, 300);
                }
            }
        }
    }, [selectedKpiDrilldown, kpiConfig]);

    // Color logic using Tailwind classes
    let scoreColorClass = "text-support-red";
    let progressBarClass = "bg-support-red";
    if (categoryScore >= 70) {
        scoreColorClass = "text-support-green";
        progressBarClass = "bg-support-green";
    } else if (categoryScore >= 50) {
        scoreColorClass = "text-support-orange";
        progressBarClass = "bg-support-orange";
    }

    // Icon Mapping
    const getIcon = (title) => {
        const t = title.toLowerCase();
        if (t.includes('vehic')) return <Car className="h-6 w-6 text-brand-blue" />;
        if (t.includes('proced')) return <ClipboardCheck className="h-6 w-6 text-brand-blue" />;
        if (t.includes('conver')) return <TrendingUp className="h-6 w-6 text-brand-blue" />;
        if (t.includes('satis')) return <Smile className="h-6 w-6 text-brand-blue" />;
        if (t.includes('prod')) return <Zap className="h-6 w-6 text-brand-blue" />;
        return <Activity className="h-6 w-6 text-brand-blue" />;
    }

    return (
        <div className="mb-6">
            <Card
                className="group relative overflow-hidden p-8 cursor-pointer border-black/5 shadow-md rounded-2xl hover:translate-y-[-4px] hover:shadow-lg transition-all duration-300 bg-white"
                onClick={() => setIsModalOpen(true)}
            >
                {/* Decorative background circle */}
                <div className="absolute top-0 right-0 -mr-8 -mt-8 h-32 w-32 rounded-full bg-brand-blue/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                <div className="flex items-start justify-between relative z-10 w-full">
                    <div className="flex flex-col gap-3">
                        <div className="p-3 bg-white w-fit rounded-xl border border-black/5">
                            {getIcon(title)}
                        </div>
                        <div className="flex flex-col gap-1">
                            <span className="text-xl font-black text-foreground">
                                {title}
                            </span>
                            <span className="text-xs text-muted-foreground font-bold uppercase tracking-wider group-hover:text-brand-blue transition-colors">
                                View Details →
                            </span>
                        </div>
                    </div>

                    {categoryScore !== null && (
                        <div className="flex flex-col items-end gap-2">
                            <div className={`text-5xl font-black ${scoreColorClass} tracking-tighter`}>
                                {categoryScore.toFixed(0)}%
                            </div>
                        </div>
                    )}
                </div>

                {/* Progress Bar & Monetary Contribution */}
                {categoryScore !== null && (
                    <div className="mt-8 flex items-center justify-between gap-4">
                        <div className="flex-1 h-3 bg-muted rounded-full overflow-hidden">
                            <div
                                className={`h-full rounded-full ${progressBarClass} transition-all duration-1000`}
                                style={{ width: `${categoryScore}%` }}
                            />
                        </div>
                        <div className="text-xl font-black text-muted-foreground/50 whitespace-nowrap">
                            +£{(overallScore > 0 ? (bonusPot * categoryScore) / (overallScore * 5) : 0).toFixed(0)}
                            <span className="text-sm text-muted-foreground/30 font-bold ml-1">
                                / £{((basePot * 1.3) / 5).toFixed(0)}
                            </span>
                        </div>
                    </div>
                )}
            </Card>

            <Modal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title={`${title} Performance`}
            >
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {Object.entries(kpis).map(([name, value], index) => {
                        const score = kpiScores[name] || 0;
                        return (
                            <div
                                key={name}
                                className="kpi-card-enter"
                                style={{ animationDelay: `${index * 60}ms` }}
                            >
                                <KPICard
                                    label={name}
                                    value={value}
                                    score={score}
                                    onClick={(data) => setSelectedKpiDrilldown({ name, ...data })}
                                />
                            </div>
                        );
                    })}
                </div>
            </Modal>

            {/* Nested Drilldown Modal */}
            <Modal
                isOpen={!!selectedKpiDrilldown}
                onClose={() => setSelectedKpiDrilldown(null)}
                title={selectedKpiDrilldown?.name || "KPI Details"}
                contentClassName={driversModalOpen ? 'blur-sm opacity-50 scale-[0.97]' : ''}
            >
                {selectedKpiDrilldown && (
                    <div className="flex flex-col gap-6 p-4">

                        <div className="flex flex-col md:flex-row gap-6 items-center drilldown-enter">
                            {/* Left Column: Numerator and Denominator */}
                            {selectedKpiDrilldown.numerator !== null && (
                                <div className="flex-1 w-full md:w-auto flex flex-col justify-center gap-2">
                                    <div className="flex items-center justify-between p-3 bg-muted/20 rounded-xl border border-black/5">
                                        <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider" title={selectedKpiDrilldown.numerator_label}>
                                            {selectedKpiDrilldown.numerator_label || "Numerator"}
                                        </span>
                                        <span className="text-xl font-black text-foreground whitespace-nowrap ml-4">
                                            {selectedKpiDrilldown.numerator?.toLocaleString() ?? "N/A"}
                                        </span>
                                    </div>

                                    {selectedKpiDrilldown.denominator !== null && (
                                        <>
                                            <div className="flex items-center justify-center -my-3 z-10 relative">
                                                <div className="bg-white rounded-full p-1 border border-black/5">
                                                    <div className="text-[10px] font-bold text-muted-foreground uppercase px-2 py-0.5 bg-muted/20 rounded-full">
                                                        ÷
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="flex items-center justify-between p-3 bg-muted/20 rounded-xl border border-black/5">
                                                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider" title={selectedKpiDrilldown.denominator_label}>
                                                    {selectedKpiDrilldown.denominator_label || "Denominator"}
                                                </span>
                                                <span className="text-xl font-black text-foreground whitespace-nowrap ml-4">
                                                    {selectedKpiDrilldown.denominator?.toLocaleString() ?? "N/A"}
                                                </span>
                                            </div>
                                        </>
                                    )}
                                </div>
                            )}

                            {/* Separator Icon for Desktop */}
                            {selectedKpiDrilldown.numerator !== null && (
                                <div className="hidden md:flex text-muted-foreground/30">
                                    <Equal className="h-8 w-8" />
                                </div>
                            )}

                            {/* Right Column: Result */}
                            {(() => {
                                // Default Style (Blue)
                                let colorClass = "bg-brand-blue/5 border-brand-blue/10 text-brand-blue";
                                let ringClass = "ring-brand-blue/10";

                                return (
                                    <div className={`flex flex-col items-center justify-center p-6 rounded-2xl shadow-sm border ring-4 ${colorClass} ${ringClass} transition-all min-w-[160px] result-enter`}>
                                        <span className="text-[10px] font-black uppercase tracking-widest opacity-80 mb-1">{selectedKpiDrilldown.result_label || "Result"}</span>
                                        <span className="text-4xl font-black">
                                            {selectedKpiDrilldown.name.includes('(£)') || selectedKpiDrilldown.name.includes('Value')
                                                ? `£${selectedKpiDrilldown.value?.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
                                                : selectedKpiDrilldown.name.includes('Rating') || selectedKpiDrilldown.name === 'Average Driving Score'
                                                    ? selectedKpiDrilldown.value?.toFixed(1)
                                                    : selectedKpiDrilldown.name.includes('Attended')
                                                        ? (selectedKpiDrilldown.value || 0).toFixed(0)
                                                        : `${(selectedKpiDrilldown.value || 0).toFixed(1)}%`
                                            }
                                        </span>
                                    </div>
                                );
                            })()}
                        </div>

                        {/* Threshold Breakdown using a horizontal scrollbar map */}
                        {(() => {
                            const resolvedThresholds = resolveThresholds(selectedKpiDrilldown.name);
                            if (!resolvedThresholds) return null;
                            return (
                                <div className="mt-8 pt-6 border-t border-black/5 w-full breakdown-enter">
                                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-4 text-center">
                                        Score Breakdown
                                    </h4>
                                    <div
                                        ref={scrollContainerRef}
                                        className="flex gap-3 overflow-x-auto pb-6 px-1 snap-x scrollbar-hide pt-4"
                                    >
                                        {(() => {
                                            const thresholds = resolvedThresholds
                                                .sort((a, b) => b.score - a.score);

                                            const direction = (kpiConfig[selectedKpiDrilldown.name] || {}).direction;

                                            // Find the highest-scoring threshold that is met.
                                            let currentTierIndex = -1;

                                            if (selectedKpiDrilldown.value !== null) {
                                                // The list is sorted DESC by score.
                                                // Iterating from top (100 pts) down to 0 pts.
                                                // The FIRST one we meet is the highest tier achieved.
                                                currentTierIndex = thresholds.findIndex(t => {
                                                    if (direction === "higher_is_better") {
                                                        return selectedKpiDrilldown.value >= (t.min ?? -Infinity);
                                                    } else {
                                                        return selectedKpiDrilldown.value <= (t.max ?? Infinity);
                                                    }
                                                });

                                                // If no threshold is met (worse than the lowest tier), fallback to the lowest score bucket
                                                if (currentTierIndex === -1 && thresholds.length > 0) {
                                                    currentTierIndex = thresholds.length - 1;
                                                }
                                            }

                                            return thresholds.map((t, i) => {
                                                const thresholdVal = t.min !== undefined ? t.min : t.max;
                                                const isCurrentTier = (i === currentTierIndex);
                                                const isAchieved = (currentTierIndex !== -1 && i >= currentTierIndex);

                                                // Dynamic Color Logic based on Points (t.score)
                                                // Defaults (Red / < 50)
                                                let activeColorClass = "border-support-red bg-support-red/10 ring-support-red text-support-red";
                                                let badgeBgClass = "bg-support-red";

                                                if (t.score >= 70) {
                                                    // Green
                                                    activeColorClass = "border-support-green bg-support-green/10 ring-support-green text-support-green";
                                                    badgeBgClass = "bg-support-green";
                                                } else if (t.score >= 50) {
                                                    // Orange
                                                    activeColorClass = "border-support-orange bg-support-orange/10 ring-support-orange text-support-orange";
                                                    badgeBgClass = "bg-support-orange";
                                                }

                                                return (
                                                    <div key={i} className={`relative flex flex-col items-center justify-center min-w-[100px] p-3 rounded-xl border snap-center transition-all ${isCurrentTier
                                                        ? `${activeColorClass} ring-2 shadow-md transform scale-105 z-10`
                                                        : isAchieved
                                                            ? "bg-brand-blue/5 border-brand-blue/10 opacity-60"
                                                            : "opacity-40 border-black/5 grayscale bg-gray-50 bg-white"
                                                        }`}>
                                                        {isCurrentTier && (
                                                            <div className={`absolute -top-3 left-1/2 -translate-x-1/2 ${badgeBgClass} text-white text-[9px] font-black uppercase tracking-widest py-0.5 px-2 rounded-full shadow-sm whitespace-nowrap`}>
                                                                You Are Here
                                                            </div>
                                                        )}
                                                        <span className={`text-[10px] font-black uppercase tracking-wider mb-1 ${isCurrentTier ? "" : isAchieved ? "text-brand-blue" : "text-muted-foreground"}`}>
                                                            {t.score} PTS
                                                        </span>
                                                        <span className={`text-lg font-black whitespace-nowrap ${isCurrentTier ? "text-foreground" : "text-foreground"}`}>
                                                            {direction === "higher_is_better" ? "≥ " : "≤ "}
                                                            {thresholdVal ?? 0}
                                                            {selectedKpiDrilldown.name.includes('%') ? '%' : ''}
                                                        </span>
                                                    </div>
                                                );
                                            });
                                        })()}
                                    </div>
                                </div>
                            );
                        })()}

                        {/* View Details button — shown if this KPI has a drilldown config */}
                        {selectedKpiDrilldown?.name && drilldownConfig[selectedKpiDrilldown.name] && tradeGroup && (
                            <div className="mt-6 pt-4 border-t border-black/5 flex justify-center">
                                <button
                                    onClick={async () => {
                                        setDriversLoading(true);
                                        try {
                                            const cfg = drilldownConfig[selectedKpiDrilldown.name];
                                            let data;
                                            if (cfg.data_source === 'reviews') {
                                                data = await fetchReviewDetails(tradeGroup, selectedMonth, activeTrade, selectedRegion);
                                            } else if (cfg.data_source === 'ops_list') {
                                                data = await fetchOpsList(tradeGroup, activeTrade, selectedRegion);
                                            } else if (cfg.data_source === 'unclosed_sas') {
                                                data = await fetchUnclosedSAs(tradeGroup, selectedMonth, activeTrade, selectedRegion);
                                            } else if (cfg.data_source === 'callback_jobs') {
                                                data = await fetchCallbackJobs(tradeGroup, selectedMonth, activeTrade, selectedRegion);
                                            } else if (cfg.data_source === 'reactive_6plus') {
                                                data = await fetchReactive6Plus(tradeGroup, selectedMonth, activeTrade, selectedRegion);
                                            } else if (cfg.data_source === 'tqr_not_satisfied') {
                                                data = await fetchTqrNotSatisfied(tradeGroup, selectedMonth, activeTrade, selectedRegion);
                                            } else if (cfg.data_source === 'late_to_site') {
                                                data = await fetchLateToSite(tradeGroup, selectedMonth, activeTrade, selectedRegion);
                                            } else if (cfg.data_source === 'cases') {
                                                data = await fetchCases(tradeGroup, selectedMonth, activeTrade, selectedRegion);
                                            } else if (cfg.data_source === 'vcr_update') {
                                                // Used for VCR Update %
                                                setDriversModalOpen(true);
                                                // Set a fake data object to trigger the right modal
                                                setDriversData({ _source: 'vcr_update' });
                                                return; // VcrDetailModal handles its own fetching
                                            } else if (cfg.data_source === 'satisfaction_form_update') {
                                                setDriversModalOpen(true);
                                                setDriversData({ _source: 'satisfaction_form_update' });
                                                return; // SatisfactionFormModal handles its own fetching
                                            } else {
                                                // Added activeTrade here to pass the trade filter down to the API
                                                data = await fetchDriverScores(tradeGroup, activeTrade, selectedRegion);
                                            }
                                            setDriversData({ ...data, _source: cfg.data_source });
                                            setDriversModalOpen(true);
                                        } catch (e) {
                                            console.error(e);
                                        } finally {
                                            setDriversLoading(false);
                                        }
                                    }}
                                    disabled={driversLoading}
                                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-brand-blue text-white font-bold text-sm uppercase tracking-wider rounded-xl hover:bg-brand-blue/90 transition-colors shadow-sm disabled:opacity-50"
                                >
                                    {driversLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Users className="w-4 h-4" />}
                                    View {drilldownConfig[selectedKpiDrilldown.name]?.title || 'Details'}
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </Modal>

            {/* Detail Modals — conditionally render based on data source */}
            {driversData?._source === 'reviews' ? (
                <ReviewsDetailModal
                    isOpen={driversModalOpen}
                    onClose={() => setDriversModalOpen(false)}
                    data={driversData}
                    tradeGroup={tradeGroup}
                />
            ) : driversData?._source === 'ops_list' ? (
                <OpsListModal
                    isOpen={driversModalOpen}
                    onClose={() => setDriversModalOpen(false)}
                    data={driversData}
                    tradeGroup={tradeGroup}
                />
            ) : driversData?._source === 'unclosed_sas' ? (
                <UnclosedSAsModal
                    isOpen={driversModalOpen}
                    onClose={() => setDriversModalOpen(false)}
                    data={driversData}
                    tradeGroup={tradeGroup}
                />
            ) : driversData?._source === 'callback_jobs' ? (
                <CallbackJobsModal
                    isOpen={driversModalOpen}
                    onClose={() => setDriversModalOpen(false)}
                    data={driversData}
                    tradeGroup={tradeGroup}
                />
            ) : driversData?._source === 'reactive_6plus' ? (
                <Reactive6PlusModal
                    isOpen={driversModalOpen}
                    onClose={() => setDriversModalOpen(false)}
                    data={driversData}
                    tradeGroup={tradeGroup}
                />
            ) : driversData?._source === 'tqr_not_satisfied' ? (
                <TqrNotSatisfiedModal
                    isOpen={driversModalOpen}
                    onClose={() => setDriversModalOpen(false)}
                    data={driversData}
                    tradeGroup={tradeGroup}
                />
            ) : driversData?._source === 'late_to_site' ? (
                <LateToSiteModal
                    isOpen={driversModalOpen}
                    onClose={() => setDriversModalOpen(false)}
                    data={driversData}
                    tradeGroup={tradeGroup}
                />
            ) : driversData?._source === 'cases' ? (
                <CasesModal
                    isOpen={driversModalOpen}
                    onClose={() => setDriversModalOpen(false)}
                    data={driversData}
                    tradeGroup={tradeGroup}
                />
            ) : driversData?._source === 'vcr_update' ? (
                <VcrDetailModal
                    isOpen={driversModalOpen}
                    onClose={() => setDriversModalOpen(false)}
                    tradeGroup={tradeGroup}
                    tradeFilter={activeTrade}
                    regionFilter={selectedRegion}
                    monthName={selectedMonth}
                />
            ) : driversData?._source === 'satisfaction_form_update' ? (
                <SatisfactionFormModal
                    isOpen={driversModalOpen}
                    onClose={() => setDriversModalOpen(false)}
                    tradeGroup={tradeGroup}
                    tradeFilter={activeTrade}
                    regionFilter={selectedRegion}
                    monthName={selectedMonth}
                />
            ) : (
                <DriversDetailModal
                    isOpen={driversModalOpen}
                    onClose={() => setDriversModalOpen(false)}
                    data={driversData}
                    tradeGroup={tradeGroup}
                />
            )}
        </div>
    );
};

export default CategoryBlock;
