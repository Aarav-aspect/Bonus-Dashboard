import React, { useState, useEffect } from 'react';
import Modal from '../common/Modal';
import { fetchVcrUpdate } from '../../api';
import {
    Loader2, Search, Zap, AlertCircle, Users, AlertTriangle, CheckCircle2,
    Droplets, Waves, Thermometer, Home, Paintbrush, Wind, Flame, Rat, Leaf, ShieldAlert, Hammer, Trash
} from 'lucide-react';

const VcrDetailModal = ({ isOpen, onClose, tradeGroup, tradeFilter, regionFilter, monthName }) => {
    const [drivers, setDrivers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        let mounted = true;
        if (isOpen) {
            setLoading(true);
            setError(null);
            fetchVcrUpdate(tradeGroup, monthName, tradeFilter, regionFilter)
                .then(data => {
                    if (mounted) {
                        setDrivers(data.drivers || []);
                        setLoading(false);
                    }
                })
                .catch(err => {
                    console.error("Error fetching VCR data:", err);
                    if (mounted) {
                        setError("Failed to load VCR details.");
                        setLoading(false);
                    }
                });
        }
        return () => { mounted = false; };
    }, [isOpen, tradeGroup, tradeFilter, regionFilter]);



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

        return <Zap className="h-3.5 w-3.5 text-brand-blue" />; // Default fallback
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={`VCR Update %`}
            maxWidth="max-w-5xl"
        >
            <div className="flex flex-col h-[60vh] max-h-[600px]">
                {/* Header Actions */}
                <div className="flex justify-between items-center mb-6 pl-1">

                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-y-auto min-h-0 bg-gray-50/50 rounded-xl border border-gray-100">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center h-full text-muted-foreground gap-3">
                            <Loader2 className="h-6 w-6 animate-spin text-brand-blue" />
                            <span className="text-sm font-medium">Loading drivers...</span>
                        </div>
                    ) : error ? (
                        <div className="flex flex-col items-center justify-center h-full text-support-red gap-2">
                            <AlertCircle className="h-8 w-8 opacity-50" />
                            <span className="text-sm font-medium">{error}</span>
                        </div>
                    ) : drivers.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-muted-foreground gap-2">
                            <div className="h-12 w-12 rounded-full bg-gray-100 flex items-center justify-center mb-2">
                                <Search className="h-6 w-6 text-gray-400" />
                            </div>
                            <span className="text-sm font-medium">No drivers found matching your search.</span>
                        </div>
                    ) : (
                        <table className="w-full text-sm text-left relative">
                            <thead className="text-xs uppercase bg-gray-100/80 text-muted-foreground sticky top-0 z-10 backdrop-blur-sm">
                                <tr>
                                    <th className="px-6 py-4 font-bold tracking-wider rounded-tl-xl">Driver Name</th>
                                    <th className="px-6 py-4 font-bold tracking-wider">Trade</th>
                                    <th className="px-6 py-4 font-bold tracking-wider">Region</th>
                                    <th className="px-6 py-4 font-bold tracking-wider text-right rounded-tr-xl">Submitted / Target</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100 bg-white">
                                {drivers.map((driver, idx) => (
                                    <tr
                                        key={idx}
                                        className="hover:bg-brand-blue/5 transition-colors group cursor-default"
                                    >
                                        <td className="px-6 py-4 font-semibold text-gray-900 group-hover:text-brand-blue transition-colors">
                                            {driver.name}
                                        </td>
                                        <td className="px-6 py-4 text-gray-700">
                                            <div className="flex items-center gap-1.5 font-medium">
                                                {getTradeIcon(driver.trade)}
                                                {driver.trade}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-gray-500 font-medium">
                                            {driver.region}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className={`inline-flex items-center justify-end font-bold text-base tracking-tight ${driver.submissions >= driver.target ? 'text-support-green' : 'text-support-red'}`}>
                                                {driver.submissions} / {driver.target}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>

                {!loading && !error && drivers.length > 0 && (
                    <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground px-1">
                        <div>Showing <span className="font-bold text-gray-700">{drivers.length}</span> drivers</div>
                        <div className="flex gap-4">
                            <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-support-green"></span>Met Target</div>
                            <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-support-red"></span>Missed Target</div>
                        </div>
                    </div>
                )}
            </div>
        </Modal>
    );
};

export default VcrDetailModal;
