import { create } from 'zustand'
import * as workoutAPI from '../api/workouts'
import * as authAPI from '../api/auth'

export const workoutStore = create((set, get) => ({
  // Auth State
  token: localStorage.getItem('token') || null,
  refreshToken: localStorage.getItem('refreshToken') || null,
  isAuthenticated: !!localStorage.getItem('token'),
  user: null,

  // Data State
  exercises: [],
  userProgressions: {}, // String-keyed: {"1": {...}, "2": {...}}
  lastPerformances: {}, // {prog_id_str: {set1: {...}, set2: {...}}}

  // Workout State
  activeWorkout: null,
  currentStep: 0, // 0-5
  isWorkoutActive: false,
  initialized: false,

  // Auth Actions
  login: async (username, password) => {
    try {
      const { access, refresh } = await authAPI.login(username, password)
      localStorage.setItem('token', access)
      localStorage.setItem('refreshToken', refresh)
      set({
        token: access,
        refreshToken: refresh,
        isAuthenticated: true,
      })
      // Load initial data
      await get().initialize()
      return true
    } catch (error) {
      console.error('Login failed:', error)
      return false
    }
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    set({
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      user: null,
      exercises: [],
      userProgressions: {},
      activeWorkout: null,
      currentStep: 0,
      isWorkoutActive: false,
      initialized: false,
    })
  },

  // Initialize: Load exercises and user progressions (guard against double-load)
  initialize: async () => {
    const { initialized, exercises } = get()
    if (initialized && exercises.length > 0) return

    try {
      set({ initialized: true })
      const [exData, progData] = await Promise.all([
        workoutAPI.exercises(),
        workoutAPI.userProgressions(),
      ])

      // progData is already a dictionary with string keys from backend
      set({
        exercises: exData,
        userProgressions: progData,
      })
    } catch (error) {
      console.error('Initialize failed:', error)
      set({ initialized: false })
    }
  },

  // Fetch user progressions (for refresh after complete)
  fetchUserProgressions: async () => {
    try {
      const progData = await workoutAPI.userProgressions()
      // progData is already a dictionary with string keys from backend
      set({ userProgressions: progData })
    } catch (error) {
      console.error('Fetch progressions failed:', error)
    }
  },

  // Fetch last performances
  fetchLastPerformances: async () => {
    try {
      const perfData = await workoutAPI.lastPerformance()
      set({ lastPerformances: perfData })
    } catch (error) {
      console.error('Fetch last performance failed:', error)
    }
  },

  // Workout Actions
  startWorkout: async () => {
    try {
      let workout = await workoutAPI.currentWorkout()
      if (!workout) {
        workout = await workoutAPI.createWorkout()
      }
      set({
        activeWorkout: workout,
        currentStep: 0,
        isWorkoutActive: true,
      })
      await get().fetchLastPerformances()
      return workout
    } catch (error) {
      console.error('Start workout failed:', error)
    }
  },

  addSet: async (exerciseId, setNumber, progressionId, data) => {
    try {
      const { activeWorkout } = get()
      if (!activeWorkout) return

      await workoutAPI.addSet(activeWorkout.id, exerciseId, setNumber, progressionId, data)
    } catch (error) {
      console.error('Add set failed:', error)
    }
  },

  completeWorkout: async () => {
    try {
      const { activeWorkout } = get()
      if (!activeWorkout) return

      const result = await workoutAPI.completeWorkout(activeWorkout.id)

      // Refresh progressions to show new levels
      try {
        await get().fetchUserProgressions()
      } catch (error) {
        console.error('Failed to refresh progressions:', error)
      }

      set({
        activeWorkout: null,
        currentStep: 0,
        isWorkoutActive: false,
      })

      return result // {workout, upgrades, downgrades}
    } catch (error) {
      console.error('Complete workout failed:', error)
      return null
    }
  },

  setStep: (step) => {
    set({ currentStep: step })
  },

  setWorkoutActive: (active) => {
    set({ isWorkoutActive: active })
  },
}))
