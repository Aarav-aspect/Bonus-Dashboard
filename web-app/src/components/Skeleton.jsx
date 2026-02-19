import React from 'react';
import { Skeleton as ShadcnSkeleton } from "@/components/ui/skeleton"
import { Card } from "@/components/ui/card"

// Generic Skeleton Component (wrapping Shadcn)
export const Skeleton = ({ width, height, className, style }) => (
    <ShadcnSkeleton
        className={className}
        style={{ width, height, ...style }}
    />
);

// Performance Summary Skeleton
export const SummarySkeleton = () => (
    <div className="mb-10">
        <Skeleton width="280px" height="36px" className="mb-8 rounded-lg" />

        <div className="grid grid-cols-1 md:grid-cols-[2.2fr_1fr] gap-8">
            {/* Overall Score Card Skeleton */}
            <Card className="p-10 border-border shadow-md rounded-3xl flex flex-col justify-center bg-card">
                <Skeleton width="200px" height="14px" className="mb-4" />
                <Skeleton width="180px" height="64px" className="my-2" />
                <Skeleton width="100%" height="12px" className="mt-6 rounded-full" />
            </Card>

            {/* Bonus Card Skeleton */}
            <Card className="bg-brand-blue border-none shadow-md flex flex-col justify-between p-6 rounded-xl">
                <div>
                    <Skeleton width="140px" height="14px" className="mb-2 bg-white/20" />
                    <Skeleton width="120px" height="48px" className="my-2 bg-white/30" />
                </div>
                <div className="border-t border-white/15 pt-5 mt-auto">
                    <Skeleton width="100%" height="14px" className="mb-2 bg-white/20" />
                    <Skeleton width="100%" height="14px" className="bg-white/20" />
                </div>
            </Card>
        </div>
    </div>
);

// Category Block Skeleton
export const CategorySkeleton = () => (
    <div className="mb-6">
        <Card className="flex items-center justify-between p-8 border-border shadow-md rounded-2xl">
            <div className="flex flex-col gap-2">
                <Skeleton width="140px" height="20px" />
                <Skeleton width="120px" height="14px" />
            </div>
            <Skeleton width="60px" height="32px" />
        </Card>
    </div>
);

export default Skeleton;
