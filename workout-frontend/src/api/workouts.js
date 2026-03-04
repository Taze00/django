import client from './client'

export const exercises = async () => {
  const response = await client.get('/workout/exercises/')
  return response.data.results
}

export const userProgressions = async () => {
  const response = await client.get('/workout/user-progressions/')
  return response.data.results
}

export const currentWorkout = async () => {
  try {
    const response = await client.get('/workout/workouts/current/')
    return response.data
  } catch (error) {
    if (error.response?.status === 404) {
      return null
    }
    throw error
  }
}

export const createWorkout = async () => {
  const response = await client.post('/workout/workouts/current/')
  return response.data
}

export const addSet = async (workoutId, exerciseId, setNumber, data) => {
  const response = await client.post(`/workout/workouts/${workoutId}/add_set/`, {
    exercise: exerciseId,
    set_number: setNumber,
    ...data,
  })
  return response.data
}

export const completeWorkout = async (workoutId) => {
  const response = await client.post(`/workout/workouts/${workoutId}/complete/`)
  return response.data
}

export const lastPerformance = async () => {
  const response = await client.get('/workout/workouts/last_performance/')
  return response.data
}
