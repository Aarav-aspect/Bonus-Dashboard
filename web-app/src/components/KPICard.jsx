import React from 'react';
import { Card } from "@/components/ui/card"
import {
    Activity,
    Target,
    TrendingUp,
    CheckCircle,
    AlertCircle,
    Clock,
    DollarSign,
    Percent
} from 'lucide-react';

const KPICard = ({ label, value, score, onClick }) => {
    // Helper to format values
    const formatValue = (label, value) => {
        if (value === null || value === undefined) return "N/A";

        const isPct = label.includes("%");
        const isCurrency = label.includes("£") || label.includes("Value");
        const isRating = label.includes("Rating");

        if (typeof value === 'number') {
            if (isPct && !isRating) return `${value.toFixed(1)}%`;
            if (isRating) return value.toFixed(1);
            if (isCurrency) return `£${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
            return value.toLocaleString(undefined, { maximumFractionDigits: 1 });
        }
        return value;
    };

    // Helper: Get Icon based on label
    const getIcon = (label) => {
        const l = label.toLowerCase();
        if (l.includes('value') || l.includes('cost')) return <DollarSign className="h-4 w-4" />;
        if (l.includes('%') || l.includes('rate')) return <Percent className="h-4 w-4" />;
        if (l.includes('time') || l.includes('days')) return <Clock className="h-4 w-4" />;
        if (l.includes('score') || l.includes('rating')) return <Target className="h-4 w-4" />;
        return <Activity className="h-4 w-4" />;
    };

    // Handle value being an object (for drilldown) or a primitive
    const kpiData = typeof value === 'object' && value !== null ? value : { value };
    const actualValue = kpiData.value;
    const hasDrilldown = typeof value === 'object' && value !== null;

    const displayValue = formatValue(label, actualValue);

    // Determine colors
    let barColorClass = "bg-support-red";
    let borderColorClass = "border-l-support-red";
    let iconColorClass = "text-support-red bg-support-red/20"; // More opaque red

    if (score >= 70) {
        barColorClass = "bg-support-green";
        borderColorClass = "border-l-support-green";
        iconColorClass = "text-support-green bg-support-green/10";
    } else if (score >= 50) {
        barColorClass = "bg-support-orange";
        borderColorClass = "border-l-support-orange";
        iconColorClass = "text-support-orange bg-support-orange/10";
    }

    // Set a minimum width of 5% even for 0 scores so the red indicator is visible
    const barWidth = score ? Math.max(5, Math.min(100, score)) : 5;

    return (
        <Card
            className={`flex flex-col justify-between h-[160px] p-5 shadow-sm rounded-xl hover:shadow-md transition-all border border-black/5 border-l-[6px] ${borderColorClass} bg-white ${hasDrilldown ? 'cursor-pointer hover:bg-gray-50' : ''}`}
            onClick={() => hasDrilldown && onClick && onClick(kpiData)}
        >
            <div className="flex justify-between items-start">
                <div className="text-xs font-bold text-muted-foreground uppercase tracking-wider leading-tight pr-2">
                    {label}
                </div>
                <div className={`p-1.5 rounded-full ${iconColorClass}`}>
                    {getIcon(label)}
                </div>
            </div>

            <div className="text-3xl font-black text-foreground my-1 tracking-tight">
                {displayValue}
            </div>

            <div className="w-full h-2.5 bg-muted rounded-full overflow-hidden border border-black/5">
                <div
                    className={`h-full rounded-full transition-all duration-1000 ease-out ${barColorClass}`}
                    style={{
                        width: `${barWidth}%`
                    }}
                />
            </div>
        </Card>
    );
};

export default KPICard;
