import { apiClient, API_BASE_URL } from './client';
import { ApiResponse, CostRecord, TagAnalysis } from '../types';

export interface CostQueryFilters {
  page?: number;
  pageSize?: number;
  startDate?: string;
  endDate?: string;
  accountId?: string;
  service?: string;
  region?: string;
  category?: string;
  minCost?: number;
  maxCost?: number;
  search?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export const costApi = {
  getCosts: async (filters: CostQueryFilters = {}) => {
    const params = new URLSearchParams();
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.pageSize) params.append('page_size', filters.pageSize.toString());
    if (filters.startDate) params.append('start_date', filters.startDate);
    if (filters.endDate) params.append('end_date', filters.endDate);
    if (filters.accountId && filters.accountId !== 'all') params.append('account_id', filters.accountId);
    if (filters.service && filters.service !== 'all') params.append('service', filters.service);
    if (filters.region && filters.region !== 'all') params.append('region', filters.region);
    if (filters.category && filters.category !== 'all') params.append('category', filters.category);
    if (filters.minCost !== undefined) params.append('min_cost', filters.minCost.toString());
    if (filters.maxCost !== undefined) params.append('max_cost', filters.maxCost.toString());
    if (filters.search) params.append('search', filters.search);
    if (filters.sortBy) params.append('sort_by', filters.sortBy);
    if (filters.sortOrder) params.append('sort_order', filters.sortOrder);

    const res = await apiClient.get<ApiResponse<CostRecord[]>>(`/costs?${params.toString()}`);
    return res.data;
  },
  getTagAnalysis: async (accountId: string = 'all') => {
    const res = await apiClient.get<ApiResponse<TagAnalysis>>(`/costs/tag-analysis?account_id=${accountId}`);
    return res.data;
  },
  getCsvDownloadUrl: (filters: CostQueryFilters = {}) => {
    const params = new URLSearchParams();
    if (filters.startDate) params.append('start_date', filters.startDate);
    if (filters.endDate) params.append('end_date', filters.endDate);
    if (filters.accountId && filters.accountId !== 'all') params.append('account_id', filters.accountId);
    if (filters.service && filters.service !== 'all') params.append('service', filters.service);
    if (filters.region && filters.region !== 'all') params.append('region', filters.region);
    if (filters.search) params.append('search', filters.search);
    return `${API_BASE_URL}/costs/export/csv?${params.toString()}`;
  },
  syncLiveCosts: async (days: number = 7) => {
    const res = await apiClient.post<ApiResponse<{ message: string; count: number }>>(`/costs/sync?days=${days}`);
    return res.data;
  },
};

