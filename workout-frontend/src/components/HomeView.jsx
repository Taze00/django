import { useEffect } from 'react'
import { workoutStore } from '../store/workoutStore'

export default function HomeView({ onStartWorkout }) {
  const exercises = workoutStore((state) => state.exercises)
  const userProgressions = workoutStore((state) => state.userProgressions)
  const user = workoutStore((state) => state.user)
  const logout = workoutStore((state) => state.logout)

  // Get day of week and determine if it's a workout day
  const getDayInfo = () => {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    const today = new Date()
    const dayName = days[today.getDay()]
    const dayNum = today.getDay()

    // Mo-Fr: Training, Sa: Optional, So: Rest
    let isWorkoutDay = dayNum >= 1 && dayNum <= 5
    let status = isWorkoutDay ? '🏋️ Workout day!' : dayNum === 6 ? '😎 Optional rest day' : '😴 Rest day'

    return { dayName, status }
  }

  const { dayName, status } = getDayInfo()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">💪 Workout Tracker</h1>
            <p className="text-gray-600 mt-1">
              {dayName} — {status}
            </p>
          </div>
          <button
            onClick={logout}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Greeting */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900">
            Hey {user?.first_name || 'there'}! 👋
          </h2>
          <p className="text-gray-600 mt-2">Let's crush your workout today.</p>
        </div>

        {/* Progress Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          {exercises.map((exercise) => {
            const prog = userProgressions[String(exercise.id)]
            if (!prog) return null

            const currentProgression = prog.current_progression

            return (
              <div key={exercise.id} className="bg-white rounded-lg shadow p-6">
                <h3 className="text-xl font-bold text-gray-900">{exercise.name}</h3>
                <p className="text-gray-600 mt-1 text-sm">{exercise.description}</p>

                <div className="mt-6 space-y-4">
                  <div>
                    <p className="text-sm text-gray-600">Current Level</p>
                    <p className="text-2xl font-bold text-blue-600">
                      {currentProgression.name}
                    </p>
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                    <span className="text-sm text-gray-600">Progress Level {currentProgression.level}/7</span>
                    <div className="flex-1 ml-4 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${(currentProgression.level / 7) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Start Workout Button */}
        <div className="flex gap-4">
          <button
            onClick={onStartWorkout}
            className="flex-1 py-4 px-6 text-lg font-bold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition"
          >
            💪 Start Workout
          </button>
        </div>
      </div>
    </div>
  )
}
