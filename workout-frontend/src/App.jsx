import { useEffect, useState } from 'react'
import { workoutStore } from './store/workoutStore'
import LoginView from './components/LoginView'
import HomeView from './components/HomeView'
import WorkoutView from './components/WorkoutView/WorkoutView'

export default function App() {
  const isAuthenticated = workoutStore((state) => state.isAuthenticated)
  const initialize = workoutStore((state) => state.initialize)
  const startWorkout = workoutStore((state) => state.startWorkout)
  const setWorkoutActive = workoutStore((state) => state.setWorkoutActive)

  const [view, setView] = useState('home') // 'home' or 'workout'

  useEffect(() => {
    if (isAuthenticated) {
      initialize()
    }
  }, [isAuthenticated, initialize])

  if (!isAuthenticated) {
    return <LoginView />
  }

  if (view === 'workout') {
    return (
      <WorkoutView
        onBack={() => {
          setWorkoutActive(false)
          setView('home')
        }}
      />
    )
  }

  return (
    <HomeView
      onStartWorkout={async () => {
        await startWorkout()
        setWorkoutActive(true)
        setView('workout')
      }}
    />
  )
}
