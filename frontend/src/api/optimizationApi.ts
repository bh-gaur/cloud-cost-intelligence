import { apiClient } from './client';
import { ApiResponse, OptimizationRecommendation, PotentialSavingsSummary } from '../types';

export const optimizationApi = {
  getRecommendations: async (filters: { accountId?: string; service?: string; priority?: string; confidence?: string; status?: string } = {}) => {
    const params = new URLSearchParams();
    if (filters.accountId && filters.accountId !== 'all') params.append('account_id', filters.accountId);
    if (filters.service && filters.service !== 'all') params.append('service', filters.service);
    if (filters.priority && filters.priority !== 'all') params.append('priority', filters.priority);
    if (filters.confidence && filters.confidence !== 'all') params.append('confidence', filters.confidence);
    if (filters.status && filters.status !== 'all') params.append('status', filters.status);

    const res = await apiClient.get<ApiResponse<OptimizationRecommendation[]>>(`/optimization/recommendations?${params.toString()}`);
    return res.data;
  },
  getSummary: async (accountId: string = 'all') => {
    const res = await apiClient.get<ApiResponse<PotentialSavingsSummary>>(`/optimization/summary?account_id=${accountId}`);
    return res.data;
  },
  triggerEvaluation: async (accountId: string = 'all') => {
    const res = await apiClient.post<ApiResponse<{ message: string; count: number }>>(`/optimization/run?account_id=${accountId}`);
    return res.data;
  },
};

