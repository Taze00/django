import { create } from 'zustand';
import client from '../api/client';

export const useStatsStore = create((set) => ({
  overview: null,
  exerciseProgress: null,
  progressionHistory: null,
  isLoading: false,
  error: null,

  fetchOverview: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await client.get('/stats/overview/');
      set({ overview: response.data, isLoading: false });
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch overview';
      set({ error: errorMessage, isLoading: false });
    }
  },

  fetchExerciseProgress: async (exerciseId, days = 30) => {
    set({ isLoading: true, error: null });
    try {
      const response = await client.get(`/stats/exercise-progress/?exercise_id=${exerciseId}&days=${days}`);
      set({ exerciseProgress: response.data, isLoading: false });
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch progress';
      set({ error: errorMessage, isLoading: false });
    }
  },

  fetchProgressionHistory: async (exerciseId) => {
    set({ isLoading: true, error: null });
    try {
      const response = await client.get(`/stats/progression-history/?exercise_id=${exerciseId}`);
      set({ progressionHistory: response.data, isLoading: false });
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch history';
      set({ error: errorMessage, isLoading: false });
    }
  },

  clearError: () => set({ error: null }),
}));
