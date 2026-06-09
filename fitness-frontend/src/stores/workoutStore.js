import { create } from 'zustand';
import api from '../api';

export const useWorkoutStore = create((set, get) => ({
  exercises: [],
  userProgressions: {},
  workouts: [],
  currentWorkout: (() => {
    // Restore currentWorkout from localStorage if it exists
    try {
      const saved = localStorage.getItem('currentWorkout');
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      return null;
    }
  })(),
  lastPerformance: {},
  trainingDays: [1, 2, 3, 4, 5], // Mon-Fri default
  streak: { current: 0, longest: 0, trained_today: false, rested_today: false, is_training_day_today: false },
  timeline: [],
  weeklyReview: null,
  isInitialized: false,
  isLoading: false,

  initialize: async () => {
    const state = get();
    if (state.isInitialized && state.exercises.length > 0) return;

    set({ isLoading: true });
    try {
      const [exRes, progRes, workRes, settRes, streakRes, timelineRes, weeklyRes] = await Promise.all([
        api.get('/exercises/'),
        api.get('/user-progressions/'),
        api.get('/workouts/'),
        api.get('/profile/settings/').catch(() => ({ data: { training_days: [1, 2, 3, 4, 5] } })),
        api.get('/streak/').catch(() => ({ data: null })),
        api.get('/timeline/').catch(() => ({ data: { events: [] } })),
        api.get('/weekly-review/').catch(() => ({ data: null })),
      ]);

      const progressionsMap = {};
      (progRes.data.results || []).forEach(prog => {
        progressionsMap[String(prog.exercise)] = prog;
      });

      set({
        exercises: exRes.data.results || [],
        userProgressions: progressionsMap,
        workouts: workRes.data.results || [],
        trainingDays: settRes.data.training_days || [1, 2, 3, 4, 5],
        streak: streakRes.data || get().streak,
        timeline: timelineRes.data?.events || [],
        weeklyReview: weeklyRes.data || null,
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
      // Save to localStorage so it persists if app closes
      localStorage.setItem('currentWorkout', JSON.stringify(res.data));
      return res.data;
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  addSet: async (workoutId, exerciseId, progressionId, setNumber, reps, seconds, restTime, isDropSet, dropSetCompleted) => {
    try {
      const res = await api.post(`/workouts/${workoutId}/add_set/`, {
        exercise: exerciseId,
        progression: progressionId,
        set_number: setNumber,
        reps,
        seconds,
        rest_time_seconds: restTime,
        is_drop_set: isDropSet,
        drop_set_completed: dropSetCompleted,
      });
      return res.data;
    } catch (error) {
      throw error;
    }
  },

  completeWorkout: async (workoutId) => {
    try {
      const res = await api.post(`/workouts/${workoutId}/complete/`);
      // Refresh workouts list + streak + timeline after completing
      const [workRes, streakRes, timelineRes] = await Promise.all([
        api.get('/workouts/'),
        api.get('/streak/').catch(() => ({ data: null })),
        api.get('/timeline/').catch(() => ({ data: { events: [] } })),
      ]);
      set({
        workouts: workRes.data.results || [],
        currentWorkout: null,
        streak: streakRes.data || get().streak,
        timeline: timelineRes.data?.events || get().timeline,
      });
      // Clear localStorage when workout is done
      localStorage.removeItem('currentWorkout');
      return res.data;
    } catch (error) {
      throw error;
    }
  },

  refreshStreak: async () => {
    try {
      const res = await api.get('/streak/');
      set({ streak: res.data });
      return res.data;
    } catch (error) {
      throw error;
    }
  },

  markRestDay: async () => {
    try {
      await api.post('/rest-day/');
      const res = await api.get('/streak/');
      set({ streak: res.data });
      return res.data;
    } catch (error) {
      throw error;
    }
  },

  unmarkRestDay: async () => {
    try {
      await api.delete('/rest-day/remove/');
      const res = await api.get('/streak/');
      set({ streak: res.data });
      return res.data;
    } catch (error) {
      throw error;
    }
  },

  getLastPerformance: async () => {
    try {
      const res = await api.get('/workouts/last_performance/');
      set({ lastPerformance: res.data });
      return res.data;
    } catch (error) {
      throw error;
    }
  },

  resetWorkout: async (workoutId) => {
    try {
      const res = await api.post(`/workouts/${workoutId}/reset/`);
      // Refresh workouts list after reset (workout is deleted)
      const workRes = await api.get('/workouts/');
      set({ workouts: workRes.data.results || [] });
      return res.data;
    } catch (error) {
      throw error;
    }
  },

  updateTrainingDays: async (trainingDays) => {
    try {
      const res = await api.put('/profile/settings/', { training_days: trainingDays });
      const updatedDays = res.data.training_days || trainingDays;
      set({ trainingDays: updatedDays });
      return res.data;
    } catch (error) {
      throw error;
    }
  },
}));
