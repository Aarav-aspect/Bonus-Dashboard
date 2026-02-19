import { Link, useLocation } from 'react-router-dom';
import logo from '../assets/Aspect_Logo.svg';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"

import { signOut as apiSignOut } from '../api';
import { Button } from "@/components/ui/button"
import { useAuth } from '../context/AuthContext';

const Header = ({
    months = [],
    tradeGroups = {},
    selectedMonth,
    selectedGroup,
    selectedFilter,
    onMonthChange,
    onGroupChange,
    onFilterChange,
    availableSubgroups = {},
    showMonthFilter = true,
    showGroupFilter = true,
}) => {
    const { user, logout } = useAuth();
    const location = useLocation();

    const isPathActive = (path) => location.pathname === path;

    return (
        <header className="flex justify-between items-center mb-8 pb-4 border-b border-black/5">
            {/* Logo Area */}
            <div className="flex items-center gap-6">
                <Link to="/dashboard" className="transition-transform hover:scale-105 active:scale-95">
                    <img src={logo} alt="Aspect Logo" className="w-[130px]" />
                </Link>
                <div className="flex gap-4 ml-2 items-center">
                    {!isPathActive('/dashboard') && (
                        <Link
                            to="/dashboard"
                            className={`font-bold text-sm uppercase tracking-wider transition-colors ${isPathActive('/dashboard') ? 'text-brand-blue' : 'text-muted-foreground hover:text-brand-blue'
                                }`}
                        >
                            Dashboard
                        </Link>
                    )}
                    {(user?.role === 'admin' || user?.role === 'manager') && !isPathActive('/thresholds') && (
                        <Link
                            to="/thresholds"
                            className={`font-bold text-sm uppercase tracking-wider transition-colors ${isPathActive('/thresholds') ? 'text-brand-blue' : 'text-muted-foreground hover:text-brand-blue'
                                }`}
                        >
                            Management
                        </Link>
                    )}
                    {!isPathActive('/historic') && (
                        <Link
                            to="/historic"
                            className={`font-bold text-sm uppercase tracking-wider transition-colors ${isPathActive('/historic') ? 'text-brand-blue' : 'text-muted-foreground hover:text-brand-blue'
                                }`}
                        >
                            History
                        </Link>
                    )}

                </div>
            </div>


            {/* Filters Area */}
            {(showMonthFilter || showGroupFilter) && (
                <div className="flex gap-3 items-center bg-white p-2 px-4 rounded-xl border border-black/5 shadow-sm">

                    {/* Month Filter */}
                    {showMonthFilter && (
                        <div className="flex flex-col gap-1">
                            <span className="text-[9px] font-bold text-muted-foreground uppercase pl-1 tracking-wider">Month</span>
                            <Select value={selectedMonth} onValueChange={onMonthChange}>
                                <SelectTrigger className="w-[140px] h-8 rounded-md border border-input bg-white px-2 py-1 text-xs shadow-sm hover:border-brand-blue focus:ring-1 focus:ring-brand-blue transition-all font-bold">
                                    <SelectValue placeholder="Select Month" />
                                </SelectTrigger>
                                <SelectContent className="rounded-xl border-black/5 shadow-lg bg-white">
                                    {months.map(m => (
                                        <SelectItem key={m} value={m} className="font-medium focus:bg-brand-blue/10 focus:text-brand-blue cursor-pointer rounded-lg my-1">{m}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    )}

                    {/* Trade Group Filter */}
                    {showGroupFilter && (
                        <div className="flex flex-col gap-1">
                            <span className="text-[9px] font-bold text-muted-foreground uppercase pl-1 tracking-wider">Trade Group</span>
                            <Select
                                value={selectedGroup}
                                onValueChange={onGroupChange}
                                disabled={user?.role === 'trade_group_manager' || user?.role === 'trade_manager'}
                            >
                                <SelectTrigger className="w-[180px] h-8 rounded-md border border-input bg-white px-2 py-1 text-xs shadow-sm hover:border-brand-blue focus:ring-1 focus:ring-brand-blue transition-all font-bold disabled:opacity-80 disabled:bg-gray-50">
                                    <SelectValue placeholder="Select Group" />
                                </SelectTrigger>
                                <SelectContent className="rounded-xl border-black/5 shadow-lg bg-white">
                                    {Object.keys(tradeGroups).map(g => (
                                        <SelectItem key={g} value={g} className="font-medium focus:bg-brand-blue/10 focus:text-brand-blue cursor-pointer rounded-lg my-1">{g}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    )}

                    {showGroupFilter && Object.keys(availableSubgroups).length > 0 && (
                        <>
                            {/* Trade Filter */}
                            <div className="flex flex-col gap-1">
                                <span className="text-[9px] font-bold text-muted-foreground uppercase pl-1 tracking-wider">Trade Filter</span>
                                <Select
                                    value={selectedFilter}
                                    onValueChange={onFilterChange}
                                    disabled={user?.role === 'trade_manager'}
                                >
                                    <SelectTrigger className="w-[160px] h-8 rounded-md border border-input bg-white px-2 py-1 text-xs shadow-sm hover:border-brand-blue focus:ring-1 focus:ring-brand-blue transition-all font-bold disabled:opacity-80 disabled:bg-gray-50">
                                        <SelectValue placeholder="Select Trade" />
                                    </SelectTrigger>
                                    <SelectContent className="rounded-xl border-black/5 shadow-lg bg-white">
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
            )}

            {user && (
                <div className="flex items-center gap-3">
                    {user.image ? (
                        <img src={user.image} alt={user.name} className="w-7 h-7 rounded-full border border-gray-200" />
                    ) : (
                        <div className="w-7 h-7 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-[10px] border border-blue-200">
                            {user.name?.charAt(0)}
                        </div>
                    )}
                    <button
                        onClick={logout}
                        className="ml-1 text-[10px] font-bold text-white uppercase tracking-wider bg-red-500 hover:bg-red-600 px-2 py-1 rounded-md transition-colors shadow-sm"
                    >
                        Sign Out
                    </button>
                </div>
            )}
        </header>
    );
}

export default Header;
