import React from 'react';
import Modal from '../common/Modal';
import { Star, MessageSquare, Award } from 'lucide-react';

const ReviewsDetailModal = ({ isOpen, onClose, data, tradeGroup }) => {
    if (!data) return null;

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={`Reviews — ${tradeGroup}`}
            maxWidth="max-w-4xl"
        >
            <div className="flex flex-col gap-6 p-2">
                {/* Summary row */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-2xl bg-gray-50 border border-black/5 text-center shadow-sm">
                        <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1 flex items-center justify-center gap-1.5">
                            <MessageSquare className="w-3.5 h-3.5" /> Total Reviews
                        </div>
                        <div className="text-3xl font-black text-gray-900">{data.total_count}</div>
                    </div>
                    <div className="p-4 rounded-2xl bg-blue-50/50 border border-blue-100 text-center shadow-sm">
                        <div className="text-[10px] font-bold text-blue-600 uppercase tracking-widest mb-1 flex items-center justify-center gap-1.5">
                            <Award className="w-3.5 h-3.5" /> Average Rating
                        </div>
                        <div className="text-3xl font-black text-blue-600 flex items-center justify-center gap-2">
                            {data.avg_rating ?? '—'}
                            {data.avg_rating && <Star className="w-6 h-6 fill-blue-600" />}
                        </div>
                    </div>
                </div>

                {/* Review list */}
                <div className="max-h-[50vh] overflow-y-auto rounded-2xl border border-black/5 bg-white shadow-sm overflow-hidden">
                    <table className="w-full text-sm">
                        <thead className="sticky top-0 bg-gray-50/90 backdrop-blur-md z-10">
                            <tr className="border-b border-black/5">
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">#</th>
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">SA Number</th>
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px]">Rating</th>
                                <th className="text-left py-4 px-6 font-bold text-muted-foreground uppercase tracking-wider text-[10px] w-1/3">Performance</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-black/5">
                            {(data.reviews || []).map((review, i) => {
                                const rating = Math.round(review.rating);
                                const scoreColor = rating >= 4 ? 'text-green-600' : rating >= 3 ? 'text-yellow-600' : 'text-red-600';
                                const barColor = rating >= 4 ? 'bg-green-500' : rating >= 3 ? 'bg-yellow-500' : 'bg-red-500';
                                const barWidth = `${Math.min((rating / 5) * 100, 100)}%`;

                                return (
                                    <tr key={i} className="transition-colors hover:bg-brand-blue/5">
                                        <td className="py-4 px-6 text-muted-foreground font-medium">{i + 1}</td>
                                        <td className="py-4 px-6 font-bold text-gray-900">{review.sa_number}</td>
                                        <td className="py-4 px-6">
                                            <div className="flex items-center gap-1">
                                                <span className={`text-lg font-black ${scoreColor}`}>{rating}</span>
                                                <div className="flex gap-0.5">
                                                    {[...Array(5)].map((_, starIdx) => (
                                                        <Star
                                                            key={starIdx}
                                                            className={`w-3 h-3 ${starIdx < rating ? `fill-current ${scoreColor}` : 'text-gray-200 fill-gray-200'}`}
                                                        />
                                                    ))}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="py-4 px-6">
                                            <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden shadow-inner">
                                                <div className={`h-full rounded-full transition-all duration-500 ${barColor}`} style={{ width: barWidth }} />
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>

                {(!data.reviews || data.reviews.length === 0) && (
                    <div className="text-center py-12 text-muted-foreground bg-gray-50/50 rounded-2xl border border-dashed border-black/10">
                        <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-20" />
                        <p className="font-medium text-lg">No reviews available.</p>
                    </div>
                )}
            </div>
        </Modal>
    );
};

export default ReviewsDetailModal;
