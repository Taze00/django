import { useState, useEffect } from 'react'
import './App.css'

export default function App() {
  const [exercises, setExercises] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/workout/exercises/')
      .then(res => res.json())
      .then(data => {
        setExercises(data.results || [])
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) return <div className="container"><p>Loading...</p></div>
  if (error) return <div className="container"><p>Error: {error}</p></div>

  return (
    <div className="container">
      <h1>💪 Workout Tracker</h1>
      <p>Backend is ready! Exercises loaded:</p>
      <ul>
        {exercises.map(ex => (
          <li key={ex.id}>{ex.name} ({ex.progressions.length} progressions)</li>
        ))}
      </ul>
    </div>
  )
}
