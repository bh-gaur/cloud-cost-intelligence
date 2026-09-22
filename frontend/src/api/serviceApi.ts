import { apiClient } from './client';
import { ApiResponse, ServiceBreakdownItem } from '../types';

export const serviceApi = {
  getServices: async (accountId: string = 'all', range: string = '30d') => {
    const res = await apiClient.get<ApiResponse<ServiceBreakdownItem[]>>(
      `/services?account_id=${accountId}&range=${range}`
    );
    return res.data;
  },
  getServiceDetail: async (serviceName: string, accountId: string = 'all') => {
    const res = await apiClient.get<ApiResponse<any>>(
      `/services/${encodeURIComponent(serviceName)}?account_id=${accountId}`
    );
    return res.data;
  },
};

