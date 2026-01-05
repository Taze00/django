import { useState } from 'react';

export default function ExerciseDetail({ exercise, userProgression, onClose }) {
  const [expandedProgressions, setExpandedProgressions] = useState([]);

  const currentProgression = exercise.progressions.find(
    (p) => p.id === userProgression?.current_progression
  );

  const toggleProgression = (progressionId) => {
    setExpandedProgressions((prev) =>
      prev.includes(progressionId)
        ? prev.filter((id) => id !== progressionId)
        : [...prev, progressionId]
    );
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-end z-50">
      <div className="bg-slate-800 border-t border-slate-700 rounded-t-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-slate-800 border-b border-slate-700 px-4 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white">{exercise.name}</h2>
            <p className="text-slate-400 text-sm">{exercise.description}</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-2xl font-bold w-10 h-10 flex items-center justify-center"
          >
            ×
          </button>
        </div>

        <div className="px-4 py-6 space-y-6">
          {/* Current Level Card */}
          {currentProgression && (
            <div className="bg-gradient-to-r from-blue-600/20 to-blue-700/20 border border-blue-500/30 rounded-2xl p-4">
              <p className="text-blue-300 text-xs font-semibold mb-2">YOUR CURRENT LEVEL</p>
              <h3 className="text-white font-bold text-lg">
                {currentProgression.name}
              </h3>
              {currentProgression.description && (
                <p className="text-blue-100 text-sm mt-2">
                  {currentProgression.description}
                </p>
              )}
              <div className="mt-3 flex items-center justify-between">
                <span className="text-blue-300 text-sm font-semibold">
                  Level {currentProgression.level} of{' '}
                  {exercise.progressions.length}
                </span>
                <div className="flex gap-1">
                  {exercise.progressions.map((_, idx) => (
                    <div
                      key={idx}
                      className={`h-2 rounded-full transition-colors ${
                        idx < currentProgression.level
                          ? 'bg-blue-500 w-4'
                          : 'bg-slate-600 w-2'
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Video Link */}
          {exercise.video_url && (
            <a
              href={exercise.video_url}
              target="_blank"
              rel="noopener noreferrer"
              className="block bg-slate-700/50 hover:bg-slate-700 border border-slate-600 rounded-lg p-3 text-center transition-colors"
            >
              <p className="text-slate-400 text-xs mb-1">📹 INSTRUCTIONAL VIDEO</p>
              <p className="text-blue-400 font-semibold text-sm underline">
                Watch on YouTube
              </p>
            </a>
          )}

          {/* All Progressions */}
          <div>
            <h3 className="text-white font-bold text-lg mb-3">
              All Progressions ({exercise.progressions.length})
            </h3>
            <div className="space-y-2">
              {exercise.progressions.map((progression, idx) => {
                const isExpanded = expandedProgressions.includes(progression.id);
                const isCurrent = progression.id === currentProgression?.id;

                return (
                  <div key={progression.id}>
                    {/* Progression Header */}
                    <button
                      onClick={() => toggleProgression(progression.id)}
                      className={`w-full text-left p-3 rounded-lg transition-colors font-semibold ${
                        isCurrent
                          ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                          : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="bg-slate-600 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">
                            {progression.level}
                          </span>
                          <span>{progression.name}</span>
                          {isCurrent && (
                            <span className="bg-blue-500/30 text-blue-300 px-2 py-1 rounded text-xs font-semibold">
                              CURRENT
                            </span>
                          )}
                        </div>
                        <span className="text-slate-400">
                          {isExpanded ? '▼' : '▶'}
                        </span>
                      </div>
                    </button>

                    {/* Progression Details */}
                    {isExpanded && (
                      <div className="mt-2 ml-2 p-3 bg-slate-700/30 border-l-2 border-slate-600 rounded-r-lg">
                        {progression.description && (
                          <p className="text-slate-300 text-sm mb-3">
                            {progression.description}
                          </p>
                        )}
                        {progression.video_url && (
                          <a
                            href={progression.video_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-block bg-slate-600 hover:bg-slate-500 px-3 py-2 rounded text-slate-300 text-xs font-semibold transition-colors"
                          >
                            Watch Video →
                          </a>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Progression Tips */}
          <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
            <p className="text-green-300 text-xs font-semibold mb-2">💡 PROGRESSION TIPS</p>
            <ul className="text-green-200 text-xs space-y-1">
              <li>
                • Complete current level for 3 consecutive workouts with 8+ reps
                in both sets 1 and 2
              </li>
              <li>• Rest 90 seconds between sets for optimal recovery</li>
              <li>• Focus on form before increasing difficulty</li>
              <li>
                • Drop sets on set 3 help build endurance and muscle fatigue
              </li>
            </ul>
          </div>

          {/* Safety */}
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
            <p className="text-yellow-300 text-xs font-semibold mb-2">
              ⚠️ FORM & SAFETY
            </p>
            <p className="text-yellow-200 text-xs">
              Always prioritize proper form over rep count. If you cannot
              maintain control or proper technique, rest longer or drop to a
              lower progression level.
            </p>
          </div>

          {/* Close Button */}
          <div className="pb-4">
            <button
              onClick={onClose}
              className="w-full bg-slate-700 hover:bg-slate-600 text-white font-bold py-3 rounded-lg transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
