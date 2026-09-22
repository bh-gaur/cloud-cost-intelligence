import { apiClient } from './client';
import { ApiResponse, AuthTokens, User } from '../types';

export const authApi = {
  login: async (credentials: { email: string; password: string }) => {
    const res = await apiClient.post<ApiResponse<AuthTokens>>('/auth/login', credentials);
    return res.data;
  },
  register: async (userData: { email: string; password: string; full_name?: string; org_name?: string; role_name?: string }) => {
    const res = await apiClient.post<ApiResponse<User>>('/auth/register', userData);
    return res.data;
  },
  getCurrentUser: async () => {
    const res = await apiClient.get<ApiResponse<User>>('/auth/me');
    return res.data;
  },
  googleAuth: async (payload: { code?: string; credential?: string; redirect_uri?: string }) => {
    const res = await apiClient.post<ApiResponse<AuthTokens & { user: User }>>('/auth/google', payload);
    return res.data;
  },
  forgotPassword: async (email: string) => {
    const res = await apiClient.post<ApiResponse<{ message: string }>>('/auth/forgot-password', { email });
    return res.data;
  },
  resetPassword: async (payload: { token: string; new_password: string }) => {
    const res = await apiClient.post<ApiResponse<{ message: string }>>('/auth/reset-password', payload);
    return res.data;
  },
  verifyEmail: async (token: string) => {
    const res = await apiClient.post<ApiResponse<{ message: string }>>('/auth/verify-email', { token });
    return res.data;
  },
  getInviteDetails: async (token: string) => {
    const res = await apiClient.get<ApiResponse<{
      id: string;
      organization_id: string;
      organization_name: string;
      email: string;
      role: string;
      status: string;
      is_expired: boolean;
      user_exists: boolean;
      expires_at: string;
    }>>(`/auth/invite-details?token=${encodeURIComponent(token)}`);
    return res.data;
  },
  acceptInviteRegister: async (payload: { token: string; full_name: string; password: string }) => {
    const res = await apiClient.post<ApiResponse<AuthTokens & { organization_id: string; organization_name: string; role: string; user: User }>>('/auth/accept-invite-register', payload);
    return res.data;
  },
  acceptInvite: async (token: string) => {
    const res = await apiClient.post<ApiResponse<{ message: string; organization_id: string; organization_name: string; role: string }>>('/auth/accept-invite', { token });
    return res.data;
  },
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};

