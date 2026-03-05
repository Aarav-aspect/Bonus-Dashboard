import React from 'react';
import Modal from '../common/Modal';
import { Clock } from 'lucide-react';

const Reactive6PlusModal = ({ isOpen, onClose, data, tradeGroup }) => {
    if (!data) return null;

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            noBackdrop
            title={`Reactive 6+ Hrs — ${tradeGroup}`}
        >
            <div className="flex flex-col gap-4 p-2">
                {/* Summary row */}
                <div className="grid grid-cols-1 gap-3">
                    <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-center">
                        <div className="text-[10px] font-bold text-red-600 uppercase tracking-wider flex items-center justify-center gap-1">
                            <Clock className="w-3 h-3" /> Total 6+ Hrs
                        </div>
                        <div className="text-2xl font-black text-red-600">{data.total_count}</div>
                    </div>
                </div>

                {/* Job list */}
                <div className="max-h-[400px] overflow-y-auto rounded-xl border border-black/5">
                    <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-muted/80 backdrop-blur-sm z-10">
                            <tr className="border-b border-black/5">
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">#</th>
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Job Number</th>
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Total Duration (hrs)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {(data.reactive_6plus || []).map((item, i) => (
                                <tr key={i} className="border-b border-black/5 transition-colors hover:bg-muted/20">
                                    <td className="p-3 text-muted-foreground font-medium">{i + 1}</td>
                                    <td className="p-3 font-bold text-foreground">{item.appointment_number}</td>
                                    <td className="p-3 text-muted-foreground font-medium">{item.duration}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {(data.reactive_6plus || []).length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                        <Clock className="w-10 h-10 mx-auto mb-2 opacity-30" />
                        <p className="font-medium">No reactive 6+ hour jobs found.</p>
                    </div>
                )}
            </div>
        </Modal>
    );
};

export default Reactive6PlusModal;
