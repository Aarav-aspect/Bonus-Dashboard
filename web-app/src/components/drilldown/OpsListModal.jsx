import React from 'react';
import Modal from '../common/Modal';
import { Users } from 'lucide-react';

const OpsListModal = ({ isOpen, onClose, data, tradeGroup }) => {
    if (!data) return null;

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            noBackdrop
            title={`Ops — ${tradeGroup}`}
        >
            <div className="flex flex-col gap-4 p-2">
                {/* Summary row */}
                <div className="grid grid-cols-1 gap-3">
                    <div className="p-3 rounded-xl bg-blue-50 border border-blue-200 text-center">
                        <div className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">Total Ops</div>
                        <div className="text-2xl font-black text-blue-600">{data.total_count}</div>
                    </div>
                </div>

                {/* Ops list */}
                <div className="max-h-[400px] overflow-y-auto rounded-xl border border-black/5">
                    <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-muted/80 backdrop-blur-sm z-10">
                            <tr className="border-b border-black/5">
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">#</th>
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Name</th>
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Trade</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.ops.map((op, i) => (
                                <tr key={i} className="border-b border-black/5 transition-colors hover:bg-muted/20">
                                    <td className="p-3 text-muted-foreground font-medium">{i + 1}</td>
                                    <td className="p-3 font-bold text-foreground">{op.name}</td>
                                    <td className="p-3 text-muted-foreground text-xs">{op.trade}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {data.ops.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                        <Users className="w-10 h-10 mx-auto mb-2 opacity-30" />
                        <p className="font-medium">No ops data available.</p>
                    </div>
                )}
            </div>
        </Modal>
    );
};

export default OpsListModal;
