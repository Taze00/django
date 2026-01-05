import { create } from 'zustand';
import { workoutAPI, exerciseAPI, setAPI } from '../api';

export const useWorkoutStore = create((set, get) => ({
  currentWorkout: null,
  exercises: [],
  userProgressions: {},
  isLoading: false,
  error: null,
  activeExerciseIndex: 0,

  // Fetch exercises
  fetchExercises: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await exerciseAPI.list();
      // Handle paginated response (DRF returns {count, next, previous, results})
      const exercises = response.data.results || response.data;
      set({ exercises, isLoading: false });
      return exercises;
    } catch (error) {
      console.error('Failed to fetch exercises:', error);
      set({ error: 'Failed to fetch exercises', isLoading: false });
      return [];
    }
  },

  // Fetch user progressions
  fetchUserProgressions: async () => {
    try {
      const response = await exerciseAPI.userProgressions();
      const progressionsMap = {};
      response.data.forEach((prog) => {
        progressionsMap[prog.exercise] = prog;
      });
      set({ userProgressions: progressionsMap });
      return progressionsMap;
    } catch (error) {
      set({ error: 'Failed to fetch progressions' });
      return {};
    }
  },

  // Get or create today's workout
  fetchCurrentWorkout: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await workoutAPI.current();
      set({
        currentWorkout: response.data,
        isLoading: false,
        activeExerciseIndex: 0
      });
      return response.data;
    } catch (error) {
      set({ error: 'Failed to fetch workout', isLoading: false });
      return null;
    }
  },

  // Add set to workout
  addSet: async (exerciseId, progressionId, reps, setNumber, isDropSet = false) => {
    try {
      const currentWorkout = get().currentWorkout;
      if (!currentWorkout) return null;

      const setData = {
        workout: currentWorkout.id,
        exercise: exerciseId,
        progression: progressionId,
        reps: reps,
        set_number: setNumber,
        is_drop_set: isDropSet,
      };

      const response = await setAPI.create(setData);

      // Update current workout with new set
      const updatedWorkout = { ...currentWorkout };
      if (!updatedWorkout.sets) updatedWorkout.sets = [];
      updatedWorkout.sets.push(response.data);

      set({ currentWorkout: updatedWorkout });
      return response.data;
    } catch (error) {
      set({ error: 'Failed to add set' });
      return null;
    }
  },

  // Complete workout
  completeWorkout: async () => {
    try {
      const currentWorkout = get().currentWorkout;
      if (!currentWorkout) return null;

      const response = await workoutAPI.complete(currentWorkout.id);

      set({
        currentWorkout: response.data.workout,
        error: null
      });

      return response.data;
    } catch (error) {
      set({ error: 'Failed to complete workout' });
      return null;
    }
  },

  // Update warmup checklist
  updateWarmup: async (warmupData) => {
    try {
      const currentWorkout = get().currentWorkout;
      if (!currentWorkout) return null;

      const response = await workoutAPI.updateWarmup(currentWorkout.id, warmupData);

      const updatedWorkout = { ...currentWorkout };
      updatedWorkout.warmup = response.data;
      set({ currentWorkout: updatedWorkout });

      return response.data;
    } catch (error) {
      set({ error: 'Failed to update warmup' });
      return null;
    }
  },

  // Set active exercise
  setActiveExerciseIndex: (index) => set({ activeExerciseIndex: index }),

  // Clear error
  clearError: () => set({ error: null }),

  // Initialize (fetch all data)
  initialize: async () => {
    set({ isLoading: true });
    await get().fetchExercises();
    await get().fetchUserProgressions();
    await get().fetchCurrentWorkout();
    set({ isLoading: false });
  },
}));
