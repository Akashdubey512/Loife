import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { apiService } from '../services/api';
import { AuthUser } from '../types';

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  loginError: string | null;
  login: (email: string, password: string) => Promise<AuthUser>;
  signup: (payload: SignupPayload) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

export interface SignupPayload {
  email: string;
  password: string;
  full_name: string;
  phone_number?: string;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loginError, setLoginError] = useState<string | null>(null);
  const initialized = useRef(false);

  // Session restoration on mount — called once
  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    const restoreSession = async () => {
      const token = localStorage.getItem('reserve_token');
      if (!token) {
        setIsLoading(false);
        return;
      }
      try {
        const profile = await apiService.getMe();
        setUser(profile);
      } catch {
        // Token is expired / invalid — clear it
        localStorage.removeItem('reserve_token');
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []);

  // Listen for the 401 event dispatched by the API interceptor
  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null);
      localStorage.removeItem('reserve_token');
    };
    window.addEventListener('reserveai:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('reserveai:unauthorized', handleUnauthorized);
  }, []);

  const login = useCallback(async (email: string, password: string): Promise<AuthUser> => {
    setLoginError(null);
    const res = await apiService.login(email, password);
    setUser(res.user);
    return res.user;
  }, []);

  const signup = useCallback(async (payload: SignupPayload): Promise<void> => {
    setLoginError(null);
    // POST to /api/v1/auth/register — backend enforces PUBLIC_USER role, no org assignment
    await apiService.register(payload);
  }, []);

  const logout = useCallback(() => {
    apiService.logout();
    setUser(null);
  }, []);

  const clearError = useCallback(() => setLoginError(null), []);

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: user !== null,
      isLoading,
      loginError,
      login,
      signup,
      logout,
      clearError,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>');
  return ctx;
};
