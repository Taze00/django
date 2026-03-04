import { useState } from 'react'

export default function DropSetInstructions({ exercise, currentProgression, progressions, onDone }) {
  const [step, setStep] = useState(1)

  // Find current progression index
  const currentLevel = currentProgression?.level || 0
  const currentIndex = progressions.findIndex((p) => p.level === currentLevel)

  // Drop-set: current level + 2 levels down (or as many as available)
  const dropSetLevels = [
    progressions[currentIndex],
    currentIndex > 0 ? progressions[currentIndex - 1] : null,
    currentIndex > 1 ? progressions[currentIndex - 2] : null,
  ].filter(Boolean)

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">
          SET 3: DROP-SET 🔥
        </h2>
        <p className="text-gray-700 mt-2">{exercise.name}</p>
      </div>

      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-sm font-medium text-red-800">⚠️ NO REST between drops!</p>
        <p className="text-sm text-red-700 mt-1">
          Do each level until failure, then immediately go to the next.
        </p>
      </div>

      <div className="space-y-4">
        {dropSetLevels.map((prog, idx) => (
          <div
            key={prog.id}
            className={`p-4 rounded-lg border-2 transition ${
              step === idx + 1
                ? 'bg-blue-50 border-blue-500'
                : 'bg-gray-50 border-gray-300'
            }`}
          >
            <p className="text-sm font-medium text-gray-600">
              Drop {idx + 1}
            </p>
            <p className="text-lg font-bold text-gray-900 mt-1">
              {prog.name}
            </p>
            <p className="text-xs text-gray-500 mt-2">
              {idx === 0 && 'Go until failure'}
              {idx === 1 && 'Immediately continue until failure'}
              {idx > 1 && 'Total exhaustion!'}
            </p>
          </div>
        ))}
      </div>

      <button
        onClick={onDone}
        className="w-full py-3 px-4 text-white bg-blue-600 rounded-lg hover:bg-blue-700 font-medium"
      >
        ✓ Drop-Set Complete
      </button>
    </div>
  )
}
