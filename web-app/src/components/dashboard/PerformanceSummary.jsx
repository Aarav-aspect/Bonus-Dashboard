import React, { useState } from 'react';
import { Card } from "@/components/ui/card"
import AspectLogo from '@/assets/aspectLogoIcon.svg';
import ShareholderDetailModal from '../drilldown/ShareholderDetailModal';
import { calculateLiveBonusPot } from '../../utils/liveBonusPot';

const PerformanceSummary = ({ overallScore, bonus, liveCollections, liveLabour, liveMaterials, tradeFilter, region, tradeGroup, showTitle = true }) => {
    const [isShareholderModalOpen, setIsShareholderModalOpen] = useState(false);

    // Determine color class based on score
    let progressColorClass = "bg-support-red";
    if (overallScore >= 70) progressColorClass = "bg-support-green";
    else if (overallScore >= 50) progressColorClass = "bg-support-orange";

    // Shareholder Calculations
    const { liveBasePot: shareholderBasePot, liveBonusPot: shareholderCurrent } = calculateLiveBonusPot({
        live_collections: liveCollections,
        live_labour: liveLabour,
        live_materials: liveMaterials,
        bonus
    });

    const shareholderMax = shareholderBasePot * 1.3;

    return (
        <div className="mb-10">
            {showTitle && (
                <h1 className="text-4xl font-black mb-8 text-foreground tracking-tight">
                    Bonus Summary
                </h1>
            )}

            <div className="grid grid-cols-1 md:grid-cols-[1.8fr_1fr] gap-8">
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

                {/* Bonus Card (HIDDEN AS REQUESTED)
                <Card className="relative overflow-hidden bg-brand-blue border-none shadow-md flex flex-col justify-between p-6 rounded-3xl">
                    <span className="absolute right-[-10px] top-[-10px] h-32 w-32 text-white/10 rotate-12 text-[10rem] font-bold leading-none select-none">£</span>

                    <div className="relative z-10 flex gap-4 items-start">
                        <div className="flex-1">
                            <div className="text-sm text-white/80 font-bold uppercase tracking-wider">
                                Current Bonus
                            </div>
                            <div className="text-4xl font-black my-3 text-white tracking-tight">
                                £{bonus?.bonus_value?.toLocaleString(undefined, { maximumFractionDigits: 0 }) || 0}
                            </div>
                        </div>

                        <div className="w-px self-stretch bg-white/15 mx-1" />

                        <div className="flex-1 opacity-0 pointer-events-none">
                            <div className="text-sm text-white/80 font-bold uppercase tracking-wider">
                                Max Bonus
                            </div>
                            <div className="text-4xl font-black my-3 text-brand-yellow tracking-tight">
                            </div>
                        </div>
                    </div>

                    <div className="relative z-10 border-t border-white/15 pt-5 mt-auto">
                        <div className="flex justify-between text-sm text-white mb-2 opacity-90">
                        </div>
                        <div className="flex justify-between text-sm text-brand-yellow">
                            <span className="font-bold">Adjustment</span>
                            <strong className="font-black">{bonus?.multiplier > 0 ? '+' : ''}{(bonus?.multiplier * 100).toFixed(0)}%</strong>
                        </div>
                    </div>
                </Card>
                */}

                {/* Shareholder Card */}
                <Card
                    className={`relative overflow-hidden bg-brand-blue border-none shadow-md flex flex-col justify-between p-6 rounded-3xl transition-all duration-300 group ${bonus?.bonus_pot_unavailable ? 'cursor-default' : 'cursor-pointer hover:-translate-y-1 hover:shadow-xl'}`}
                    onClick={() => !bonus?.bonus_pot_unavailable && setIsShareholderModalOpen(true)}
                >

                    <img
                        src={AspectLogo}
                        alt=""
                        className="absolute opacity-10 rotate-12 transition-transform duration-500 group-hover:scale-110 pointer-events-none select-none"
                        style={{ right: '-50px', top: '-20px', width: '260px', height: '260px' }}
                    />
                    {bonus?.bonus_pot_unavailable ? (
                        <div className="relative z-10 flex flex-col justify-center items-center h-full py-6 text-center">
                            <div className="text-white/60 font-bold uppercase tracking-wider text-sm mb-3">Bonus Pot</div>
                            <div className="text-white font-black text-xl">
                                Not available for {bonus.bonus_pot_unavailable}
                            </div>
                        </div>
                    ) : (
                        <>
                            <div className="relative z-10 flex gap-4 items-start">
                                {/* Current Bonus */}
                                <div className="flex-1">
                                    <div className="text-sm text-white/80 font-bold uppercase tracking-wider">
                                        Current Bonus
                                    </div>
                                    <div className="text-4xl font-black my-3 text-white tracking-tight group-hover:scale-[1.02] transition-transform origin-left">
                                        £{shareholderCurrent.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                                    </div>
                                </div>

                                {/* Divider */}
                                <div className="w-px self-stretch bg-white/15 mx-1" />

                                {/* Max Bonus */}
                                <div className="flex-1">
                                    <div className="text-sm text-white/80 font-bold uppercase tracking-wider">
                                        Max Bonus
                                    </div>
                                    <div className="text-4xl font-black my-3 text-brand-yellow tracking-tight group-hover:scale-[1.02] transition-transform origin-left">
                                        £{shareholderMax.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                                    </div>
                                </div>
                            </div>

                            <div className="relative z-10 border-t border-white/15 pt-5 mt-auto">
                                <div className="flex justify-between text-sm text-white mb-2 opacity-90">
                                    <span className="font-medium">Base Pot</span>
                                    <strong className="font-bold">£{shareholderBasePot.toLocaleString(undefined, { maximumFractionDigits: 0 })}</strong>
                                </div>
                                <div className="flex justify-between text-sm text-brand-yellow">
                                    <span className="font-bold">Adjustment</span>
                                    <strong className="font-black">{bonus?.multiplier > 0 ? '+' : ''}{(bonus?.multiplier * 100).toFixed(0)}%</strong>
                                </div>
                            </div>
                        </>
                    )}
                </Card>
            </div>

            <ShareholderDetailModal
                isOpen={isShareholderModalOpen}
                onClose={() => setIsShareholderModalOpen(false)}
                liveCollections={liveCollections}
                liveLabour={liveLabour}
                liveMaterials={liveMaterials}
                tradeFilter={tradeFilter}
                region={region}
                tradeGroup={tradeGroup}
            />
        </div>
    );
};

export default PerformanceSummary;
