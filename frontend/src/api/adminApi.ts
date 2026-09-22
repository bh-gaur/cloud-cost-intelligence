import { apiClient } from './client';
import type { ApiResponse, User } from '../types';

export interface AuditLogEntry {
  id: number;
  action: string;
  resource_type: string;
  resource_id?: string;
  user_email?: string;
  status: string;
  ip_address?: string;
  details?: Record<string, any>;
  created_at: string;
}

export interface SystemStatus {
  environment: string;
  demo_mode: boolean;
  report_retention_days: number;
  database_url_masked: string;
  app_name: string;
  version: string;
}

export const adminApi = {
  getUsers: async () => {
    const res = await apiClient.get<ApiResponse<User[]>>('/admin/users');
    return res.data;
  },
  getAuditLogs: async (page = 1, pageSize = 50) => {
    const res = await apiClient.get<ApiResponse<AuditLogEntry[]>>(`/admin/audit-logs?page=${page}&page_size=${pageSize}`);
    return res.data;
  },
  getSystemStatus: async () => {
    const res = await apiClient.get<ApiResponse<SystemStatus>>('/admin/system');
    return res.data;
  },
  deleteUser: async (userId: string) => {
    const res = await apiClient.delete<ApiResponse<{ message: string }>>(`/admin/users/${userId}`);
    return res.data;
  },
};

