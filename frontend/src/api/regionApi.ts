import { apiClient } from './client';
import { ApiResponse, RegionBreakdownItem } from '../types';

export const regionApi = {
  getRegions: async (range: string = '30d') => {
    const res = await apiClient.get<ApiResponse<RegionBreakdownItem[]>>(`/regions?range=${range}`);
    return res.data;
  },
};

