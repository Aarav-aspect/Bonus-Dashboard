import React from 'react';
import Modal from '../common/Modal';
import { FileText } from 'lucide-react';

const CasesModal = ({ isOpen, onClose, data, tradeGroup }) => {
    if (!data) return null;

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            noBackdrop
            title={`Cases — ${tradeGroup}`}
        >
            <div className="flex flex-col gap-4 p-2">
                {/* Summary row */}
                <div className="grid grid-cols-1 gap-3">
                    <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-center">
                        <div className="text-[10px] font-bold text-red-600 uppercase tracking-wider flex items-center justify-center gap-1">
                            <FileText className="w-3 h-3" /> Total Cases
                        </div>
                        <div className="text-2xl font-black text-red-600">{data.total_count}</div>
                    </div>
                </div>

                {/* Cases list */}
                <div className="max-h-[400px] overflow-y-auto rounded-xl border border-black/5">
                    <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-muted/80 backdrop-blur-sm z-10">
                            <tr className="border-b border-black/5">
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">#</th>
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Case Number</th>
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Case Type</th>
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Engineer</th>
                            </tr>
                        </thead>
                        <tbody>
                            {(data.cases || []).map((c, i) => (
                                <tr key={i} className="border-b border-black/5 transition-colors hover:bg-muted/20">
                                    <td className="p-3 text-muted-foreground font-medium">{i + 1}</td>
                                    <td className="p-3 font-bold text-foreground">{c.case_number}</td>
                                    <td className="p-3 text-muted-foreground">
                                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-700 border border-amber-200">
                                            {c.case_type}
                                        </span>
                                    </td>
                                    <td className="p-3 text-muted-foreground font-medium">{c.engineer_name}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {(data.cases || []).length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                        <FileText className="w-10 h-10 mx-auto mb-2 opacity-30" />
                        <p className="font-medium">No cases found.</p>
                    </div>
                )}
            </div>
        </Modal>
    );
};

export default CasesModal;
