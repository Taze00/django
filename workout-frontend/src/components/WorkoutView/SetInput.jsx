import { useState, useEffect } from 'react'

export default function SetInput({ exercise, progression, setNumber, lastPerformance, onSubmit }) {
  const [reps, setReps] = useState('')

  useEffect(() => {
    // Initialize with last performance if available
    if (lastPerformance?.[`set${setNumber}`]?.reps !== undefined) {
      setReps(String(lastPerformance[`set${setNumber}`].reps))
    }
  }, [lastPerformance, setNumber])

  const lastReps = lastPerformance?.[`set${setNumber}`]?.reps

  const handleSubmit = (e) => {
    e.preventDefault()
    const repsNum = parseInt(reps, 10)
    if (isNaN(repsNum) || repsNum < 0) {
      alert('Please enter a valid number')
      return
    }
    onSubmit({ reps: repsNum })
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">
          SET {setNumber}: {exercise.name}
        </h2>
        <p className="text-lg text-gray-700 mt-2">{progression.name}</p>
      </div>

      {lastReps !== undefined && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-gray-600">Last time</p>
          <p className="text-2xl font-bold text-blue-600">{lastReps} reps</p>
        </div>
      )}

      {lastReps === undefined && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-gray-600">✨ First time at this level!</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            How many reps?
          </label>
          <input
            type="number"
            value={reps}
            onChange={(e) => setReps(e.target.value)}
            placeholder="0"
            className="w-full px-4 py-3 text-lg border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <button
          type="submit"
          className="w-full py-3 px-4 text-white bg-blue-600 rounded-lg hover:bg-blue-700 font-medium"
        >
          ✓ Set Complete
        </button>
      </form>
    </div>
  )
}
