import { useMemo } from 'react'
import SetInput from './SetInput'
import TimerInput from './TimerInput'
import DropSetInstructions from './DropSetInstructions'

export default function ExerciseCard({ exercise, setNumber, currentProgression, lastPerformance, onSetCompleted }) {
  // Get exercise-specific progressions for this set
  const exerciseProgressions = useMemo(() => {
    return exercise.progressions.sort((a, b) => a.level - b.level)
  }, [exercise])

  // Use current progression passed from WorkoutView
  const progression = currentProgression

  if (!progression) {
    return <div className="p-4 text-red-600">Error: No current progression found</div>
  }

  // Get last performance for this specific set number
  const setPerf = lastPerformance?.[String(progression.id)]

  // Routing: Set 3 with Drop-Sets
  if (setNumber === 3) {
    if (progression.level === 1) {
      // Level 1: just say "Go until failure"
      return (
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              SET {setNumber}: {exercise.name}
            </h2>
            <p className="text-lg text-gray-700 mt-2">{progression.name}</p>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
            <p className="text-2xl font-bold text-green-700">🔥 Go until failure!</p>
            <p className="text-sm text-green-600 mt-2">Give it everything you've got</p>
          </div>

          <button
            onClick={() => onSetCompleted()}
            className="w-full py-3 px-4 text-white bg-blue-600 rounded-lg hover:bg-blue-700 font-medium"
          >
            ✓ Done
          </button>
        </div>
      )
    } else {
      // Level > 1: show drop-set instructions
      return (
        <DropSetInstructions
          exercise={exercise}
          currentProgression={progression}
          progressions={exerciseProgressions}
          onDone={() => onSetCompleted({ is_drop_set: true })}
        />
      )
    }
  }

  // Set 1-2 routing
  if (progression.target_type === 'time') {
    return (
      <TimerInput
        exercise={exercise}
        progression={progression}
        setNumber={setNumber}
        lastPerformance={setPerf}
        onSubmit={(data) => onSetCompleted(data)}
      />
    )
  }

  return (
    <SetInput
      exercise={exercise}
      progression={progression}
      setNumber={setNumber}
      lastPerformance={setPerf}
      onSubmit={(data) => onSetCompleted(data)}
    />
  )
}
