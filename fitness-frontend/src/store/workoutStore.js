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
  addSet: async (exerciseId, progressionId, reps, setNumber, isDropSet = false, seconds = null) => {
    try {
      const currentWorkout = get().currentWorkout;
      if (!currentWorkout) {
        console.error('[Workout Store] No current workout found');
        return null;
      }

      // Check if set already exists
      const existingSet = currentWorkout.sets?.find(
        (s) => s.exercise === exerciseId && s.set_number === setNumber && s.is_drop_set === isDropSet
      );

      const setData = {
        workout: currentWorkout.id,
        exercise: exerciseId,
        progression: progressionId,
        set_number: setNumber,
        is_drop_set: isDropSet,
      };

      // Add reps or seconds based on exercise type
      if (seconds !== null) {
        setData.seconds = seconds;
      } else {
        setData.reps = reps;
      }

      let response;
      if (existingSet) {
        // Update existing set
        console.log('[Workout Store] Updating set with data:', setData);
        response = await setAPI.update(existingSet.id, setData);
        console.log('[Workout Store] Set updated successfully:', response.data);
      } else {
        // Create new set
        console.log('[Workout Store] Creating set with data:', setData);
        response = await setAPI.create(setData);
        console.log('[Workout Store] Set created successfully:', response.data);
      }

      // Update current workout with new/updated set
      const updatedWorkout = { ...currentWorkout };
      if (!updatedWorkout.sets) updatedWorkout.sets = [];

      if (existingSet) {
        // Replace existing set
        const index = updatedWorkout.sets.findIndex((s) => s.id === existingSet.id);
        if (index !== -1) {
          updatedWorkout.sets[index] = response.data;
        }
      } else {
        // Add new set
        updatedWorkout.sets.push(response.data);
      }

      set({ currentWorkout: updatedWorkout });
      return response.data;
    } catch (error) {
      console.error('[Workout Store] Error saving set:', error.response?.data || error.message);
      set({ error: 'Failed to save set' });
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

  // Initialize (fetch all data in correct order)
  initialize: async () => {
    set({ isLoading: true });
    try {
      // IMPORTANT: Must fetch current workout FIRST to initialize UserExerciseProgressions
      await get().fetchCurrentWorkout();
      // Then fetch progressions after workout (to get the newly created ones)
      await get().fetchUserProgressions();
      // Finally fetch exercises in parallel with above if not done yet
      await get().fetchExercises();
    } catch (error) {
      console.error('Initialize error:', error);
      set({ error: 'Failed to initialize' });
    } finally {
      set({ isLoading: false });
    }
  },
}));
