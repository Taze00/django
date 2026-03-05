import { create } from 'zustand';
import api from '../api';

export const useWorkoutStore = create((set, get) => ({
  exercises: [],
  userProgressions: {},
  currentWorkout: null,
  lastPerformance: {},
  isInitialized: false,
  isLoading: false,

  initialize: async () => {
    const state = get();
    if (state.isInitialized && state.exercises.length > 0) return;
    
    set({ isLoading: true });
    try {
      const [exRes, progRes] = await Promise.all([
        api.get('/exercises/'),
        api.get('/user-progressions/'),
      ]);
      
      const progressionsMap = {};
      (progRes.data.results || []).forEach(prog => {
        progressionsMap[String(prog.exercise)] = prog;
      });

      set({
        exercises: exRes.data.results || [],
        userProgressions: progressionsMap,
        isInitialized: true,
        isLoading: false,
      });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  getCurrentWorkout: async () => {
    set({ isLoading: true });
    try {
      const res = await api.get('/workouts/current/');
      set({ currentWorkout: res.data, isLoading: false });
      return res.data;
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  addSet: async (workoutId, exerciseId, progressionId, setNumber, reps, seconds, restTime, isDropSet) => {
    try {
      const res = await api.post(`/workouts/${workoutId}/add_set/`, {
        exercise: exerciseId,
        progression: progressionId,
        set_number: setNumber,
        reps,
        seconds,
        rest_time_seconds: restTime,
        is_drop_set: isDropSet,
      });
      return res.data;
    } catch (error) {
      throw error;
    }
  },

  completeWorkout: async (workoutId) => {
    try {
      const res = await api.post(`/workouts/${workoutId}/complete/`);
      return res.data;
    } catch (error) {
      throw error;
    }
  },

  getLastPerformance: async () => {
    try {
      const res = await api.get('/last_performance/');
      set({ lastPerformance: res.data });
      return res.data;
    } catch (error) {
      throw error;
    }
  },
}));
