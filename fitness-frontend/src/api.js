import axios from 'axios';

// Use relative path so it works on any domain
const API_BASE = '/api/fitness';

const api = axios.create({
  baseURL: API_BASE,
});

// Request interceptor - add JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - handle 401 with refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        try {
          const res = await axios.post(`/api/token/refresh/`, { refresh });
          localStorage.setItem('access_token', res.data.access);
          api.defaults.headers.Authorization = `Bearer ${res.data.access}`;
          return api(original);
        } catch {
          // Auch der refresh_token ist hin - die Sitzung ist zu Ende.
          //
          // Kein window.location: das warf bisher die ganze SPA weg und
          // zeigte dabei auf /fitness/login, eine Route, die es seit der
          // Umbenennung zu /corvis-app/ nicht mehr gibt (HTTP 404).
          //
          // Stattdessen nur den Zustand zuruecksetzen. logout() loescht
          // beide Token und setzt isAuthenticated auf false; PrivateRoute
          // haengt an genau diesem Wert und leitet daraufhin von selbst
          // auf /login um - innerhalb des Routers, ohne Neuladen.
          //
          // Der Import liegt bewusst hier drin und nicht oben: authStore
          // importiert seinerseits diese Datei, ein statischer Import
          // waere also ein Zyklus. Zum Zeitpunkt dieses Aufrufs sind
          // beide Module laengst ausgewertet.
          const { useAuthStore } = await import('./stores/authStore');
          useAuthStore.getState().logout();
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
