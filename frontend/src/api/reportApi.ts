import { apiClient, API_BASE_URL } from './client';
import { ApiResponse, ReportItem } from '../types';

export const reportApi = {
  getReports: async () => {
    const res = await apiClient.get<ApiResponse<ReportItem[]>>('/reports');
    return res.data;
  },
  generateReport: async (payload: { format: string; start_date: string; end_date: string; account_id?: string; name?: string }) => {
    const res = await apiClient.post<ApiResponse<ReportItem>>('/reports/generate', payload);
    return res.data;
  },
  deleteReport: async (id: string) => {
    const res = await apiClient.delete<ApiResponse<any>>(`/reports/${id}`);
    return res.data;
  },
  getDownloadUrl: (id: string) => {
    return `${API_BASE_URL}/reports/${id}/download`;
  },
};

