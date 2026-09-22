import { apiClient } from './client';
import { ApiResponse, AnomalyEvent, BudgetRecord } from '../types';

export const alertApi = {
  getAnomalies: async () => {
    const res = await apiClient.get<ApiResponse<AnomalyEvent[]>>('/alerts/anomalies');
    return res.data;
  },
  getBudgets: async () => {
    const res = await apiClient.get<ApiResponse<BudgetRecord[]>>('/alerts/budgets');
    return res.data;
  },
  triggerScan: async () => {
    const res = await apiClient.post<ApiResponse<{ message: string; anomalies_count: number }>>('/alerts/scan');
    return res.data;
  },
};

