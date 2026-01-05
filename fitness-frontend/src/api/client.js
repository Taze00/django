import axios from 'axios';

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

// Response interceptor: Handle token refresh
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retrying
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          localStorage.setItem('access_token', access);

          originalRequest.headers.Authorization = `Bearer ${access}`;
          return client(originalRequest);
        } else {
          // No refresh token, logout
          localStorage.clear();
          window.location.href = '/fitness/#/login';
        }
      } catch (refreshError) {
        localStorage.clear();
        window.location.href = '/fitness/#/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default client;
