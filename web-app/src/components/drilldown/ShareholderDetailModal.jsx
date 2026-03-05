import React from 'react';
import Modal from '../common/Modal';

const ShareholderDetailModal = ({ isOpen, onClose, liveCollections, liveLabour, liveMaterials }) => {
    const grossProfit = (liveCollections || 0) - (liveLabour || 0) - (liveMaterials || 0);
    const basePot = grossProfit * 0.01;

    // Formatting helper
    const formatCurrency = (val) => {
        return new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(val || 0);
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            contentClassName="!bg-white border-border text-foreground max-w-lg"
        >
            <div className="pt-2">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-black text-brand-blue tracking-tight">
                        Shareholder Breakdown
                    </h2>
                </div>

                <div className="space-y-2 text-base font-medium">
                    {/* Collection Total */}
                    <div className="flex justify-between items-center py-1">
                        <span className="font-bold text-foreground">Collection Total</span>
                        <span className="font-black text-foreground text-lg">{formatCurrency(liveCollections)}</span>
                    </div>

                    {/* Labour */}
                    <div className="flex justify-between items-center py-1">
                        <span className="text-muted-foreground">Labour Cost</span>
                        <span className="font-bold text-support-red">-{formatCurrency(liveLabour)}</span>
                    </div>

                    {/* Material */}
                    <div className="flex justify-between items-center py-1">
                        <span className="text-muted-foreground">Material Cost</span>
                        <span className="font-bold text-support-red">-{formatCurrency(liveMaterials)}</span>
                    </div>

                    {/* Gross Profit */}
                    <div className="flex justify-between items-center pt-4 pb-2">
                        <span className="text-brand-blue font-black text-lg">Gross Profit</span>
                        <span className="font-black text-brand-blue text-xl">{formatCurrency(grossProfit)}</span>
                    </div>

                    {/* 1% as Pot */}
                    <div className="flex justify-between items-center pt-2">
                        <span className="text-foreground font-black text-lg">1% of Profit (Pot)</span>
                        <span className="font-black text-foreground text-xl">{formatCurrency(basePot)}</span>
                    </div>
                </div>
            </div>
        </Modal>
    );
};

export default ShareholderDetailModal;
