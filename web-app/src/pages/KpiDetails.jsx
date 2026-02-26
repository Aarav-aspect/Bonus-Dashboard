import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Header from '../components/layout/Header';
import { Card } from '@/components/ui/card';
import { fetchDriverScores, fetchTradeGroups } from '../api';
import { useAuth } from '../context/AuthContext';
import { ArrowLeft, Loader2, AlertTriangle, CheckCircle2, Users } from 'lucide-react';

function KpiDetails() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();

    const tradeGroup = searchParams.get('trade_group') || '';
    const kpi = searchParams.get('kpi') || '';

    const [drivers, setDrivers] = useState([]);
    const [summary, setSummary] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!tradeGroup) return;

        async function load() {
            try {
                setLoading(true);
                setError(null);
                const data = await fetchDriverScores(tradeGroup);
                setDrivers(data.drivers || []);
                setSummary({
                    total: data.total_count,
                    below7: data.below_7_count,
                    tradeGroup: data.trade_group,
                });
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        }
        load();
    }, [tradeGroup]);

    const getScoreColor = (score) => {
        if (score >= 8) return 'text-green-600';
        if (score >= 7) return 'text-yellow-600';
        return 'text-red-600';
    };

    const getScoreBg = (score) => {
        if (score >= 8) return 'bg-green-50 border-green-200';
        if (score >= 7) return 'bg-yellow-50 border-yellow-200';
        return 'bg-red-50 border-red-200';
    };

    const getBarWidth = (score) => `${Math.min((score / 10) * 100, 100)}%`;

    const getBarColor = (score) => {
        if (score >= 8) return 'bg-green-500';
        if (score >= 7) return 'bg-yellow-500';
        return 'bg-red-500';
    };

    return (
        <div className="max-w-6xl mx-auto p-6">
            <Header
                showMonthFilter={false}
                showGroupFilter={false}
            />

            {/* Back button + Title */}
            <div className="flex items-center gap-4 mb-8">
                <button
                    onClick={() => navigate(-1)}
                    className="flex items-center gap-2 text-muted-foreground hover:text-brand-blue transition-colors font-bold text-sm uppercase tracking-wider"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back
                </button>
                <div className="h-6 w-px bg-black/10" />
                <h1 className="text-3xl font-black text-foreground tracking-tight">
                    KPI Details
                </h1>
            </div>

            {/* KPI Section Title */}
            <div className="mb-6">
                <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
                    <Users className="w-5 h-5 text-brand-blue" />
                    Drivers with &lt;7 — {tradeGroup}
                </h2>
                <p className="text-sm text-muted-foreground mt-1">
                    OptiDrive scores for all drivers in this trade group. Scores below 7.0 are flagged.
                </p>
            </div>

            {/* Summary Cards */}
            {summary && !loading && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
                    <Card className="p-5 border-black/5 shadow-sm rounded-2xl">
                        <div className="text-sm text-muted-foreground font-bold uppercase tracking-wider mb-1">Total Drivers</div>
                        <div className="text-3xl font-black text-foreground">{summary.total}</div>
                    </Card>
                    <Card className="p-5 border-red-200 bg-red-50 shadow-sm rounded-2xl">
                        <div className="text-sm text-red-600 font-bold uppercase tracking-wider mb-1 flex items-center gap-1">
                            <AlertTriangle className="w-4 h-4" /> Below 7.0
                        </div>
                        <div className="text-3xl font-black text-red-600">{summary.below7}</div>
                    </Card>
                    <Card className="p-5 border-green-200 bg-green-50 shadow-sm rounded-2xl">
                        <div className="text-sm text-green-600 font-bold uppercase tracking-wider mb-1 flex items-center gap-1">
                            <CheckCircle2 className="w-4 h-4" /> At or Above 7.0
                        </div>
                        <div className="text-3xl font-black text-green-600">{summary.total - summary.below7}</div>
                    </Card>
                </div>
            )}

            {/* Loading */}
            {loading && (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="w-8 h-8 animate-spin text-brand-blue" />
                    <span className="ml-3 text-muted-foreground font-medium">Loading driver scores...</span>
                </div>
            )}

            {/* Error */}
            {error && (
                <Card className="p-6 bg-red-50 border-red-200 text-red-700 rounded-2xl">
                    <p className="font-bold">Error loading driver data</p>
                    <p className="text-sm mt-1">{error}</p>
                </Card>
            )}

            {/* Driver Table */}
            {!loading && !error && drivers.length > 0 && (
                <Card className="overflow-hidden border-black/5 shadow-md rounded-2xl">
                    <table className="w-full">
                        <thead>
                            <tr className="bg-muted/50 border-b border-black/5">
                                <th className="text-left p-4 text-sm font-bold text-muted-foreground uppercase tracking-wider">#</th>
                                <th className="text-left p-4 text-sm font-bold text-muted-foreground uppercase tracking-wider">Driver Name</th>
                                <th className="text-left p-4 text-sm font-bold text-muted-foreground uppercase tracking-wider">Score</th>
                                <th className="text-left p-4 text-sm font-bold text-muted-foreground uppercase tracking-wider w-1/3">Performance</th>
                                <th className="text-center p-4 text-sm font-bold text-muted-foreground uppercase tracking-wider">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {drivers.map((driver, index) => (
                                <tr
                                    key={index}
                                    className={`border-b border-black/5 transition-colors hover:bg-muted/30 ${driver.below_threshold ? 'bg-red-50/50' : ''}`}
                                >
                                    <td className="p-4 text-sm text-muted-foreground font-medium">
                                        {index + 1}
                                    </td>
                                    <td className="p-4">
                                        <span className="font-bold text-foreground">{driver.name}</span>
                                    </td>
                                    <td className="p-4">
                                        <span className={`text-lg font-black ${getScoreColor(driver.score)}`}>
                                            {driver.score.toFixed(1)}
                                        </span>
                                        <span className="text-sm text-muted-foreground/50 ml-1">/10</span>
                                    </td>
                                    <td className="p-4">
                                        <div className="w-full h-2.5 bg-muted rounded-full overflow-hidden">
                                            <div
                                                className={`h-full rounded-full transition-all duration-700 ${getBarColor(driver.score)}`}
                                                style={{ width: getBarWidth(driver.score) }}
                                            />
                                        </div>
                                    </td>
                                    <td className="p-4 text-center">
                                        {driver.below_threshold ? (
                                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-700 border border-red-200">
                                                <AlertTriangle className="w-3 h-3" /> Below
                                            </span>
                                        ) : (
                                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-green-100 text-green-700 border border-green-200">
                                                <CheckCircle2 className="w-3 h-3" /> Pass
                                            </span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </Card>
            )}

            {/* Empty state */}
            {!loading && !error && drivers.length === 0 && (
                <Card className="p-12 text-center border-black/5 shadow-sm rounded-2xl">
                    <Users className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
                    <p className="text-muted-foreground font-medium">No driver data available for {tradeGroup}.</p>
                </Card>
            )}
        </div>
    );
}

export default KpiDetails;
