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

// State to manage silent refresh and prevent parallel refresh loops
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: any) => void;
}> = [];

const processQueue = (error: any = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve();
    }
  });
  failedQueue = [];
};

const PUBLIC_AUTH_PATHS = [
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
  '/verify-email',
  '/invite',
];

const isPublicAuthRoute = () => {
  const path = window.location.pathname;
  return PUBLIC_AUTH_PATHS.some((p) => path.includes(p));
};

// Response interceptor: silent token refresh on 401; cleanup stale org on 403
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 Unauthorized
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      const reqUrl = originalRequest.url || '';
      // Don't refresh on auth endpoints
      if (
        reqUrl.includes('/auth/login') ||
        reqUrl.includes('/auth/refresh') ||
        reqUrl.includes('/auth/register') ||
        reqUrl.includes('/auth/forgot-password') ||
        reqUrl.includes('/auth/reset-password')
      ) {
        return Promise.reject(error);
      }

      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        if (!isPublicAuthRoute()) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('active_org_id');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => {
            const newToken = localStorage.getItem('access_token');
            if (newToken && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshResp = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const authData = refreshResp.data?.data || refreshResp.data;
        const newAccessToken = authData?.access_token;
        const newRefreshToken = authData?.refresh_token;

        if (newAccessToken) {
          localStorage.setItem('access_token', newAccessToken);
          if (newRefreshToken) {
            localStorage.setItem('refresh_token', newRefreshToken);
          }
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          }
          processQueue(null);
          return apiClient(originalRequest);
        } else {
          throw new Error('Refresh token response missing access_token');
        }
      } catch (refreshErr) {
        processQueue(refreshErr);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('active_org_id');
        if (!isPublicAuthRoute()) {
          window.location.href = '/login';
        }
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    // Handle 403 Tenant or Permission Mismatches
    if (error.response?.status === 403) {
      const errMsg =
        error.response?.data?.error?.message ||
        error.response?.data?.detail ||
        '';
      if (
        errMsg.includes('Access to the requested organization is denied') ||
        errMsg.includes('not associated with any active organization')
      ) {
        localStorage.removeItem('active_org_id');
      }
    }

    return Promise.reject(error);
  }
);
