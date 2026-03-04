import { useState, useEffect } from 'react'

export default function TimerInput({ exercise, progression, setNumber, lastPerformance, onSubmit }) {
  const [seconds, setSeconds] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [displayTime, setDisplayTime] = useState(0)
  const [isEditMode, setIsEditMode] = useState(false)

  const lastSeconds = lastPerformance?.[`set${setNumber}`]?.seconds

  useEffect(() => {
    if (isRunning) {
      const timer = setInterval(() => {
        setDisplayTime((prev) => prev + 1)
      }, 1000)
      return () => clearInterval(timer)
    }
  }, [isRunning])

  const handleStart = () => {
    setDisplayTime(0)
    setIsRunning(true)
  }

  const handleStop = () => {
    setIsRunning(false)
  }

  const handleManualSubmit = (e) => {
    e.preventDefault()
    const secsNum = parseInt(seconds, 10)
    if (isNaN(secsNum) || secsNum < 0) {
      alert('Please enter a valid number')
      return
    }
    onSubmit({ seconds: secsNum })
  }

  const handleTimerSubmit = () => {
    onSubmit({ seconds: displayTime })
  }

  if (isEditMode) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            SET {setNumber}: {exercise.name}
          </h2>
          <p className="text-lg text-gray-700 mt-2">{progression.name}</p>
        </div>

        {lastSeconds !== undefined && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-gray-600">Last time</p>
            <p className="text-2xl font-bold text-blue-600">{lastSeconds}s</p>
          </div>
        )}

        <form onSubmit={handleManualSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Seconds held
            </label>
            <input
              type="number"
              value={seconds}
              onChange={(e) => setSeconds(e.target.value)}
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

        <button
          onClick={() => setIsEditMode(false)}
          className="w-full py-2 px-4 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300"
        >
          ← Back to Timer
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">
          SET {setNumber}: {exercise.name}
        </h2>
        <p className="text-lg text-gray-700 mt-2">{progression.name}</p>
      </div>

      {lastSeconds !== undefined && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-gray-600">Last time</p>
          <p className="text-2xl font-bold text-blue-600">{lastSeconds}s</p>
        </div>
      )}

      {lastSeconds === undefined && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-gray-600">✨ First time at this level!</p>
        </div>
      )}

      <div className="bg-green-50 border border-green-200 rounded-lg p-12 text-center">
        <div className="text-6xl font-mono font-bold text-green-600 mb-4">
          {String(Math.floor(displayTime / 60)).padStart(2, '0')}:{String(displayTime % 60).padStart(2, '0')}
        </div>
        <p className="text-gray-600 text-sm">seconds held</p>
      </div>

      <div className="flex gap-4">
        {!isRunning && displayTime === 0 && (
          <button
            onClick={handleStart}
            className="flex-1 py-3 px-4 text-white bg-green-600 rounded-lg hover:bg-green-700 font-medium"
          >
            ▶ Start Timer
          </button>
        )}

        {isRunning && (
          <button
            onClick={handleStop}
            className="flex-1 py-3 px-4 text-white bg-yellow-600 rounded-lg hover:bg-yellow-700 font-medium"
          >
            ⏹ Stop Timer
          </button>
        )}

        {displayTime > 0 && !isRunning && (
          <>
            <button
              onClick={handleTimerSubmit}
              className="flex-1 py-3 px-4 text-white bg-blue-600 rounded-lg hover:bg-blue-700 font-medium"
            >
              ✓ Done
            </button>
            <button
              onClick={() => setIsEditMode(true)}
              className="px-4 py-3 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 font-medium"
            >
              Edit
            </button>
          </>
        )}
      </div>
    </div>
  )
}
