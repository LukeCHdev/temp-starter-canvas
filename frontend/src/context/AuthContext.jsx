import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authAPI } from '@/utils/api';

// Auth Context
const AuthContext = createContext(null);

// Emergent Auth URL for Google OAuth
const EMERGENT_AUTH_URL = 'https://demobackend.emergentagent.com/auth/v1/env/oauth/google';

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [initialized, setInitialized] = useState(false);

    // Check if user is logged in on mount
    useEffect(() => {
        const checkAuth = async () => {
            try {
                const response = await authAPI.me();
                if (response.data?.success && response.data?.user) {
                    setUser(response.data.user);
                }
            } catch (error) {
                // Not logged in - that's fine
                setUser(null);
            } finally {
                setLoading(false);
                setInitialized(true);
            }
        };

        checkAuth();
    }, []);

    // Login with email/password
    const login = useCallback(async (email, password) => {
        const response = await authAPI.login({ email, password });
        if (response.data?.success && response.data?.user) {
            setUser(response.data.user);
            return response.data;
        }
        throw new Error(response.data?.detail || 'Login failed');
    }, []);

    // Register new user
    const register = useCallback(async (email, username, password, confirmPassword) => {
        const response = await authAPI.register({
            email,
            username,
            password,
            confirm_password: confirmPassword
        });
        if (response.data?.success && response.data?.user) {
            setUser(response.data.user);
            return response.data;
        }
        throw new Error(response.data?.detail || 'Registration failed');
    }, []);

    // Logout
    const logout = useCallback(async () => {
        try {
            await authAPI.logout();
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            setUser(null);
        }
    }, []);

    // Google OAuth - redirect to Emergent Auth
    const loginWithGoogle = useCallback((redirectPath = '/') => {
        // Get the current origin for redirect
        const currentOrigin = window.location.origin;
        const redirectUri = `${currentOrigin}/auth/callback?redirect=${encodeURIComponent(redirectPath)}`;
        
        // Redirect to Emergent Auth
        window.location.href = `${EMERGENT_AUTH_URL}?redirect_uri=${encodeURIComponent(redirectUri)}`;
    }, []);

    // Handle Google OAuth callback
    const handleGoogleCallback = useCallback(async (sessionId) => {
        const response = await authAPI.googleAuth(sessionId);
        if (response.data?.success && response.data?.user) {
            setUser(response.data.user);
            return response.data;
        }
        throw new Error(response.data?.detail || 'Google login failed');
    }, []);

    // Refresh user data
    const refreshUser = useCallback(async () => {
        try {
            const response = await authAPI.me();
            if (response.data?.success && response.data?.user) {
                setUser(response.data.user);
                return response.data.user;
            }
        } catch (error) {
            setUser(null);
        }
        return null;
    }, []);

    const value = {
        user,
        isAuthenticated: !!user,
        loading,
        initialized,
        login,
        register,
        logout,
        loginWithGoogle,
        handleGoogleCallback,
        refreshUser,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext;
