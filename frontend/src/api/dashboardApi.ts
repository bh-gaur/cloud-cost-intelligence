import { apiClient } from './client';
import { ApiResponse, DashboardSummary, FinOpsKpis, CostTrendResponse } from '../types';

export const dashboardApi = {
  getSummary: async (accountId: string = 'all') => {
    const res = await apiClient.get<ApiResponse<DashboardSummary>>(`/dashboard/summary?account_id=${accountId}`);
    return res.data;
  },
  getKpis: async (accountId: string = 'all', startDate?: string, endDate?: string) => {
    let url = `/dashboard/kpis?account_id=${accountId}`;
    if (startDate && endDate) {
      url += `&start_date=${startDate}&end_date=${endDate}`;
    }
    const res = await apiClient.get<ApiResponse<FinOpsKpis>>(url);
    return res.data;
  },
  getTrends: async (range: string = '30d', type: string = 'line', accountId: string = 'all', startDate?: string, endDate?: string) => {
    let url = `/dashboard/trends?range=${range}&type=${type}&account_id=${accountId}`;
    if (startDate && endDate) {
      url += `&start_date=${startDate}&end_date=${endDate}`;
    }
    const res = await apiClient.get<ApiResponse<CostTrendResponse>>(url);
    return res.data;
  },
};

