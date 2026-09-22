import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach JWT access token & active organization ID header
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const orgId = localStorage.getItem('active_org_id');
  if (orgId && config.headers) {
    config.headers['X-Organization-ID'] = orgId;
  }
  return config;
});

// Response interceptor: handle 401 and redirect to login; clean stale org on 403 tenant mismatch
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !window.location.pathname.includes('/login')) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('active_org_id');
      window.location.href = '/login';
    } else if (
      error.response?.status === 403 &&
      (error.response?.data?.detail?.includes('Access to the requested organization is denied') ||
       error.response?.data?.detail?.includes('not associated with any active organization'))
    ) {
      localStorage.removeItem('active_org_id');
    }
    return Promise.reject(error);
  }
);

