import React, { createContext, useContext, useState, useEffect } from 'react';
import { fetchSession, signOut as apiSignOut } from '../api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const refreshSession = async () => {
        setLoading(true);
        try {
            const data = await fetchSession();
            if (data && data.user) {
                setUser(data.user);
            } else {
                setUser(null);
            }
        } catch (error) {
            console.error("Session refresh failed:", error);
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    const logout = async () => {
        try {
            // apiSignOut now handles Microsoft logout redirect
            await apiSignOut();
        } catch (error) {
            console.error("Logout failed:", error);
            // Fallback: just redirect to login
            setUser(null);
            window.location.href = "/";
        }
    };

    useEffect(() => {
        refreshSession();
    }, []);

    return (
        <AuthContext.Provider value={{ user, loading, refreshSession, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
};
