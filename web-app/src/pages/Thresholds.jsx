import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchTradeGroups, fetchTradeSubgroups, fetchBonusPots, saveBonusPots, fetchKPIConfig, saveKPIConfig, updateDynamicThreshold, updateDynamicThresholdAll } from '../api';
import Header from '../components/layout/Header';
import { useAuth } from '../context/AuthContext';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";

const Thresholds = () => {
    // DATA
    const [tradeGroups, setTradeGroups] = useState({});
    const [tradeSubgroups, setTradeSubgroups] = useState({}); // Stores trades per group
    const [bonusPots, setBonusPots] = useState({});
    const [kpiConfig, setKpiConfig] = useState({});

    // UI selections
    const [potGroup, setPotGroup] = useState("");
    const [potTrade, setPotTrade] = useState("__ALL__");
    const [selectedGroup, setSelectedGroup] = useState("");
    const [selectedKpi, setSelectedKpi] = useState("");
    const [selectedTrade, setSelectedTrade] = useState(""); // For dynamic KPIs

    // Edit States
    const [newPotValue, setNewPotValue] = useState(0);
    const [thresholds, setThresholds] = useState([]);
    const [gridThresholds, setGridThresholds] = useState({}); // Array of {min/max, score} or just values for dynamic

    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState(null);

    useEffect(() => {
        async function load() {
            try {
                const [g, sg, pots, kpis] = await Promise.all([
                    fetchTradeGroups(),
                    fetchTradeSubgroups(),
                    fetchBonusPots(),
                    fetchKPIConfig()
                ]);
                setTradeGroups(g);
                setTradeSubgroups(sg);
                setBonusPots(pots);
                setKpiConfig(kpis);

                const groups = Object.keys(g);
                if (groups.length > 0) {
                    setPotGroup(groups[0]);
                    setSelectedGroup("__ALL__");
                }
            } catch (e) {
                console.error(e);
                setMessage({ type: 'error', text: 'Failed to load config data.' });
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    // Sync Pot Value when group or trade changes
    useEffect(() => {
        if (potGroup && bonusPots) {
            if (potTrade && potTrade !== "__ALL__") {
                // Try trade-specific key first
                const tradeKey = `${potGroup}::${potTrade}`;
                setNewPotValue(bonusPots[tradeKey] ?? bonusPots[potGroup] ?? 0);
            } else {
                setNewPotValue(bonusPots[potGroup] || 0);
            }
        }
    }, [potGroup, potTrade, bonusPots]);

    // Available KPIs for selected group
    const availableKpis = Object.keys(kpiConfig).filter(kpi => {
        const cfg = kpiConfig[kpi];
        if (selectedGroup === "__ALL__") return true; // All KPIs visible for "All" selection
        if (cfg.dynamic && cfg.dynamic.thresholds_by_trade) {
            const groupTrades = tradeGroups[selectedGroup] || [];
            return groupTrades.some(t => t in cfg.dynamic.thresholds_by_trade);
        }
        return true;
    });

    // Default KPI selection
    useEffect(() => {
        if (availableKpis.length > 0 && !availableKpis.includes(selectedKpi)) {
            setSelectedKpi(availableKpis[0]);
        }
    }, [selectedGroup, availableKpis]);

    // Trade mapping for dynamic KPIs: Dashboard Detailed Trade -> Backend Config Key
    const TRADE_TO_DYNAMIC_KEY = {
        "Air Conditioning": "HVAC",
        "Gas & Heating": "HVAC",
        "Electrical": "Electrical",
        "Plumbing": "Plumbing",
        "Plumbing & Cold Water": "Plumbing"
    };

    // Load Thresholds when KPI or Trade changes
    useEffect(() => {
        if (selectedKpi && kpiConfig[selectedKpi]) {
            const cfg = kpiConfig[selectedKpi];

            // Dynamic KPI - load trade-specific thresholds
            if (cfg.dynamic && cfg.dynamic.type === 'trade_based') {
                if (selectedGroup === "__ALL__") {
                    // For "All", load the first available trade's thresholds as a starting point
                    const firstTrade = Object.keys(cfg.dynamic.thresholds_by_trade || {})[0];
                    const existing = firstTrade ? cfg.dynamic.thresholds_by_trade[firstTrade] : null;
                    if (existing && existing.length > 0) {
                        setThresholds(existing);
                    } else if (cfg.dynamic.scores) {
                        setThresholds(new Array(cfg.dynamic.scores.length).fill(0));
                    } else {
                        setThresholds([]);
                    }
                    setGridThresholds({});
                    return;
                }

                // Get allowed detail trades for this group
                const allowedTrades = Object.keys(tradeSubgroups[selectedGroup] || {});
                const effectiveTrades = [selectedGroup, ...allowedTrades];

                // Ensure selectedTrade is valid for this group
                let activeTrade = selectedTrade;

                // If current selection is not valid for this group, default to Group Name
                if (!effectiveTrades.includes(activeTrade)) {
                    activeTrade = selectedGroup;
                    setSelectedTrade(activeTrade);
                }

                // Map the active UI trade to the config key (e.g. "Air Conditioning" -> "HVAC")
                let configKey = activeTrade;
                if (activeTrade !== selectedGroup && TRADE_TO_DYNAMIC_KEY[activeTrade]) {
                    configKey = TRADE_TO_DYNAMIC_KEY[activeTrade];
                }

                if (activeTrade === selectedGroup) {
                    // GRID MODE
                    const newGrid = {};
                    const scoresLen = cfg.dynamic.scores ? cfg.dynamic.scores.length : 0;
                    allowedTrades.forEach(t => {
                        const ck = TRADE_TO_DYNAMIC_KEY[t] || t;
                        const existing = cfg.dynamic.thresholds_by_trade?.[ck];
                        if (existing && existing.length > 0) {
                            newGrid[t] = [...existing];
                        } else {
                            newGrid[t] = new Array(scoresLen).fill(0);
                        }
                    });
                    newGrid["All"] = new Array(scoresLen).fill('');
                    setGridThresholds(newGrid);
                    setThresholds([]);
                } else {
                    const existingThresholds = cfg.dynamic.thresholds_by_trade?.[configKey];

                    if (existingThresholds && existingThresholds.length > 0) {
                        setThresholds(existingThresholds);
                    } else if (cfg.dynamic.scores) {
                        setThresholds(new Array(cfg.dynamic.scores.length).fill(0));
                    } else {
                        setThresholds([]);
                    }
                    setGridThresholds({});
                }
            }
            // Static KPI - load regular thresholds
            else if (cfg.thresholds) {
                const sorted = [...cfg.thresholds].sort((a, b) => {
                    if (cfg.direction === 'higher_is_better') return b.min - a.min;
                    return a.max - b.max;
                });
                setThresholds(sorted);
                setGridThresholds({});
            } else {
                setThresholds([]);
                setGridThresholds({});
            }
        }
    }, [selectedKpi, selectedGroup, kpiConfig, selectedTrade]);


    // HANDLERS
    const handleSavePot = async () => {
        const key = (potTrade && potTrade !== "__ALL__") ? `${potGroup}::${potTrade}` : potGroup;
        const updated = { ...bonusPots, [key]: parseFloat(newPotValue) };
        try {
            await saveBonusPots(updated);
            setBonusPots(updated);
            const label = (potTrade && potTrade !== "__ALL__") ? `${potTrade} (${potGroup})` : potGroup;
            setMessage({ type: 'success', text: `Saved bonus pot for ${label}` });
        } catch (e) {
            setMessage({ type: 'error', text: 'Failed to save bonus pot.' });
        }
    };

    const handleThresholdChange = (index, field, value) => {
        const newThresholds = [...thresholds];
        newThresholds[index] = { ...newThresholds[index], [field]: parseFloat(value) };
        setThresholds(newThresholds);
    };

    const handleGridChange = (trade, scoreIdx, value) => {
        const newGrid = { ...gridThresholds };
        const parsed = parseFloat(value);
        if (trade === "All") {
            newGrid["All"] = [...newGrid["All"]];
            newGrid["All"][scoreIdx] = value;
        } else {
            newGrid[trade] = [...newGrid[trade]];
            newGrid[trade][scoreIdx] = isNaN(parsed) ? 0 : parsed;
        }
        setGridThresholds(newGrid);
    };

    const handleSaveThresholds = async () => {
        const cfg = kpiConfig[selectedKpi];
        const payload = thresholds; // The current state of thresholds to be saved
        const newConfig = { ...kpiConfig }; // Create a mutable copy

        try {
            // Dynamic KPI - save trade-specific thresholds
            if (cfg.dynamic && cfg.dynamic.type === 'trade_based') {
                const isAll = selectedTrade === selectedGroup; // "All Trades" option maps to the group name
                if (selectedGroup === "__ALL__") {
                    // Save to ALL trade groups at once
                    await updateDynamicThresholdAll(selectedKpi, payload);
                    // Update local config for all trades in all groups
                    Object.keys(tradeGroups).forEach(groupName => {
                        const tradesForGroup = Object.keys(tradeSubgroups[groupName] || {});
                        tradesForGroup.forEach(t => {
                            const configKey = TRADE_TO_DYNAMIC_KEY[t] || t;
                            if (!newConfig[selectedKpi].dynamic.thresholds_by_trade) {
                                newConfig[selectedKpi].dynamic.thresholds_by_trade = {};
                            }
                            newConfig[selectedKpi].dynamic.thresholds_by_trade[configKey] = payload;
                        });
                        // Also update the group-level entry if it exists
                        if (!newConfig[selectedKpi].dynamic.thresholds_by_trade) {
                            newConfig[selectedKpi].dynamic.thresholds_by_trade = {};
                        }
                        newConfig[selectedKpi].dynamic.thresholds_by_trade[groupName] = payload;
                    });
                    setMessage({ type: 'success', text: `Saved thresholds for ${selectedKpi} across all trade groups` });
                } else if (isAll) {
                    // We are in Grid Mode for a specific group
                    const tradesForGroup = Object.keys(tradeSubgroups[selectedGroup] || {});

                    if (!newConfig[selectedKpi].dynamic.thresholds_by_trade) {
                        newConfig[selectedKpi].dynamic.thresholds_by_trade = {};
                    }

                    // Save each trade individually
                    await Promise.all(tradesForGroup.map(async (t) => {
                        const configKey = TRADE_TO_DYNAMIC_KEY[t] || t;
                        const rawPayload = gridThresholds[t] || [];
                        const tradePayload = rawPayload.map(val => {
                            const num = parseFloat(val);
                            return isNaN(num) ? 0 : num;
                        });

                        await updateDynamicThreshold(selectedKpi, configKey, tradePayload);
                        newConfig[selectedKpi].dynamic.thresholds_by_trade[configKey] = tradePayload;
                    }));

                    // Optional: update the fallback group key (from the 'All' column)
                    const rawAllPayload = gridThresholds["All"] || [];
                    const allPayload = rawAllPayload.map(val => {
                        const num = parseFloat(val);
                        return isNaN(num) ? 0 : num;
                    });
                    newConfig[selectedKpi].dynamic.thresholds_by_trade[selectedGroup] = allPayload;
                    await updateDynamicThresholdAll(selectedKpi, allPayload);

                    setMessage({ type: 'success', text: `Saved thresholds for all trades in ${selectedGroup} for ${selectedKpi}` });
                } else {
                    // Determine the config key for the specific trade
                    const configKey = TRADE_TO_DYNAMIC_KEY[selectedTrade] || selectedTrade;
                    await updateDynamicThreshold(selectedKpi, configKey, payload);
                    if (!newConfig[selectedKpi].dynamic.thresholds_by_trade) {
                        newConfig[selectedKpi].dynamic.thresholds_by_trade = {};
                    }
                    newConfig[selectedKpi].dynamic.thresholds_by_trade[configKey] = payload;
                    setMessage({ type: 'success', text: `Saved ${selectedTrade} thresholds for ${selectedKpi}` });
                }
                setKpiConfig(newConfig); // Update state with the modified config
            }
            // Static KPI - save regular thresholds (always global)
            else {
                const updatedConfig = { ...kpiConfig };
                updatedConfig[selectedKpi] = { ...updatedConfig[selectedKpi], thresholds: thresholds };
                await saveKPIConfig(updatedConfig);
                setKpiConfig(updatedConfig);
                setMessage({ type: 'success', text: `Saved thresholds for ${selectedKpi}` });
            }
        } catch (e) {
            setMessage({ type: 'error', text: 'Failed to save thresholds.' });
        }
    };


    if (loading) return (
        <div className="min-h-screen flex items-center justify-center bg-white">
            <div className="text-muted-foreground font-bold animate-pulse">Loading Configuration...</div>
        </div>
    );

    const currentKpiConfig = kpiConfig[selectedKpi];
    const isDynamic = currentKpiConfig?.dynamic;

    return (
        <div className="min-h-screen bg-white pb-20 font-sans">
            <div className="container mx-auto px-6 py-8">

                {/* Unified Header */}
                <Header
                    tradeGroups={tradeGroups}
                    selectedGroup={selectedGroup}
                    onGroupChange={setSelectedGroup}
                    showMonthFilter={false}
                    showGroupFilter={false}
                />

                <h1 className="text-3xl font-black text-foreground tracking-tight mb-8">
                    Threshold Management
                </h1>


                {/* Message Banner */}
                {message && (
                    <div className={`p-4 mb-8 rounded-xl flex items-center gap-3 font-bold border ${message.type === 'error' ? 'bg-destructive/10 text-destructive border-destructive/20' : 'bg-green-50 text-green-700 border-green-200'}`}>
                        <span>{message.type === 'error' ? '⚠️' : '✅'}</span>
                        {message.text}
                    </div>
                )}

                {/* Bonus Pot Card */}
                <Card className="mb-10 shadow-md border-black/5 bg-white rounded-3xl overflow-hidden">
                    <CardHeader className="border-b border-black/5 bg-stone-50/50 pb-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle className="flex items-center gap-3 text-xl font-bold">
                                    <span className="bg-brand-blue/10 text-brand-blue px-2.5 py-1 rounded-md text-xs font-black uppercase tracking-wider">Configuration</span>
                                    Base Bonus Pot
                                </CardTitle>
                                <CardDescription className="mt-2 text-muted-foreground font-medium">
                                    Set the starting bonus value (£) for each trade group.
                                </CardDescription>
                            </div>
                        </div>
                    </CardHeader>

                    <CardContent className="p-8">
                        <div className="grid grid-cols-1 md:grid-cols-[1.2fr_1.2fr_1fr_auto] gap-6 items-start">
                            <div className="space-y-2">
                                <label className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Trade Group</label>
                                <Select value={potGroup} onValueChange={(v) => { setPotGroup(v); setPotTrade("__ALL__"); }}>
                                    <SelectTrigger className="h-11 font-bold bg-white">
                                        <SelectValue placeholder="Select Group" />
                                    </SelectTrigger>
                                    <SelectContent className="bg-white border-black/5 shadow-lg rounded-xl">
                                        {Object.keys(tradeGroups).map(g => (
                                            <SelectItem key={g} value={g} className="font-medium cursor-pointer">{g}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Trade</label>
                                <Select value={potTrade} onValueChange={setPotTrade}>
                                    <SelectTrigger className="h-11 font-bold bg-white">
                                        <SelectValue placeholder="Select Trade" />
                                    </SelectTrigger>
                                    <SelectContent className="bg-white border-black/5 shadow-lg rounded-xl">
                                        <SelectItem value="__ALL__" className="font-bold border-b border-border mb-1 pb-1 cursor-pointer">
                                            All Trades
                                        </SelectItem>
                                        {Object.keys(tradeSubgroups[potGroup] || {}).map(t => (
                                            <SelectItem key={t} value={t} className="font-medium cursor-pointer">{t}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Base Amount (£)</label>
                                <Input
                                    type="number"
                                    className="h-11 font-bold text-lg bg-white"
                                    value={newPotValue}
                                    onChange={(e) => setNewPotValue(e.target.value)}
                                />
                                <div className="text-xs font-bold text-muted-foreground text-right">
                                    Max Payout (+30%): <span className="text-support-green">£{((parseFloat(newPotValue) || 0) * 1.3).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                                </div>
                            </div>

                            <div className="pt-[26px]">
                                <Button
                                    onClick={handleSavePot}
                                    className="h-11 px-8 font-bold bg-support-green hover:bg-support-green/90 text-white shadow-sm transition-all"
                                >
                                    Save
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* KPI Config Card */}
                <Card className="shadow-md border-black/5 bg-white rounded-3xl overflow-hidden">
                    <CardHeader className="border-b border-black/5 bg-stone-50/50 pb-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle className="flex items-center gap-3 text-xl font-bold">
                                    <span className="bg-brand-yellow/20 text-yellow-700 px-2.5 py-1 rounded-md text-xs font-black uppercase tracking-wider">Rules</span>
                                    KPI Thresholds
                                </CardTitle>
                                <CardDescription className="mt-2 text-muted-foreground font-medium">
                                    Configure score boundaries for each KPI.
                                </CardDescription>
                            </div>
                        </div>
                    </CardHeader>

                    <CardContent className="p-8">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
                            <div className="space-y-2">
                                <label className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Trade Group</label>
                                <Select value={selectedGroup} onValueChange={setSelectedGroup}>
                                    <SelectTrigger className="h-11 font-bold bg-white">
                                        <SelectValue placeholder="Select Group" />
                                    </SelectTrigger>
                                    <SelectContent className="bg-white border-border shadow-lg rounded-xl">
                                        {/* All Trade Groups option */}
                                        <SelectItem value="__ALL__" className="font-bold border-b border-border mb-1 pb-1 cursor-pointer">
                                            🌐 All Trade Groups
                                        </SelectItem>
                                        {Object.keys(tradeGroups).map(g => (
                                            <SelectItem key={g} value={g} className="font-medium cursor-pointer">{g}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                {selectedGroup === "__ALL__" && !isDynamic && (
                                    <p className="text-xs text-muted-foreground font-medium mt-1">
                                        ℹ️ Static KPI thresholds are already shared across all trade groups.
                                    </p>
                                )}
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Select KPI</label>
                                <Select value={selectedKpi} onValueChange={setSelectedKpi}>
                                    <SelectTrigger className="h-11 font-bold bg-white">
                                        <SelectValue placeholder="Select KPI" />
                                    </SelectTrigger>
                                    <SelectContent className="bg-white border-border shadow-lg rounded-xl">
                                        {availableKpis.map(k => (
                                            <SelectItem key={k} value={k} className="font-medium cursor-pointer">{k}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>

                        {isDynamic ? (
                            <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                                {/* Trade Selector for Dynamic KPIs */}
                                <div className="mb-8 space-y-2 max-w-md">
                                    <label className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Trade Configuration</label>
                                    <Select value={selectedTrade} onValueChange={setSelectedTrade}>
                                        <SelectTrigger className="h-11 font-bold bg-white">
                                            <SelectValue placeholder="Select Trade" />
                                        </SelectTrigger>
                                        <SelectContent className="bg-white border-border shadow-lg rounded-xl">
                                            {/* "All Trades" Option -> Maps to Group Name */}
                                            <SelectItem value={selectedGroup} className="font-bold border-b border-border mb-1 pb-1 cursor-pointer">
                                                All Trades ({selectedGroup})
                                            </SelectItem>

                                            {/* Detailed Trades within the Group */}
                                            {Object.keys(tradeSubgroups[selectedGroup] || {}).map(t => (
                                                <SelectItem key={t} value={t} className="font-medium cursor-pointer pl-6">{t}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>

                                {/* Dynamic Threshold Table */}
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-lg font-bold text-foreground">
                                        Threshold Rules for {selectedTrade === selectedGroup ? `All Trades (${selectedGroup})` : selectedTrade}
                                    </h3>
                                    <div className="text-xs font-bold uppercase tracking-wider bg-muted px-3 py-1 rounded-full text-muted-foreground">
                                        {currentKpiConfig?.direction?.replace(/_/g, ' ')}
                                    </div>
                                </div>

                                <div className="border border-black/5 rounded-xl overflow-hidden shadow-sm overflow-x-auto">
                                    <table className="w-full text-left border-collapse min-w-max">
                                        <thead className="bg-muted/30">
                                            <tr>
                                                <th className="p-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Score Level</th>
                                                {selectedTrade === selectedGroup && selectedGroup !== "__ALL__" ? (
                                                    // Grid Layout Headers
                                                    <>
                                                        <th className="p-4 text-xs font-bold text-brand-blue uppercase tracking-wider border-l border-black/5 bg-brand-blue/5">All ({selectedGroup})</th>
                                                        {Object.keys(tradeSubgroups[selectedGroup] || {}).map(t => (
                                                            <th key={t} className="p-4 text-xs font-bold text-muted-foreground uppercase tracking-wider border-l border-black/5">{t}</th>
                                                        ))}
                                                    </>
                                                ) : (
                                                    <th className="p-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Threshold Value</th>
                                                )}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {(currentKpiConfig.dynamic.scores || []).map((score, idx) => {
                                                const scoreColorClass = score >= 80 ? 'text-support-green' : score >= 60 ? 'text-support-orange' : 'text-support-red';

                                                return (
                                                    <tr key={idx} className="border-b border-black/5 last:border-0 hover:bg-muted/5 transition-colors">
                                                        <td className="p-4">
                                                            <span className={`text-xl font-black ${scoreColorClass}`}>{score}%</span>
                                                        </td>

                                                        {selectedTrade === selectedGroup && selectedGroup !== "__ALL__" ? (
                                                            // Grid Layout Cells
                                                            <>
                                                                <td className="p-4 border-l border-black/5 bg-brand-blue/5">
                                                                    <Input
                                                                        type="number"
                                                                        min={0}
                                                                        step="any"
                                                                        value={gridThresholds["All"]?.[idx] !== undefined ? gridThresholds["All"][idx] : ''}
                                                                        onChange={(e) => handleGridChange("All", idx, e.target.value)}
                                                                        className="w-[120px] font-black bg-white border-2 border-brand-blue/20 focus-visible:ring-brand-blue"
                                                                    />
                                                                </td>
                                                                {Object.keys(tradeSubgroups[selectedGroup] || {}).map(t => (
                                                                    <td key={t} className="p-4 border-l border-black/5">
                                                                        <Input
                                                                            type="number"
                                                                            min={0}
                                                                            step="any"
                                                                            value={gridThresholds[t]?.[idx] !== undefined ? gridThresholds[t][idx] : ''}
                                                                            onChange={(e) => handleGridChange(t, idx, e.target.value)}
                                                                            className="w-[120px] font-bold bg-white"
                                                                        />
                                                                    </td>
                                                                ))}
                                                            </>
                                                        ) : (
                                                            <td className="p-4">
                                                                <Input
                                                                    type="number"
                                                                    className="w-[150px] font-bold bg-white"
                                                                    value={thresholds[idx] !== undefined ? thresholds[idx] : 0}
                                                                    onChange={(e) => {
                                                                        const newThresholds = [...thresholds];
                                                                        newThresholds[idx] = parseFloat(e.target.value);
                                                                        setThresholds(newThresholds);
                                                                    }}
                                                                />
                                                            </td>
                                                        )}
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>

                                <div className="mt-8 flex justify-end">
                                    <Button
                                        onClick={handleSaveThresholds}
                                        className="h-11 px-8 font-bold bg-support-green hover:bg-support-green/90 text-white shadow-sm transition-all"
                                    >
                                        {selectedGroup === "__ALL__" ? "Save for All Trade Groups" : "Save Thresholds"}
                                    </Button>
                                </div>
                            </div>
                        ) : (
                            <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-lg font-bold text-foreground">Threshold Rules</h3>
                                    <div className="text-xs font-bold uppercase tracking-wider bg-muted px-3 py-1 rounded-full text-muted-foreground">
                                        {currentKpiConfig?.direction?.replace(/_/g, ' ')}
                                    </div>
                                </div>

                                <div className="border border-black/5 rounded-xl overflow-hidden shadow-sm">
                                    <table className="w-full text-left border-collapse">
                                        <thead className="bg-muted/30">
                                            <tr>
                                                <th className="p-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                                                    {currentKpiConfig?.direction === 'lower_is_better' ? 'Max Value' : 'Min Value'}
                                                </th>
                                                <th className="p-4 text-xs font-bold text-muted-foreground uppercase tracking-wider">Score Awarded</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {thresholds.map((t, idx) => {
                                                const isHighScore = t.score >= 80;
                                                const isMedScore = t.score >= 60;
                                                const badgeBg = isHighScore ? 'bg-green-100' : (isMedScore ? 'bg-amber-100' : 'bg-red-100');
                                                const badgeText = isHighScore ? 'bg-green-700' : (isMedScore ? 'bg-amber-700' : 'bg-red-700');

                                                return (
                                                    <tr key={idx} className="border-b border-black/5 last:border-0 hover:bg-muted/5 transition-colors bg-white">
                                                        <td className="p-4">
                                                            <div className="flex items-center gap-2">
                                                                <span className="text-muted-foreground font-bold">≥</span>
                                                                <Input
                                                                    type="number"
                                                                    className="w-[120px] font-bold bg-white"
                                                                    value={(currentKpiConfig?.direction === 'lower_is_better' ? t.max : t.min) || 0}
                                                                    onChange={(e) => handleThresholdChange(idx, currentKpiConfig?.direction === 'lower_is_better' ? 'max' : 'min', e.target.value)}
                                                                />
                                                            </div>
                                                        </td>
                                                        <td className="p-4">
                                                            <div className="flex items-center gap-4">
                                                                <Input
                                                                    type="number"
                                                                    className="w-[90px] font-bold bg-white"
                                                                    value={t.score}
                                                                    onChange={(e) => handleThresholdChange(idx, 'score', e.target.value)}
                                                                />
                                                                <div className={`w-[60px] h-1.5 rounded-full ${badgeBg} overflow-hidden`}>
                                                                    <div
                                                                        className={`h-full rounded-full ${badgeText}`}
                                                                        style={{ width: `${Math.min(t.score, 100)}%` }}
                                                                    />
                                                                </div>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>

                                <div className="mt-8 flex justify-end">
                                    <Button
                                        onClick={handleSaveThresholds}
                                        className="h-11 px-8 font-bold bg-support-green hover:bg-support-green/90 text-white shadow-sm transition-all"
                                    >
                                        Save Changes
                                    </Button>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default Thresholds;
