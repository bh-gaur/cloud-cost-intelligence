import { apiClient } from './client';
import { ApiResponse, AccountBreakdownItem } from '../types';

export const accountApi = {
  getAccounts: async (range: string = '30d') => {
    const res = await apiClient.get<ApiResponse<AccountBreakdownItem[]>>(`/accounts?range=${range}`);
    return res.data;
  },
  getAccountDetail: async (accountId: string) => {
    const res = await apiClient.get<ApiResponse<any>>(`/accounts/${accountId}`);
    return res.data;
  },
};

