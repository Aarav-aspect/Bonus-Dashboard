import React from 'react';
import { Link } from 'react-router-dom';
import logo from '../assets/Aspect_Logo.svg';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"

const Header = ({
    months,
    tradeGroups,
    selectedMonth,
    selectedGroup,
    selectedFilter,
    onMonthChange,
    onGroupChange,
    onFilterChange,
    availableSubgroups
}) => {
    return (
        <header className="flex justify-between items-center mb-12 pb-10 border-b border-border">
            {/* Logo Area */}
            <div className="flex items-center gap-8">
                <Link to="/">
                    <img src={logo} alt="Aspect Logo" className="w-[150px]" />
                </Link>
                <div className="flex gap-6 ml-4">
                    <Link to="/thresholds" className="font-bold text-muted-foreground text-sm uppercase tracking-wider hover:text-brand-blue transition-colors">
                        Management
                    </Link>
                    <Link to="/targets" className="font-bold text-muted-foreground text-sm uppercase tracking-wider hover:text-brand-blue transition-colors">
                        Trade View
                    </Link>
                    <Link to="/insights" className="font-bold text-muted-foreground text-sm uppercase tracking-wider hover:text-brand-blue transition-colors">
                        Insights
                    </Link>
                </div>
            </div>

            {/* Filters Area */}
            <div className="flex gap-4 items-center bg-white p-3 px-6 rounded-2xl border border-border shadow-md">

                {/* Month Filter */}
                <div className="flex flex-col gap-1.5">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase pl-1 tracking-wider">Month</span>
                    <Select value={selectedMonth} onValueChange={onMonthChange}>
                        <SelectTrigger className="w-[160px] h-10 rounded-lg border border-input bg-white px-3 py-2 text-sm shadow-sm hover:border-brand-blue focus:ring-1 focus:ring-brand-blue transition-all font-bold">
                            <SelectValue placeholder="Select Month" />
                        </SelectTrigger>
                        <SelectContent className="rounded-xl border-border shadow-lg bg-white">
                            {months.map(m => (
                                <SelectItem key={m} value={m} className="font-medium focus:bg-brand-blue/10 focus:text-brand-blue cursor-pointer rounded-lg my-1">{m}</SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>



                {/* Trade Group Filter */}
                <div className="flex flex-col gap-1.5">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase pl-1 tracking-wider">Trade Group</span>
                    <Select value={selectedGroup} onValueChange={onGroupChange}>
                        <SelectTrigger className="w-[200px] h-10 rounded-lg border border-input bg-white px-3 py-2 text-sm shadow-sm hover:border-brand-blue focus:ring-1 focus:ring-brand-blue transition-all font-bold">
                            <SelectValue placeholder="Select Group" />
                        </SelectTrigger>
                        <SelectContent className="rounded-xl border-border shadow-lg bg-white">
                            {Object.keys(tradeGroups).map(g => (
                                <SelectItem key={g} value={g} className="font-medium focus:bg-brand-blue/10 focus:text-brand-blue cursor-pointer rounded-lg my-1">{g}</SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                {Object.keys(availableSubgroups).length > 0 && (
                    <>


                        {/* Trade Filter */}
                        <div className="flex flex-col gap-1.5">
                            <span className="text-[10px] font-bold text-muted-foreground uppercase pl-1 tracking-wider">Trade Filter</span>
                            <Select value={selectedFilter} onValueChange={onFilterChange}>
                                <SelectTrigger className="w-[180px] h-10 rounded-lg border border-input bg-white px-3 py-2 text-sm shadow-sm hover:border-brand-blue focus:ring-1 focus:ring-brand-blue transition-all font-bold">
                                    <SelectValue placeholder="Select Trade" />
                                </SelectTrigger>
                                <SelectContent className="rounded-xl border-border shadow-lg bg-white">
                                    <SelectItem value="All" className="font-bold focus:bg-brand-blue/10 focus:text-brand-blue cursor-pointer rounded-lg my-1">All Trades</SelectItem>
                                    {Object.keys(availableSubgroups).map(sg => (
                                        <SelectItem key={sg} value={sg} className="font-medium focus:bg-brand-blue/10 focus:text-brand-blue cursor-pointer rounded-lg my-1">{sg}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </>
                )}
            </div>
        </header>
    );
}

export default Header;
