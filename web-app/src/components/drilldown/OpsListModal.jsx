import React from 'react';
import Modal from '../common/Modal';
import {
    Users, Search, Zap, Droplets, Waves, Thermometer, Home,
    Paintbrush, Wind, Flame, Rat, Leaf, ShieldAlert, Hammer, User, Trash
} from 'lucide-react';

const OpsListModal = ({ isOpen, onClose, data, tradeGroup }) => {
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
            title={`Ops — ${tradeGroup}`}
            maxWidth="max-w-5xl"
        >
            <div className="flex flex-col gap-6 p-2">
                {/* Summary row */}
                <div className="grid grid-cols-1">
                    <div className="p-4 rounded-2xl bg-gray-50 border border-black/5 text-center shadow-sm">
                        <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1 flex items-center justify-center gap-1.5">
                            <Users className="w-3.5 h-3.5" /> Total Ops
                        </div>
                        <div className="text-3xl font-black text-gray-900">{data.total_count}</div>
                    </div>
                </div>

                {/* Ops list */}
                <div className="max-h-[50vh] overflow-y-auto rounded-2xl border border-black/5 bg-white shadow-sm overflow-hidden">
                    <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-gray-50/90 backdrop-blur-md z-10">
                            <tr className="border-b border-black/5">
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">#</th>
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Name</th>
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Trade</th>
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Region</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-black/5">
                            {(data.ops || []).map((op, i) => (
                                <tr key={i} className="transition-colors hover:bg-brand-blue/5">
                                    <td className="py-4 px-6 text-muted-foreground font-medium">{i + 1}</td>
                                    <td className="py-4 px-6 font-bold text-gray-900 flex items-center gap-2">
                                        <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-400">
                                            <User className="w-4 h-4" />
                                        </div>
                                        {op.name}
                                    </td>
                                    <td className="py-4 px-6">
                                        <div className="flex items-center gap-2 font-medium text-gray-700 text-xs">
                                            {getTradeIcon(op.trade)}
                                            {op.trade}
                                        </div>
                                    </td>
                                    <td className="py-4 px-6">
                                        <span className="font-bold text-gray-400 text-xs uppercase tracking-wider">
                                            {op.region || 'All'}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {(!data.ops || data.ops.length === 0) && (
                    <div className="text-center py-12 text-muted-foreground bg-gray-50/50 rounded-2xl border border-dashed border-black/10">
                        <Users className="w-12 h-12 mx-auto mb-3 opacity-20" />
                        <p className="font-medium text-lg">No ops data available.</p>
                    </div>
                )}
            </div>
        </Modal>
    );
};

export default OpsListModal;
