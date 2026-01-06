import axios from 'axios';
import { OfflineQueue } from '../utils/sync';

// Use the deployment URL in production, fallback for local development
const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname === 'alex.volkmann.com'
  ? 'https://alex.volkmann.com/api/fitness'
  : (process.env.VITE_API_URL || '/api/fitness');

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add JWT token
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Handle token refresh and offline
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle offline errors - queue for later sync
    if (!navigator.onLine || error.code === 'ECONNABORTED' || error.message === 'Network Error') {
      // Only queue POST/PUT/PATCH requests (data-mutating operations)
      if (['post', 'put', 'patch'].includes(originalRequest.method)) {
        console.log('[API Client] Offline: Queueing request:', originalRequest.method, originalRequest.url);
        OfflineQueue.addToQueue({
          method: originalRequest.method.toUpperCase(),
          url: originalRequest.url.replace(API_BASE_URL, ''),
          data: originalRequest.data,
          type: originalRequest.data?.type || originalRequest.method.toUpperCase()
        });
        return Promise.reject({ ...error, offline: true });
      }
    }

    // If 401 and not already retrying
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          console.log('[API Client] Token expired, attempting refresh...');
          const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          localStorage.setItem('access_token', access);
          console.log('[API Client] Token refreshed successfully, retrying request...');

          originalRequest.headers.Authorization = `Bearer ${access}`;
          return client(originalRequest);
        } else {
          // No refresh token, logout
          console.log('[API Client] No refresh token found, redirecting to login...');
          localStorage.clear();
          window.location.href = '/fitness/#/login';
        }
      } catch (refreshError) {
        console.error('[API Client] Token refresh failed:', refreshError.response?.data || refreshError.message);
        localStorage.clear();
        window.location.href = '/fitness/#/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default client;
