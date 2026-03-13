import React from 'react';
import Modal from '../common/Modal';
import {
    Users, AlertTriangle, CheckCircle2, Search, Zap,
    Droplets, Waves, Thermometer, Home, Paintbrush, Wind, Flame, Rat, Leaf, ShieldAlert, Hammer, MapPin, Trash
} from 'lucide-react';

const DriversDetailModal = ({ isOpen, onClose, data, tradeGroup }) => {
    if (!data) return null;

    const getTradeIcon = (trade = "") => {
        const t = trade.toLowerCase();
        if (t.includes('plumbing')) return <Droplets className="h-3.5 w-3.5 text-brand-blue" />;
        if (t.includes('drainage')) return <Waves className="h-3.5 w-3.5 text-brand-blue" />;
        if (t.includes('leak detection')) return <Search className="h-3.5 w-3.5 text-brand-blue" />;
        if (t.includes('damp') || t.includes('mould')) return <Thermometer className="h-3.5 w-3.5 text-brand-blue" />;
        if (t.includes('roofing') || t.includes('window') || t.includes('door')) return <Home className="h-3.5 w-3.5 text-brand-blue" />;
        if (t.includes('decoration') || t.includes('decorating') || t.includes('painting')) return <Paintbrush className="h-3.5 w-3.5 text-brand-blue" />;
        if (t.includes('electrical')) return <Zap className="h-3.5 w-3.5 text-brand-blue" />;
        if (t.includes('heating') || t.includes('hvac') || t.includes('air con') || t.includes('ventilation')) return <Wind className="h-3.5 w-3.5 text-brand-blue" />;
        if (t.includes('gas') || t.includes('flame')) return <Flame className="h-3.5 w-3.5 text-brand-blue" />;
        if (t.includes('pest')) return <Rat className="h-3.5 w-3.5 text-brand-blue" />;
        if (t.includes('garden')) return <Leaf className="h-3.5 w-3.5 text-brand-blue" />;
        if (t.includes('fire')) return <ShieldAlert className="h-3.5 w-3.5 text-brand-blue" />;
        if (t.includes('carpentry') || t.includes('handyman')) return <Hammer className="h-3.5 w-3.5 text-brand-blue" />;
        if (t.includes('waste')) return <Trash className="h-3.5 w-3.5 text-brand-blue" />;

        return <Zap className="h-3.5 w-3.5 text-brand-blue" />;
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={`Drivers — ${tradeGroup}`}
            maxWidth="max-w-5xl"
        >
            <div className="flex flex-col gap-6 p-2">
                {/* Summary row */}
                <div className="grid grid-cols-4 gap-4">
                    <div className="p-4 rounded-2xl bg-gray-50 border border-black/5 text-center shadow-sm">
                        <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1 flex items-center justify-center gap-1.5">
                            <Users className="w-3.5 h-3.5" /> Total Drivers
                        </div>
                        <div className="text-3xl font-black text-gray-900">{data.total_count}</div>
                    </div>
                    <div className="p-4 rounded-2xl bg-red-50/50 border border-red-100 text-center shadow-sm">
                        <div className="text-[10px] font-bold text-red-600 uppercase tracking-widest mb-1 flex items-center justify-center gap-1.5">
                            <AlertTriangle className="w-3.5 h-3.5" /> Below 7.0
                        </div>
                        <div className="text-3xl font-black text-red-600">{data.below_7_count}</div>
                    </div>
                    <div className="p-4 rounded-2xl bg-green-50/50 border border-green-100 text-center shadow-sm">
                        <div className="text-[10px] font-bold text-green-600 uppercase tracking-widest mb-1 flex items-center justify-center gap-1.5">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Pass
                        </div>
                        <div className="text-3xl font-black text-green-600">{(data.scored_count ?? data.total_count) - data.below_7_count}</div>
                    </div>
                    {(data.missing_count ?? 0) > 0 && (
                        <div className="p-4 rounded-2xl bg-amber-50/50 border border-amber-200 text-center shadow-sm">
                            <div className="text-[10px] font-bold text-amber-600 uppercase tracking-widest mb-1 flex items-center justify-center gap-1.5">
                                <AlertTriangle className="w-3.5 h-3.5" /> Missing Data
                            </div>
                            <div className="text-3xl font-black text-amber-600">{data.missing_count}</div>
                        </div>
                    )}
                </div>

                {/* Driver list */}
                <div className="max-h-[50vh] overflow-y-auto rounded-2xl border border-black/5 bg-white shadow-sm overflow-hidden">
                    <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-gray-50/90 backdrop-blur-md z-10">
                            <tr className="border-b border-black/5">
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">#</th>
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Name</th>
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Trade</th>
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Optidrive</th>
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Region</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-black/5">
                            {(data.drivers || []).map((driver, i) => {
                                const scoreColor = driver.score >= 8 ? 'text-green-600' : driver.score >= 7 ? 'text-yellow-600' : 'text-red-600';
                                const isMissing = driver.missing_data;
                                return (
                                    <tr key={i} className={`transition-colors hover:bg-brand-blue/5 ${isMissing ? 'bg-amber-50/30' : driver.below_threshold ? 'bg-red-50/20' : ''}`}>
                                        <td className="py-4 px-6 text-muted-foreground font-medium">{i + 1}</td>
                                        <td className="py-4 px-6 font-bold text-gray-900">
                                            {isMissing ? (
                                                <div className="flex items-center gap-2">
                                                    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-100 text-amber-700 uppercase tracking-wider border border-amber-200">Missing Data</span>
                                                    <span className="text-gray-500 font-medium">{driver.name}</span>
                                                </div>
                                            ) : driver.name}
                                        </td>
                                        <td className="py-4 px-6">
                                            <div className="flex items-center gap-2 font-medium text-gray-700">
                                                {getTradeIcon(driver.trade)}
                                                {driver.trade}
                                            </div>
                                        </td>
                                        <td className="py-4 px-6">
                                            {isMissing ? (
                                                <span className="text-xs font-semibold text-amber-500 italic">No Optidrive record</span>
                                            ) : (
                                                <div className="flex items-baseline gap-0.5">
                                                    <span className={`text-lg font-black ${scoreColor}`}>{driver.score.toFixed(1)}</span>
                                                    <span className="text-muted-foreground/40 text-[10px] uppercase font-bold">/ 10</span>
                                                </div>
                                            )}
                                        </td>
                                        <td className="py-4 px-6">
                                            <span className="font-bold text-gray-500">{driver.region}</span>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>

                {(!data.drivers || data.drivers.length === 0) && (
                    <div className="text-center py-12 text-muted-foreground bg-gray-50/50 rounded-2xl border border-dashed border-black/10">
                        <Users className="w-12 h-12 mx-auto mb-3 opacity-20" />
                        <p className="font-medium text-lg">No driver data available.</p>
                    </div>
                )}
            </div>
        </Modal>
    );
};

export default DriversDetailModal;
