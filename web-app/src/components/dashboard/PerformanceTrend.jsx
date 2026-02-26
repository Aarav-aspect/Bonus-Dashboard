import React from 'react';
import { LineChart, Card, Title, Text, Flex, Icon, BadgeDelta } from "@tremor/react";
import { TrendingUp, Loader2 } from 'lucide-react';

const valueFormatter = (number) => `£${Intl.NumberFormat("en-GB").format(number).toString()}`;
const scoreFormatter = (number) => `${number.toFixed(0)}%`;

const PerformanceTrend = ({ data, loading, onMonthSelect }) => {
    if (loading && data.length === 0) {
        return (
            <Card className="border-black/5 shadow-md rounded-3xl p-8 bg-white h-[450px] flex flex-col items-center justify-center">
                <Loader2 className="w-10 h-10 text-brand-blue animate-spin mb-4" />
                <Text className="font-bold">Analysing performance history...</Text>
            </Card>
        );
    }

    // Calculate delta if possible
    let deltaType = "unchanged";
    let deltaLabel = "0%";

    if (data.length >= 2) {
        const last = data[data.length - 1]["Bonus Percentage (%)"];
        const prev = data[data.length - 2]["Bonus Percentage (%)"];
        const diff = last - prev;

        if (diff > 0) deltaType = "moderateIncrease";
        else if (diff < 0) deltaType = "moderateDecrease";

        deltaLabel = `${diff > 0 ? '+' : ''}${diff.toFixed(1)}% vs prev. month`;
    }

    return (
        <Card className="border-black/5 shadow-md rounded-3xl p-8 bg-white animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Hidden Safelist for Tailwind v4 + Tremor */}
            <div className="hidden h-0 w-0">
                <div className="bg-indigo-500 text-indigo-500 fill-indigo-500 stroke-indigo-500 border-indigo-500 bg-indigo-500/10" />
            </div>

            <Flex alignItems="start" justifyContent="between">
                <div>
                    <Flex className="gap-2 mb-1">
                        <TrendingUp className="h-5 w-5 text-brand-blue" />
                        <Title className="text-xl font-black text-foreground tracking-tight">
                            Performance Trend
                        </Title>
                    </Flex>
                    <Text className="text-sm text-muted-foreground font-medium">
                        Bonus percentage trajectory across past 12 months
                    </Text>
                </div>
                {data.length >= 2 && (
                    <BadgeDelta deltaType={deltaType} className="font-black text-xs uppercase tracking-widest px-3 py-1">
                        {deltaLabel}
                    </BadgeDelta>
                )}
            </Flex>

            <LineChart
                className={`h-72 mt-10 transition-all duration-500 ${loading ? 'opacity-30' : 'opacity-100'}`}
                data={data}
                index="month"
                categories={["Bonus Percentage (%)"]}
                colors={["indigo"]}
                valueFormatter={scoreFormatter}
                showLegend={false}
                showGridLines={false}
                showAnimation={true}
                onValueChange={(v) => v && onMonthSelect(v.month)}
                curveType="natural"
                noDataText="No historic data available for this selection."
            />

            <div className="mt-6 pt-6 border-t border-black/5">
                <Text className="text-[10px] text-muted-foreground font-bold uppercase tracking-[0.2em] text-center">
                    💡 Click any point on the chart to view detailed KPI breakdown for that month
                </Text>
            </div>
        </Card>
    );
};

export default PerformanceTrend;
