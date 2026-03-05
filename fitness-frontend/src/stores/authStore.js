import { create } from 'zustand';
import axios from 'axios';
import api from '../api';

export const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,

  login: async (username, password) => {
    set({ isLoading: true });
    try {
      // Use global /api/token/ endpoint, not fitness-specific
      const res = await axios.post('/api/token/', { username, password });
      localStorage.setItem('access_token', res.data.access);
      localStorage.setItem('refresh_token', res.data.refresh);
      
      // Get user info - simplified
      set({ 
        user: { username }, 
        isAuthenticated: true,
        isLoading: false 
      });
      return true;
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, isAuthenticated: false });
  },

  checkAuth: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      set({ isAuthenticated: false });
      return;
    }
    set({ isAuthenticated: true });
  },
}));
