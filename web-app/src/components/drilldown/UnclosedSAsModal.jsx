import React from 'react';
import Modal from '../common/Modal';
import { AlertTriangle, FileText, Calendar } from 'lucide-react';

const UnclosedSAsModal = ({ isOpen, onClose, data, tradeGroup }) => {
    if (!data) return null;

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={`Unclosed SAs — ${tradeGroup}`}
            maxWidth="max-w-4xl"
        >
            <div className="flex flex-col gap-6 p-2">
                {/* Summary row */}
                <div className="grid grid-cols-1">
                    <div className="p-4 rounded-2xl bg-red-50/50 border border-red-100 text-center shadow-sm">
                        <div className="text-[10px] font-bold text-red-600 uppercase tracking-widest mb-1 flex items-center justify-center gap-1.5">
                            <AlertTriangle className="w-3.5 h-3.5" /> Total Unclosed SAs
                        </div>
                        <div className="text-3xl font-black text-red-600">{data.total_count}</div>
                    </div>
                </div>

                {/* SA list */}
                <div className="max-h-[50vh] overflow-y-auto rounded-2xl border border-black/5 bg-white shadow-sm overflow-hidden">
                    <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-gray-50/90 backdrop-blur-md z-10">
                            <tr className="border-b border-black/5">
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">#</th>
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">SA Number</th>
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Status</th>
                                <th className="text-right py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Actual Start</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-black/5">
                            {(data.unclosed_sas || []).map((sa, i) => (
                                <tr key={i} className="transition-colors hover:bg-brand-blue/5">
                                    <td className="py-4 px-6 text-muted-foreground font-medium">{i + 1}</td>
                                    <td className="py-4 px-6 font-bold text-gray-900 flex items-center gap-2">
                                        <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-400">
                                            <FileText className="w-4 h-4" />
                                        </div>
                                        {sa.appointment_number}
                                    </td>
                                    <td className="py-4 px-6">
                                        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 uppercase tracking-wider shadow-sm">
                                            {sa.status}
                                        </span>
                                    </td>
                                    <td className="py-4 px-6 text-right font-medium text-gray-500 flex items-center justify-end gap-1.5">
                                        <Calendar className="w-3.5 h-3.5 opacity-40" />
                                        {sa.actual_start_time}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {(!data.unclosed_sas || data.unclosed_sas.length === 0) && (
                    <div className="text-center py-12 text-muted-foreground bg-gray-50/50 rounded-2xl border border-dashed border-black/10">
                        <AlertTriangle className="w-12 h-12 mx-auto mb-3 opacity-20" />
                        <p className="font-medium text-lg">No unclosed SAs found.</p>
                    </div>
                )}
            </div>
        </Modal>
    );
};

export default UnclosedSAsModal;
