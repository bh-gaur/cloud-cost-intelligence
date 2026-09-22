import { apiClient } from './client';
import { ApiResponse } from '../types';

export const notificationApi = {
  getStatus: async () => {
    const res = await apiClient.get<ApiResponse<Record<string, { healthy: boolean; message: string }>>>(
      '/notifications/status'
    );
    return res.data;
  },
  testChannel: async (payload: { channel_type: string; webhook_url?: string; recipient_email?: string }) => {
    const res = await apiClient.post<ApiResponse<{ success: boolean; message: string }>>(
      '/notifications/test',
      payload
    );
    return res.data;
  },
};

