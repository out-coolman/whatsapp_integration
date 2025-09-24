import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { authService, User, LoginRequest, RegisterRequest } from '../services/auth';
import { useQuery, useQueryClient } from '@tanstack/react-query';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  isAdmin: () => boolean;
  isManager: () => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const queryClient = useQueryClient();

  // Check if user is authenticated and get user data
  const { data: currentUser, isLoading: userLoading } = useQuery({
    queryKey: ['auth', 'currentUser'],
    queryFn: authService.getCurrentUser,
    enabled: authService.isAuthenticated() && !authService.isTokenExpired(),
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  useEffect(() => {
    const initAuth = async () => {
      try {
        if (!authService.isAuthenticated() || authService.isTokenExpired()) {
          authService.clearAuth();
          setUser(null);
          setIsLoading(false);
          return;
        }

        // Try to get user from localStorage first
        const localUser = authService.getUser();
        if (localUser) {
          setUser(localUser);
        }

        // If we have currentUser from query, update it
        if (currentUser) {
          setUser(currentUser);
          authService.setUser(currentUser);
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        authService.clearAuth();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    if (!userLoading) {
      initAuth();
    }
  }, [currentUser, userLoading]);

  const login = async (credentials: LoginRequest): Promise<void> => {
    try {
      setIsLoading(true);
      const response = await authService.login(credentials);
      setUser(response.user);

      // Invalidate and refetch queries that require auth
      queryClient.invalidateQueries();
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterRequest): Promise<void> => {
    try {
      setIsLoading(true);
      const response = await authService.register(userData);
      setUser(response.user);

      // Invalidate and refetch queries
      queryClient.invalidateQueries();
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      setIsLoading(true);
      await authService.logout();
      setUser(null);

      // Clear all cached queries
      queryClient.clear();
    } catch (error) {
      console.error('Logout error:', error);
      // Still clear local auth even if server call fails
      setUser(null);
      authService.clearAuth();
      queryClient.clear();
    } finally {
      setIsLoading(false);
    }
  };

  const refreshUser = async (): Promise<void> => {
    try {
      if (!authService.isAuthenticated()) return;

      const freshUser = await authService.getCurrentUser();
      if (freshUser) {
        setUser(freshUser);
        authService.setUser(freshUser);
      }
    } catch (error) {
      console.error('Refresh user error:', error);
      // If refresh fails, might be invalid token
      await logout();
    }
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    return authService.hasPermission(permission);
  };

  const hasRole = (role: string): boolean => {
    return authService.hasRole(role);
  };

  const hasAnyRole = (roles: string[]): boolean => {
    return authService.hasAnyRole(roles);
  };

  const isAdmin = (): boolean => {
    return authService.isAdmin();
  };

  const isManager = (): boolean => {
    return authService.isManager();
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user && authService.isAuthenticated(),
    isLoading,
    login,
    register,
    logout,
    refreshUser,
    hasPermission,
    hasRole,
    hasAnyRole,
    isAdmin,
    isManager,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}