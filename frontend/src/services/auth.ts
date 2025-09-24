import { apiService } from './api';

export interface User {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone?: string;
  role: 'admin' | 'manager' | 'agent' | 'viewer';
  status: 'active' | 'inactive' | 'suspended' | 'pending';
  timezone: string;
  language: string;
  avatar_url?: string;
  last_login_at?: string;
  created_at: string;
  last_active_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

class AuthService {
  private readonly TOKEN_KEY = 'auth_token';
  private readonly USER_KEY = 'auth_user';

  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await apiService.post<AuthResponse>('/auth/login', credentials);

    if (response.data) {
      this.setToken(response.data.access_token);
      this.setUser(response.data.user);
      return response.data;
    }

    throw new Error(response.error || 'Login failed');
  }

  async register(userData: RegisterRequest): Promise<AuthResponse> {
    const response = await apiService.post<AuthResponse>('/auth/register', userData);

    if (response.data) {
      this.setToken(response.data.access_token);
      this.setUser(response.data.user);
      return response.data;
    }

    throw new Error(response.error || 'Registration failed');
  }

  async logout(): Promise<void> {
    try {
      // Try to call logout endpoint
      await apiService.post('/auth/logout');
    } catch (error) {
      // Continue with local logout even if server call fails
      console.warn('Logout API call failed:', error);
    } finally {
      this.clearAuth();
    }
  }

  async getCurrentUser(): Promise<User | null> {
    const response = await apiService.get<User>('/auth/me');
    return response.data || null;
  }

  async changePassword(passwordData: PasswordChangeRequest): Promise<void> {
    const response = await apiService.put('/auth/password', passwordData);
    if (!response.data) {
      throw new Error(response.error || 'Password change failed');
    }
  }

  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(this.TOKEN_KEY);
  }

  setToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  getUser(): User | null {
    if (typeof window === 'undefined') return null;
    const userStr = localStorage.getItem(this.USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  }

  setUser(user: User): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  clearAuth(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  isTokenExpired(): boolean {
    const token = this.getToken();
    if (!token) return true;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      return payload.exp < currentTime;
    } catch {
      return true;
    }
  }

  hasRole(role: string): boolean {
    const user = this.getUser();
    return user?.role === role;
  }

  hasAnyRole(roles: string[]): boolean {
    const user = this.getUser();
    return user ? roles.includes(user.role) : false;
  }

  isAdmin(): boolean {
    return this.hasRole('admin');
  }

  isManager(): boolean {
    return this.hasAnyRole(['admin', 'manager']);
  }

  hasPermission(permission: string): boolean {
    const user = this.getUser();
    if (!user) return false;

    // Admin has all permissions
    if (user.role === 'admin') return true;

    // Manager permissions
    if (user.role === 'manager') {
      const managerPermissions = [
        'view_dashboard', 'view_leads', 'edit_leads', 'view_calls',
        'view_metrics', 'export_data', 'manage_agents'
      ];
      return managerPermissions.includes(permission);
    }

    // Agent permissions
    if (user.role === 'agent') {
      const agentPermissions = [
        'view_dashboard', 'view_leads', 'edit_leads', 'view_calls'
      ];
      return agentPermissions.includes(permission);
    }

    // Viewer permissions
    if (user.role === 'viewer') {
      const viewerPermissions = [
        'view_dashboard', 'view_leads', 'view_calls'
      ];
      return viewerPermissions.includes(permission);
    }

    return false;
  }
}

export const authService = new AuthService();