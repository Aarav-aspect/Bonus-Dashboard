import React from 'react';
import Modal from '../common/Modal';
import { Clock, Timer, CheckCircle } from 'lucide-react';

const Reactive6PlusModal = ({ isOpen, onClose, data, tradeGroup }) => {
    if (!data) return null;

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={`Reactive 6+ Hrs — ${tradeGroup}`}
            maxWidth="max-w-4xl"
        >
            <div className="flex flex-col gap-6 p-2">
                {/* Summary row */}
                <div className="grid grid-cols-1">
                    <div className="p-4 rounded-2xl bg-red-50/50 border border-red-100 text-center shadow-sm">
                        <div className="text-[10px] font-bold text-red-600 uppercase tracking-widest mb-1 flex items-center justify-center gap-1.5">
                            <Clock className="w-3.5 h-3.5" /> Total Long Duration Jobs
                        </div>
                        <div className="text-3xl font-black text-red-600">{data.total_count}</div>
                    </div>
                </div>

                {/* Job list */}
                <div className="max-h-[50vh] overflow-y-auto rounded-2xl border border-black/5 bg-white shadow-sm overflow-hidden">
                    <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-gray-50/90 backdrop-blur-md z-10">
                            <tr className="border-b border-black/5">
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">#</th>
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Job Number</th>
                                <th className="text-right py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Duration</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-black/5">
                            {(data.reactive_6plus || []).map((item, i) => (
                                <tr key={i} className="transition-colors hover:bg-brand-blue/5">
                                    <td className="py-4 px-6 text-muted-foreground font-medium">{i + 1}</td>
                                    <td className="py-4 px-6 font-bold text-gray-900 flex items-center gap-2">
                                        <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-400">
                                            <CheckCircle className="w-4 h-4" />
                                        </div>
                                        {item.appointment_number}
                                    </td>
                                    <td className="py-4 px-6 text-right">
                                        <div className="inline-flex items-center gap-1.5 bg-red-50 px-3 py-1 rounded-lg border border-red-100 shadow-sm">
                                            <Timer className="w-3.5 h-3.5 text-red-600" />
                                            <span className="font-black text-red-600 text-lg">{item.duration}</span>
                                            <span className="text-red-600/40 text-[10px] font-bold uppercase tracking-tight">HRS</span>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {(!data.reactive_6plus || data.reactive_6plus.length === 0) && (
                    <div className="text-center py-12 text-muted-foreground bg-gray-50/50 rounded-2xl border border-dashed border-black/10">
                        <Clock className="w-12 h-12 mx-auto mb-3 opacity-20" />
                        <p className="font-medium text-lg">No reactive 6+ hour jobs found.</p>
                    </div>
                )}
            </div>
        </Modal>
    );
};

export default Reactive6PlusModal;
