import { create } from 'zustand';
import axios from 'axios';
import api from '../api';

export const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,

  // Dritter Zustand neben "angemeldet" und "nicht angemeldet":
  // "noch nicht geprueft". Ohne den kann PrivateRoute beim ersten
  // Render nicht zwischen "kein Token" und "Token noch nicht
  // nachgeschlagen" unterscheiden - und wirft jeden Reload auf /login.
  // Wird von checkAuth() genau einmal auf true gesetzt, egal wie die
  // Pruefung ausgeht, und danach nie wieder auf false.
  authChecked: false,

  login: async (username, password) => {
    set({ isLoading: true });
    try {
      // Use global /api/token/ endpoint, not fitness-specific
      const res = await axios.post('/api/token/', { username, password });
      localStorage.setItem('access_token', res.data.access);
      localStorage.setItem('refresh_token', res.data.refresh);

      // Get full user info from API
      const userRes = await api.get('/user/');
      set({
        user: userRes.data,
        isAuthenticated: true,
        isLoading: false,
        // Nach erfolgreichem Login steht das Ergebnis fest, auch falls
        // checkAuth() noch unterwegs sein sollte.
        authChecked: true
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
    set({ user: null, isAuthenticated: false, authChecked: true });
  },

  checkAuth: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      set({ isAuthenticated: false, authChecked: true });
      return;
    }
    try {
      const userRes = await api.get('/user/');
      set({ user: userRes.data, isAuthenticated: true, authChecked: true });
    } catch {
      // Auch der Fehlerfall ist ein Ergebnis: geprueft, nicht angemeldet.
      // (Ein abgelaufener Token wird vom Interceptor in api.js vorher
      // noch per refresh_token zu erneuern versucht.)
      set({ isAuthenticated: false, authChecked: true });
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },
}));
