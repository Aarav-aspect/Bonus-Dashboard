import React from 'react';
import Modal from '../common/Modal';
import { Users, AlertTriangle, CheckCircle2 } from 'lucide-react';

const DriversDetailModal = ({ isOpen, onClose, data, tradeGroup }) => {
    if (!data) return null;

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            noBackdrop
            title={`Drivers — ${tradeGroup}`}
        >
            <div className="flex flex-col gap-4 p-2">
                {/* Summary row */}
                <div className="grid grid-cols-3 gap-3">
                    <div className="p-3 rounded-xl bg-muted/30 border border-black/5 text-center">
                        <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Total</div>
                        <div className="text-2xl font-black text-foreground">{data.total_count}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-center">
                        <div className="text-[10px] font-bold text-red-600 uppercase tracking-wider flex items-center justify-center gap-1">
                            <AlertTriangle className="w-3 h-3" /> Below 7
                        </div>
                        <div className="text-2xl font-black text-red-600">{data.below_7_count}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-green-50 border border-green-200 text-center">
                        <div className="text-[10px] font-bold text-green-600 uppercase tracking-wider flex items-center justify-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> Pass
                        </div>
                        <div className="text-2xl font-black text-green-600">{data.total_count - data.below_7_count}</div>
                    </div>
                </div>

                {/* Driver list */}
                <div className="max-h-[400px] overflow-y-auto rounded-xl border border-black/5">
                    <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-muted/80 backdrop-blur-sm z-10">
                            <tr className="border-b border-black/5">
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">#</th>
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Name</th>
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Trade</th>
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Score</th>
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px] w-1/5"></th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.drivers.map((driver, i) => {
                                const scoreColor = driver.score >= 8 ? 'text-green-600' : driver.score >= 7 ? 'text-yellow-600' : 'text-red-600';
                                const barColor = driver.score >= 8 ? 'bg-green-500' : driver.score >= 7 ? 'bg-yellow-500' : 'bg-red-500';
                                const barWidth = `${Math.min((driver.score / 10) * 100, 100)}%`;
                                return (
                                    <tr key={i} className={`border-b border-black/5 transition-colors hover:bg-muted/20 ${driver.below_threshold ? 'bg-red-50/40' : ''}`}>
                                        <td className="p-3 text-muted-foreground font-medium">{i + 1}</td>
                                        <td className="p-3 font-bold text-foreground">{driver.name}</td>
                                        <td className="p-3 text-muted-foreground text-xs">{driver.trade}</td>
                                        <td className="p-3">
                                            <span className={`font-black ${scoreColor}`}>{driver.score.toFixed(1)}</span>
                                            <span className="text-muted-foreground/40 text-xs ml-0.5">/10</span>
                                        </td>
                                        <td className="p-3">
                                            <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                                                <div className={`h-full rounded-full ${barColor}`} style={{ width: barWidth }} />
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>

                {data.drivers.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                        <Users className="w-10 h-10 mx-auto mb-2 opacity-30" />
                        <p className="font-medium">No driver data available.</p>
                    </div>
                )}
            </div>
        </Modal>
    );
};

export default DriversDetailModal;
