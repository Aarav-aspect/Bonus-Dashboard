import React, { useEffect, useRef, useState, useCallback } from 'react';
import Header from '../components/layout/Header';
import { useAuth } from '../context/AuthContext';
import { fetchUsers, createUser, updateUser, deleteUser, fetchTradeGroups, fetchTradeSubgroups, searchOrgUsers } from '../api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { UserPlus, Pencil, Trash2, X, Check, Loader2, Users, ShieldCheck, AlertCircle, Search } from 'lucide-react';
import { toast } from 'sonner';

// Roles that require extra scope fields
const ROLE_NEEDS_GROUP = ["trade_group_manager", "trade_manager", "regional_trade_group_manager", "regional_trade_manager"];
const ROLE_NEEDS_TRADE = ["trade_manager", "regional_trade_manager"];
const ROLE_NEEDS_REGION = ["regional_trade_group_manager", "regional_trade_manager"];

const ROLE_LABELS = {
    admin: "Admin",
    manager: "Manager",
    trade_group_manager: "Trade Group Manager",
    trade_manager: "Trade Manager",
    regional_trade_group_manager: "Regional Trade Group Manager",
    regional_trade_manager: "Regional Trade Manager",
    user: "User (read-only)",
};

const ROLE_COLORS = {
    admin: "bg-red-100 text-red-700 border-red-200",
    manager: "bg-purple-100 text-purple-700 border-purple-200",
    trade_group_manager: "bg-blue-100 text-blue-700 border-blue-200",
    trade_manager: "bg-indigo-100 text-indigo-700 border-indigo-200",
    regional_trade_group_manager: "bg-teal-100 text-teal-700 border-teal-200",
    regional_trade_manager: "bg-cyan-100 text-cyan-700 border-cyan-200",
    user: "bg-gray-100 text-gray-600 border-gray-200",
};

// All known regions — kept static so they're always available in the form
const ALL_REGIONS = ["North", "South", "North West", "South West", "East"];

const EMPTY_FORM = {
    email: "", name: "", role: "user",
    assigned_group: "", assigned_trade: "", assigned_region: "",
};

function ScopeText({ user }) {
    const parts = [];
    if (user.assigned_group) parts.push(user.assigned_group);
    if (user.assigned_trade) parts.push(user.assigned_trade);
    if (user.assigned_region) parts.push(user.assigned_region);
    if (!parts.length) return <span className="text-gray-300">—</span>;
    return <span className="text-gray-600 text-xs">{parts.join(" · ")}</span>;
}

function UserFormModal({ isOpen, onClose, onSave, initial, tradeGroups, tradeSubgroups }) {
    const [form, setForm] = useState(EMPTY_FORM);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);

    // Org user search
    const [searchQuery, setSearchQuery] = useState("");
    const [suggestions, setSuggestions] = useState([]);
    const [searching, setSearching] = useState(false);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const searchRef = useRef(null);
    const debounceRef = useRef(null);

    useEffect(() => {
        if (isOpen) {
            setForm(initial ? { ...EMPTY_FORM, ...initial } : EMPTY_FORM);
            setSearchQuery(initial?.email || "");
            setError(null);
            setSuggestions([]);
        }
    }, [isOpen, initial]);

    // Close suggestions on outside click
    useEffect(() => {
        const handleClick = (e) => {
            if (searchRef.current && !searchRef.current.contains(e.target)) {
                setShowSuggestions(false);
            }
        };
        document.addEventListener("mousedown", handleClick);
        return () => document.removeEventListener("mousedown", handleClick);
    }, []);

    const handleSearchInput = (val) => {
        setSearchQuery(val);
        set("email", val);
        set("name", form.name); // keep name if already set
        clearTimeout(debounceRef.current);
        if (!val || val.length < 2) { setSuggestions([]); setShowSuggestions(false); return; }
        debounceRef.current = setTimeout(async () => {
            setSearching(true);
            try {
                const data = await searchOrgUsers(val);
                setSuggestions(data.users || []);
                setShowSuggestions(true);
                if (data.error) console.warn("Graph API error:", data.error);
            } catch (e) { setSuggestions([]); console.error("Search failed:", e); }
            finally { setSearching(false); }
        }, 300);
    };

    const selectSuggestion = (u) => {
        setSearchQuery(u.email);
        setForm(f => ({ ...f, email: u.email, name: f.name || u.name }));
        setSuggestions([]);
        setShowSuggestions(false);
    };

    const set = (key, val) => setForm(f => ({ ...f, [key]: val }));

    const availableTrades = form.assigned_group && tradeSubgroups[form.assigned_group]
        ? Object.keys(tradeSubgroups[form.assigned_group])
        : [];

    const handleSave = async () => {
        if (!form.email.trim()) { setError("Email is required."); return; }
        if (!form.role) { setError("Role is required."); return; }
        setSaving(true);
        setError(null);
        try {
            const payload = {
                email: form.email.trim(),
                name: form.name.trim() || null,
                role: form.role,
                assigned_group: ROLE_NEEDS_GROUP.includes(form.role) ? form.assigned_group || null : null,
                assigned_trade: ROLE_NEEDS_TRADE.includes(form.role) ? form.assigned_trade || null : null,
                assigned_region: ROLE_NEEDS_REGION.includes(form.role) ? form.assigned_region || null : null,
            };
            await onSave(payload);
            onClose();
        } catch (e) {
            setError(e.message);
        } finally {
            setSaving(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md flex flex-col max-h-[90vh] border border-black/5">
                <div className="flex items-center justify-between px-6 py-4 border-b border-black/5 shrink-0 rounded-t-2xl">
                    <h2 className="font-bold text-gray-900 text-base">
                        {initial ? "Edit User" : "Add User"}
                    </h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors cursor-pointer">
                        <X className="h-4 w-4" />
                    </button>
                </div>

                <div className="px-6 py-5 flex flex-col gap-4 overflow-y-auto">
                    {error && (
                        <div className="flex items-center gap-2 text-support-red text-sm bg-red-50 rounded-lg px-3 py-2 border border-red-100">
                            <AlertCircle className="h-4 w-4 shrink-0" />
                            {error}
                        </div>
                    )}

                    <div className="flex flex-col gap-1.5" ref={searchRef}>
                        <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                            {initial ? "Email" : "Search user *"}
                        </label>
                        <div className="relative">
                            <div className="relative">
                                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
                                <Input
                                    type="text"
                                    placeholder="Search by name or email…"
                                    value={searchQuery}
                                    onChange={e => handleSearchInput(e.target.value)}
                                    onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                                    disabled={!!initial}
                                    className="h-9 text-sm pl-8 pr-8"
                                    autoComplete="off"
                                />
                                {searching && (
                                    <Loader2 className="absolute right-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 animate-spin text-muted-foreground" />
                                )}
                            </div>
                            {showSuggestions && suggestions.length > 0 && (
                                <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-black/10 rounded-xl shadow-lg z-50 overflow-hidden max-h-48 overflow-y-auto">
                                    {suggestions.map(u => (
                                        <button
                                            key={u.id || u.email}
                                            type="button"
                                            onMouseDown={() => selectSuggestion(u)}
                                            className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-brand-blue/5 transition-colors text-left cursor-pointer"
                                        >
                                            <div className="w-7 h-7 rounded-full bg-brand-blue/10 text-brand-blue flex items-center justify-center font-bold text-[10px] shrink-0">
                                                {(u.name || u.email).charAt(0).toUpperCase()}
                                            </div>
                                            <div className="min-w-0">
                                                <div className="font-semibold text-gray-900 text-xs truncate">{u.name}</div>
                                                <div className="text-[11px] text-muted-foreground truncate">{u.email}</div>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="flex flex-col gap-1.5">
                        <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Display Name</label>
                        <Input
                            placeholder="Full name (optional)"
                            value={form.name}
                            onChange={e => set("name", e.target.value)}
                            className="h-9 text-sm"
                        />
                    </div>

                    <div className="flex flex-col gap-1.5">
                        <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Role *</label>
                        <Select value={form.role} onValueChange={v => set("role", v)}>
                            <SelectTrigger className="h-9 text-sm">
                                <SelectValue placeholder="Select role" />
                            </SelectTrigger>
                            <SelectContent className="z-[200] bg-white">
                                {Object.entries(ROLE_LABELS).map(([r, label]) => (
                                    <SelectItem key={r} value={r} className="text-sm cursor-pointer focus:bg-brand-blue/10 focus:text-brand-blue">{label}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {ROLE_NEEDS_GROUP.includes(form.role) && (
                        <div className="flex flex-col gap-1.5">
                            <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Trade Group</label>
                            <Select value={form.assigned_group || ""} onValueChange={v => { set("assigned_group", v); set("assigned_trade", ""); }}>
                                <SelectTrigger className="h-9 text-sm">
                                    <SelectValue placeholder="Select trade group" />
                                </SelectTrigger>
                                <SelectContent className="z-[200] bg-white">
                                    {Object.keys(tradeGroups).map(g => (
                                        <SelectItem key={g} value={g} className="text-sm cursor-pointer focus:bg-brand-blue/10 focus:text-brand-blue">{g}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    )}

                    {ROLE_NEEDS_TRADE.includes(form.role) && (
                        <div className="flex flex-col gap-1.5">
                            <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Trade</label>
                            <Select value={form.assigned_trade || ""} onValueChange={v => set("assigned_trade", v)} disabled={!form.assigned_group}>
                                <SelectTrigger className="h-9 text-sm">
                                    <SelectValue placeholder={form.assigned_group ? "Select trade" : "Select a trade group first"} />
                                </SelectTrigger>
                                <SelectContent className="z-[200] bg-white">
                                    {availableTrades.map(t => (
                                        <SelectItem key={t} value={t} className="text-sm cursor-pointer focus:bg-brand-blue/10 focus:text-brand-blue">{t}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    )}

                    {ROLE_NEEDS_REGION.includes(form.role) && (
                        <div className="flex flex-col gap-1.5">
                            <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Region</label>
                            <Select value={form.assigned_region || ""} onValueChange={v => set("assigned_region", v)}>
                                <SelectTrigger className="h-9 text-sm">
                                    <SelectValue placeholder="Select region" />
                                </SelectTrigger>
                                <SelectContent className="z-[200] bg-white">
                                    {ALL_REGIONS.map(r => (
                                        <SelectItem key={r} value={r} className="text-sm cursor-pointer focus:bg-brand-blue/10 focus:text-brand-blue">{r}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    )}
                </div>

                <div className="flex justify-end gap-2 px-6 py-4 border-t border-black/5 bg-gray-50/50 shrink-0 rounded-b-2xl">
                    <Button variant="outline" size="sm" onClick={onClose} className="h-8 text-xs cursor-pointer">Cancel</Button>
                    <Button size="sm" onClick={handleSave} disabled={saving} className="h-8 text-xs bg-brand-blue hover:bg-brand-blue/90 cursor-pointer">
                        {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" /> : <Check className="h-3.5 w-3.5 mr-1.5" />}
                        {initial ? "Save Changes" : "Add User"}
                    </Button>
                </div>
            </div>
        </div>
    );
}

const AccountManagement = () => {
    const { user } = useAuth();
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [tradeGroups, setTradeGroups] = useState({});
    const [tradeSubgroups, setTradeSubgroups] = useState({});

    const [modalOpen, setModalOpen] = useState(false);
    const [editingUser, setEditingUser] = useState(null);
    const [deletingId, setDeletingId] = useState(null);
    const [search, setSearch] = useState("");

    const loadUsers = useCallback(async () => {
        try {
            const data = await fetchUsers();
            setUsers(data.users || []);
        } catch (e) {
            toast.error("Failed to load users.");
        }
    }, []);

    useEffect(() => {
        setLoading(true);
        Promise.all([loadUsers(), fetchTradeGroups(), fetchTradeSubgroups()])
            .then(([, tg, ts]) => { setTradeGroups(tg); setTradeSubgroups(ts); })
            .catch(() => { })
            .finally(() => setLoading(false));
    }, [loadUsers]);

    const handleSave = async (payload) => {
        if (editingUser) {
            const { email, ...rest } = payload;
            await updateUser(editingUser.id, rest);
            toast.success("User updated.");
        } else {
            await createUser(payload);
            toast.success("User added.");
        }
        await loadUsers();
    };

    const handleDelete = async (u) => {
        if (!window.confirm(`Remove ${u.email} from the dashboard? They will fall back to their Azure AD role on next login.`)) return;
        setDeletingId(u.id);
        try {
            await deleteUser(u.id);
            toast.success("User removed.");
            await loadUsers();
        } catch {
            toast.error("Failed to remove user.");
        } finally {
            setDeletingId(null);
        }
    };

    const openAdd = () => { setEditingUser(null); setModalOpen(true); };
    const openEdit = (u) => { setEditingUser(u); setModalOpen(true); };

    const filtered = users.filter(u =>
        !search ||
        u.email.toLowerCase().includes(search.toLowerCase()) ||
        (u.name || "").toLowerCase().includes(search.toLowerCase())
    );

    return (
        <div className="min-h-screen bg-gray-50/30 px-8 py-6 max-w-7xl mx-auto">
            <Header showMonthFilter={false} showGroupFilter={false} />

            <div className="mb-6">
                <h1 className="text-2xl font-black text-gray-900">Account Management</h1>

            </div>

            <Card className="border border-black/5 shadow-sm rounded-2xl">
                <CardHeader className="pb-4 border-b border-black/5">
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-xl bg-brand-blue/10">
                                <Users className="h-4 w-4 text-brand-blue" />
                            </div>
                            <div>
                                <CardTitle className="text-sm font-bold">Users</CardTitle>
                                <CardDescription className="text-xs">{users.length} managed account{users.length !== 1 ? "s" : ""}</CardDescription>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <Input
                                placeholder="Search users..."
                                value={search}
                                onChange={e => setSearch(e.target.value)}
                                className="h-8 text-xs w-48"
                            />
                            <Button size="sm" onClick={openAdd} className="h-8 text-xs bg-brand-blue hover:bg-brand-blue/90 cursor-pointer gap-1.5">
                                <UserPlus className="h-3.5 w-3.5" />
                                Add User
                            </Button>
                        </div>
                    </div>
                </CardHeader>

                <CardContent className="p-0">
                    {loading ? (
                        <div className="flex items-center justify-center py-16 text-muted-foreground gap-3">
                            <Loader2 className="h-5 w-5 animate-spin text-brand-blue" />
                            <span className="text-sm font-medium">Loading users...</span>
                        </div>
                    ) : filtered.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-3">
                            <div className="p-4 rounded-full bg-gray-100">
                                <Users className="h-8 w-8 text-gray-300" />
                            </div>
                            <div className="text-center">
                                <p className="font-semibold text-sm">{search ? "No users match your search." : "No managed users yet."}</p>
                                {!search && <p className="text-xs mt-1">Add a user to override their Azure AD role.</p>}
                            </div>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead className="bg-gray-50/80 border-b border-black/5">
                                    <tr>
                                        <th className="text-left py-3 px-6 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">User</th>
                                        <th className="text-left py-3 px-6 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Role</th>
                                        <th className="text-left py-3 px-6 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Scope</th>
                                        <th className="text-right py-3 px-6 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-black/5 bg-white">
                                    {filtered.map(u => (
                                        <tr key={u.id} className="hover:bg-brand-blue/5 transition-colors group">
                                            <td className="py-4 px-6">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-8 h-8 rounded-full bg-brand-blue/10 text-brand-blue flex items-center justify-center font-bold text-xs shrink-0">
                                                        {(u.name || u.email).charAt(0).toUpperCase()}
                                                    </div>
                                                    <div>
                                                        <div className="font-semibold text-gray-900 text-sm">{u.name || <span className="text-gray-400 italic font-normal text-xs">No name set</span>}</div>
                                                        <div className="text-xs text-muted-foreground">{u.email}</div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="py-4 px-6">
                                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold border ${ROLE_COLORS[u.role] || ROLE_COLORS.user}`}>
                                                    <ShieldCheck className="h-3 w-3" />
                                                    {ROLE_LABELS[u.role] || u.role}
                                                </span>
                                            </td>
                                            <td className="py-4 px-6">
                                                <ScopeText user={u} />
                                            </td>
                                            <td className="py-4 px-6">
                                                <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                    <button
                                                        onClick={() => openEdit(u)}
                                                        className="p-1.5 rounded-lg hover:bg-brand-blue/10 text-muted-foreground hover:text-brand-blue transition-colors cursor-pointer"
                                                        title="Edit"
                                                    >
                                                        <Pencil className="h-3.5 w-3.5" />
                                                    </button>
                                                    <button
                                                        onClick={() => handleDelete(u)}
                                                        disabled={deletingId === u.id || u.id === user?.id}
                                                        className="p-1.5 rounded-lg hover:bg-red-50 text-muted-foreground hover:text-support-red transition-colors disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
                                                        title={u.id === user?.id ? "Cannot delete yourself" : "Remove user"}
                                                    >
                                                        {deletingId === u.id
                                                            ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                                            : <Trash2 className="h-3.5 w-3.5" />
                                                        }
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </CardContent>
            </Card>

            <div className="mt-4 px-1 text-xs text-muted-foreground flex items-center gap-1.5">
                <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                Users not listed here will use their Azure AD role. Changes take effect on next login.
            </div>

            <UserFormModal
                isOpen={modalOpen}
                onClose={() => setModalOpen(false)}
                onSave={handleSave}
                initial={editingUser}
                tradeGroups={tradeGroups}
                tradeSubgroups={tradeSubgroups}
            />
        </div>
    );
};

export default AccountManagement;
