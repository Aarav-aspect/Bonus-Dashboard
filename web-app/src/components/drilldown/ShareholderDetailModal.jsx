import React, { useEffect, useState } from 'react';
import Modal from '../common/Modal';
import { fetchShareholderGsheetData } from '../../api';

const fmt = (val) => new Intl.NumberFormat('en-GB', {
    style: 'currency', currency: 'GBP',
    minimumFractionDigits: 2, maximumFractionDigits: 2,
}).format(val || 0);

// Ordered rows as they appear in the Google Sheet
const UI_ROWS = [
    { key: 'Collections', type: 'currency', bold: false },
    { key: 'Labour', type: 'currency', bold: false },
    { key: 'Material', type: 'currency', bold: false },
    { key: 'Profit Margin<40', type: 'currency', bold: false },
    { key: 'Aged Debt Cost', type: 'currency', bold: false },
    { key: 'Aged Debt Collection', type: 'currency', bold: false },
    { key: 'Gross Profit', type: 'currency', bold: true },
    { key: 'Staff - Cost', type: 'currency', bold: false },
    { key: 'Unrecoverable - Cost', type: 'currency', bold: false },
    { key: 'PPC', type: 'currency', bold: false },
    { key: 'Profits After Cost', type: 'currency', bold: true },
    { key: '1% of Profit after cost', type: 'currency', bold: true },
    { key: 'Claims', type: 'count', bold: false, border: true },
    { key: 'Base Bonus Pot', type: 'currency', bold: false },
];

const ShareholderDetailModal = ({ isOpen, onClose, liveCollections, liveLabour, liveMaterials, tradeFilter, region, tradeGroup }) => {
    const [sheetData, setSheetData] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!isOpen) return;
        const hasSubgroupFilter = tradeFilter && tradeFilter !== 'All';
        const hasGroupMapping = !!tradeGroup;
        if (!hasSubgroupFilter && !hasGroupMapping) { setSheetData(null); return; }
        setLoading(true);
        fetchShareholderGsheetData(tradeFilter, region, tradeGroup)
            .then(res => setSheetData(res?.found ? res.data : null))
            .catch(() => setSheetData(null))
            .finally(() => setLoading(false));
    }, [isOpen, tradeFilter, region, tradeGroup]);

    const fallbackGP = (liveCollections || 0) - (liveLabour || 0) - (liveMaterials || 0);
    const fallbackPot = fallbackGP * 0.01;

    // Display name: prefer subgroup filter, otherwise use trade group name
    const displayName = (tradeFilter && tradeFilter !== 'All') ? tradeFilter : tradeGroup;
    const subtitle = displayName
        ? ` — ${displayName}${region && region !== 'All' ? ` (${region})` : ''}`
        : '';

    return (
        <Modal isOpen={isOpen} onClose={onClose} contentClassName="!bg-white border-border text-foreground max-w-lg">
            <div className="pt-2">
                <h2 className="text-2xl font-black text-brand-blue tracking-tight mb-6">
                    {displayName}{region && region !== 'All' ? ` (${region})` : ''}
                </h2>

                {loading && (
                    <div className="text-center py-8 text-muted-foreground text-sm">Loading…</div>
                )}

                {!loading && sheetData && (
                    <div className="space-y-1 text-base font-medium">
                        {UI_ROWS.map(({ key, type, bold, border }) => {
                            const val = sheetData[key];
                            if (val === undefined) return null;

                            const num = typeof val === 'number' ? val : parseFloat(val);
                            const isNegative = num < 0;
                            const valueColor = bold
                                ? 'text-brand-blue'
                                : (type === 'currency' && isNegative) ? 'text-support-red' : 'text-foreground';

                            return (
                                <div key={key} className={`flex justify-between items-center py-1 ${bold ? 'pt-4 pb-2' : ''} ${border ? 'pt-4 mt-2 border-t border-black/10' : ''}`}>
                                    <span className={bold ? 'font-black text-lg text-brand-blue' : 'text-muted-foreground'}>
                                        {key}
                                    </span>
                                    <span className={`${bold ? 'font-black text-xl' : 'font-bold'} ${valueColor}`}>
                                        {type === 'currency' ? fmt(num) : val}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                )}

                {!loading && !sheetData && (
                    <div className="space-y-2 text-base font-medium">
                        <div className="flex justify-between items-center py-1">
                            <span className="font-bold text-foreground">Collection Total</span>
                            <span className="font-black text-foreground text-lg">{fmt(liveCollections)}</span>
                        </div>
                        <div className="flex justify-between items-center py-1">
                            <span className="text-muted-foreground">Labour Cost</span>
                            <span className="font-bold text-support-red">-{fmt(liveLabour)}</span>
                        </div>
                        <div className="flex justify-between items-center py-1">
                            <span className="text-muted-foreground">Material Cost</span>
                            <span className="font-bold text-support-red">-{fmt(liveMaterials)}</span>
                        </div>
                        <div className="flex justify-between items-center pt-4 pb-2">
                            <span className="text-brand-blue font-black text-lg">Gross Profit</span>
                            <span className="font-black text-brand-blue text-xl">{fmt(fallbackGP)}</span>
                        </div>
                        <div className="flex justify-between items-center pt-2">
                            <span className="text-foreground font-black text-lg">1% of Profit (Pot)</span>
                            <span className="font-black text-foreground text-xl">{fmt(fallbackPot)}</span>
                        </div>
                    </div>
                )}
            </div>
        </Modal>
    );
};

export default ShareholderDetailModal;
