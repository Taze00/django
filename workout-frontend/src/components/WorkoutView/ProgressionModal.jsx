export default function ProgressionModal({ upgrades, downgrades, onClose }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-md w-full space-y-6 p-6">
        <h2 className="text-2xl font-bold text-gray-900 text-center">
          Workout Complete! 🎉
        </h2>

        {upgrades && upgrades.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-green-700">✨ Upgrades</h3>
            {upgrades.map((upgrade) => (
              <div key={upgrade.exercise_id} className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-sm text-gray-600">{upgrade.exercise_name}</p>
                <p className="text-lg font-bold text-green-700 mt-1">
                  → {upgrade.new_progression_name}
                </p>
                <p className="text-xs text-green-600 mt-2">
                  After {upgrade.sessions_at_target} successful sessions
                </p>
              </div>
            ))}
          </div>
        )}

        {downgrades && downgrades.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-blue-700">💪 Adjustments</h3>
            {downgrades.map((downgrade) => (
              <div key={downgrade.exercise_id} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-gray-600">{downgrade.exercise_name}</p>
                <p className="text-lg font-bold text-blue-700 mt-1">
                  {downgrade.progression_name}
                </p>
                <p className="text-xs text-blue-600 mt-2">
                  💪 Keep building strength!
                </p>
              </div>
            ))}
          </div>
        )}

        {(!upgrades || upgrades.length === 0) && (!downgrades || downgrades.length === 0) && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
            <p className="text-gray-700">Great work! Keep it up! 🙌</p>
          </div>
        )}

        <button
          onClick={onClose}
          className="w-full py-3 px-4 text-white bg-blue-600 rounded-lg hover:bg-blue-700 font-medium"
        >
          Done
        </button>
      </div>
    </div>
  )
}
