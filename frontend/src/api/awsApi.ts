import { apiClient } from './client';
import { ApiResponse } from '../types';

export interface AWSConnectionTestRequest {
  account_id?: string;
  role_arn?: string;
  external_id?: string;
  region?: string;
}

export interface AWSConnectionTestResponse {
  is_connected: boolean;
  account_id_masked: string;
  sts_identity_verified: boolean;
  cost_explorer_accessible: boolean;
  budgets_accessible: boolean;
  status_message: string;
  timestamp: string;
}

export const awsApi = {
  testConnection: async (payload: AWSConnectionTestRequest) => {
    const res = await apiClient.post<ApiResponse<AWSConnectionTestResponse>>(
      '/aws/test-connection',
      payload
    );
    return res.data;
  },
  getAccounts: async () => {
    const res = await apiClient.get<ApiResponse<any[]>>('/aws/accounts');
    return res.data;
  },
  triggerSync: async (days: number = 7) => {
    const res = await apiClient.post<ApiResponse<{ message: string; count: number }>>(
      `/aws/sync?days=${days}`
    );
    return res.data;
  },
};

