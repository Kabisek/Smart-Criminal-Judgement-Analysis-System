import React, { createContext, useContext, useState, useEffect } from 'react';

type UserRole = 'guest' | 'lawyer';

interface AuthContextType {
    role: UserRole;
    isLoggedIn: boolean;
    login: (credentials: { email: string; pass: string }) => Promise<void>;
    logout: () => void;
    user: { name: string; email: string } | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

import { Platform } from 'react-native';

const isWeb = Platform.OS === 'web';

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [role, setRole] = useState<UserRole>('guest');
    const [user, setUser] = useState<{ name: string; email: string } | null>(null);

    useEffect(() => {
        const saved = isWeb ? sessionStorage.getItem('user_auth') : null;
        if (saved) {
            const data = JSON.parse(saved);
            setRole(data.role);
            setUser(data.user);
        }
    }, []);

    const login = async (credentials: { email: string; pass: string }) => {
        // Mock login logic
        if (credentials.email.includes('lawyer')) {
            const data = { role: 'lawyer' as UserRole, user: { name: 'Advocate Perera', email: credentials.email } };
            setRole(data.role);
            setUser(data.user);
            if (isWeb) {
                sessionStorage.setItem('user_auth', JSON.stringify(data));
            }
        } else {
            throw new Error('Invalid credentials. Use a lawyer email to access professional components.');
        }
    };

    const logout = () => {
        setRole('guest');
        setUser(null);
        if (isWeb) {
            sessionStorage.removeItem('user_auth');
        }
    };

    return (
        <AuthContext.Provider value={{ role, isLoggedIn: role !== 'guest', login, logout, user }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within AuthProvider');
    return ctx;
};
