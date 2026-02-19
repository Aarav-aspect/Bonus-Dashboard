import React from 'react';
import { Card } from "@/components/ui/card"
import { Coins } from 'lucide-react';

const PerformanceSummary = ({ overallScore, bonus, showTitle = true }) => {
    // Determine color class based on score
    let progressColorClass = "bg-support-red";
    if (overallScore >= 80) progressColorClass = "bg-support-green";
    else if (overallScore >= 60) progressColorClass = "bg-support-orange";

    return (
        <div className="mb-10">
            {showTitle && (
                <h1 className="text-4xl font-black mb-8 text-foreground tracking-tight">
                    Bonus Summary
                </h1>
            )}

            <div className="grid grid-cols-1 md:grid-cols-[2.2fr_1fr] gap-8">
                {/* Overall Score Card */}
                <Card className="relative overflow-hidden p-10 border-black/5 shadow-md rounded-3xl flex flex-col justify-center bg-white">
                    {/* Watermark Icon */}


                    <div className="relative z-10">
                        <div className="text-sm text-muted-foreground font-bold mb-4 uppercase tracking-wider flex items-center gap-2">
                            Overall Performance Score
                        </div>
                        <div className="text-[5rem] font-black text-foreground leading-none my-2 tracking-tighter">
                            {overallScore !== null ? `${overallScore.toFixed(0)}%` : 'N/A'}
                        </div>
                        {overallScore !== null && (
                            <div className="w-full h-4 bg-muted rounded-full mt-6 overflow-hidden border border-black/5">
                                <div
                                    className={`h-full rounded-full transition-all duration-1000 ease-out ${progressColorClass}`}
                                    style={{
                                        width: `${overallScore}%`
                                    }}
                                />
                            </div>
                        )}
                    </div>
                </Card>

                {/* Bonus Card */}
                <Card className="relative overflow-hidden bg-brand-blue border-none shadow-md flex flex-col justify-between p-6 rounded-3xl">
                    {/* Watermark Icon */}
                    <Coins className="absolute right-[-10px] top-[-10px] h-32 w-32 text-white/10 rotate-12" />

                    <div className="relative z-10 flex gap-4 items-start">
                        {/* Current Bonus */}
                        <div className="flex-1">
                            <div className="text-sm text-white/80 font-bold uppercase tracking-wider">
                                Current Bonus
                            </div>
                            <div className="text-4xl font-black my-3 text-white tracking-tight">
                                £{bonus?.bonus_value?.toLocaleString(undefined, { maximumFractionDigits: 0 }) || 0}
                            </div>
                        </div>

                        {/* Divider */}
                        <div className="w-px self-stretch bg-white/15 mx-1" />

                        {/* Max Bonus */}
                        <div className="flex-1">
                            <div className="text-sm text-white/80 font-bold uppercase tracking-wider">
                                Max Bonus
                            </div>
                            <div className="text-4xl font-black my-3 text-brand-yellow tracking-tight">
                                £{bonus?.pot ? (bonus.pot * 1.3).toLocaleString(undefined, { maximumFractionDigits: 0 }) : 0}
                            </div>
                        </div>
                    </div>

                    <div className="relative z-10 border-t border-white/15 pt-5 mt-auto">
                        <div className="flex justify-between text-sm text-white mb-2 opacity-90">
                            <span className="font-medium">Base Pot</span>
                            <strong className="font-bold">£{bonus?.pot?.toLocaleString(undefined, { maximumFractionDigits: 0 })}</strong>
                        </div>
                        <div className="flex justify-between text-sm text-brand-yellow">
                            <span className="font-bold">Adjustment</span>
                            <strong className="font-black">{(bonus?.multiplier * 100).toFixed(1)}%</strong>
                        </div>
                    </div>

                </Card>
            </div>
        </div>
    );
};

export default PerformanceSummary;
