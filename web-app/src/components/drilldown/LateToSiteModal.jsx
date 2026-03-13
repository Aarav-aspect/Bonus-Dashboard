import React from 'react';
import Modal from '../common/Modal';
import { Clock, AlertTriangle, UserCheck } from 'lucide-react';

const LateToSiteModal = ({ isOpen, onClose, data, tradeGroup }) => {
    if (!data) return null;

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={`Late to Site — ${tradeGroup}`}
            maxWidth="max-w-4xl"
        >
            <div className="flex flex-col gap-6 p-2">
                {/* Summary row */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-2xl bg-red-50/50 border border-red-100 text-center shadow-sm">
                        <div className="text-[10px] font-bold text-red-600 uppercase tracking-widest mb-1 flex items-center justify-center gap-1.5">
                            <AlertTriangle className="w-3.5 h-3.5" /> Total Late
                        </div>
                        <div className="text-3xl font-black text-red-600">{data.total_late}</div>
                    </div>
                    <div className="p-4 rounded-2xl bg-blue-50/50 border border-blue-100 text-center shadow-sm">
                        <div className="text-[10px] font-bold text-blue-600 uppercase tracking-widest mb-1 flex items-center justify-center gap-1.5">
                            <Clock className="w-3.5 h-3.5" /> Total SAs
                        </div>
                        <div className="text-3xl font-black text-blue-600">{data.total_sas}</div>
                    </div>
                </div>

                {/* Engineers list */}
                <div className="max-h-[50vh] overflow-y-auto rounded-2xl border border-black/5 bg-white shadow-sm overflow-hidden">
                    <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-gray-50/90 backdrop-blur-md z-10">
                            <tr className="border-b border-black/5">
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">#</th>
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Engineer</th>
                                <th className="text-right py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Late / Total</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-black/5">
                            {(data.engineers || []).map((eng, i) => (
                                <tr key={i} className="transition-colors hover:bg-brand-blue/5">
                                    <td className="py-4 px-6 text-muted-foreground font-medium">{i + 1}</td>
                                    <td className="py-4 px-6 font-bold text-gray-900 flex items-center gap-2">
                                        <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-400 group-hover:bg-brand-blue/10 group-hover:text-brand-blue transition-colors">
                                            <UserCheck className="w-4 h-4" />
                                        </div>
                                        {eng.engineer_name}
                                    </td>
                                    <td className="py-4 px-6 text-right">
                                        <div className="inline-flex items-baseline gap-1 bg-gray-50 px-3 py-1 rounded-lg border border-black/5">
                                            <span className="font-black text-red-600 text-lg">{eng.late_count}</span>
                                            <span className="text-muted-foreground/30 text-[10px] font-bold uppercase">/ {eng.total_count}</span>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {(!data.engineers || data.engineers.length === 0) && (
                    <div className="text-center py-12 text-muted-foreground bg-gray-50/50 rounded-2xl border border-dashed border-black/10">
                        <Clock className="w-12 h-12 mx-auto mb-3 opacity-20" />
                        <p className="font-medium text-lg">No late to site data found.</p>
                    </div>
                )}
            </div>
        </Modal>
    );
};

export default LateToSiteModal;
