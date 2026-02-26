import React from 'react';
import Modal from '../common/Modal';
import { Users } from 'lucide-react';

const ReviewsDetailModal = ({ isOpen, onClose, data, tradeGroup }) => {
    if (!data) return null;

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={`Reviews — ${tradeGroup}`}
            noBackdrop
        >
            <div className="flex flex-col gap-4 p-2">
                {/* Summary row */}
                <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-xl bg-muted/30 border border-black/5 text-center">
                        <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Total Reviews</div>
                        <div className="text-2xl font-black text-foreground">{data.total_count}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-blue-50 border border-blue-200 text-center">
                        <div className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">Average</div>
                        <div className="text-2xl font-black text-blue-600">{data.avg_rating ?? '—'}</div>
                    </div>
                </div>

                {/* Review list */}
                <div className="max-h-[400px] overflow-y-auto rounded-xl border border-black/5">
                    <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-muted/80 backdrop-blur-sm z-10">
                            <tr className="border-b border-black/5">
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">#</th>
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">SA Number</th>
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Rating</th>
                                <th className="text-left p-3 font-bold text-muted-foreground uppercase tracking-wider text-[10px] w-1/4"></th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.reviews.map((review, i) => {
                                const scoreColor = review.rating >= 4 ? 'text-green-600' : review.rating >= 3 ? 'text-yellow-600' : 'text-red-600';
                                const barColor = review.rating >= 4 ? 'bg-green-500' : review.rating >= 3 ? 'bg-yellow-500' : 'bg-red-500';
                                const barWidth = `${Math.min((review.rating / 5) * 100, 100)}%`;
                                return (
                                    <tr key={i} className="border-b border-black/5 transition-colors hover:bg-muted/20">
                                        <td className="p-3 text-muted-foreground font-medium">{i + 1}</td>
                                        <td className="p-3 font-bold text-foreground">{review.sa_number}</td>
                                        <td className="p-3">
                                            <span className={`font-black ${scoreColor}`}>{Math.round(review.rating)}</span>
                                            <span className="text-muted-foreground/40 text-xs ml-0.5">/5</span>
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

                {data.reviews.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                        <Users className="w-10 h-10 mx-auto mb-2 opacity-30" />
                        <p className="font-medium">No reviews available.</p>
                    </div>
                )}
            </div>
        </Modal>
    );
};

export default ReviewsDetailModal;
