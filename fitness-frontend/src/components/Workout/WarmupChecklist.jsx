import { useState, useEffect } from 'react';
import { useWorkoutStore } from '../../store/workoutStore';

const WARMUP_ITEMS = [
  { key: 'wrists', label: 'Wrist Rotations', emoji: '🤚' },
  { key: 'shoulders', label: 'Shoulder Rolls', emoji: '🔄' },
  { key: 'elbows', label: 'Elbow Circles', emoji: '⭕' },
  { key: 'back', label: 'Back Arch Hold', emoji: '⬅️' },
  { key: 'legs', label: 'Leg Shakes', emoji: '🦵' },
];

export default function WarmupChecklist({ workout }) {
  const { updateWarmup } = useWorkoutStore();
  const [warmupData, setWarmupData] = useState(() => {
    if (!workout.warmup) {
      return { wrists: false, shoulders: false, elbows: false, back: false, legs: false };
    }
    // Only extract the warmup fields we need, ignore other API fields
    return {
      wrists: workout.warmup.wrists === true,
      shoulders: workout.warmup.shoulders === true,
      elbows: workout.warmup.elbows === true,
      back: workout.warmup.back === true,
      legs: workout.warmup.legs === true,
    };
  });
  const [isExpanded, setIsExpanded] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const completedCount = Object.values(warmupData).filter(Boolean).length;
  const isAllCompleted = completedCount === WARMUP_ITEMS.length;

  const handleToggle = async (key) => {
    const newData = { ...warmupData, [key]: !warmupData[key] };
    setWarmupData(newData);

    // Auto-save
    setIsSaving(true);
    await updateWarmup(newData);
    setIsSaving(false);
  };

  return (
    <div className="bg-slate-800 rounded-2xl p-4 border border-slate-700">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={`w-full flex items-center justify-between p-2 rounded-lg transition-colors ${
          isAllCompleted
            ? 'bg-green-500/20'
            : 'hover:bg-slate-700/50'
        }`}
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">🔥</span>
          <div className="text-left">
            <h3 className="font-bold text-white">Warmup Checklist</h3>
            <p className="text-slate-400 text-sm">
              {completedCount} of {WARMUP_ITEMS.length} completed
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isAllCompleted && (
            <span className="text-green-400 font-bold text-lg">✓</span>
          )}
          <span className="text-slate-400">
            {isExpanded ? '▼' : '▶'}
          </span>
        </div>
      </button>

      {/* Checklist Items (Expanded) */}
      {isExpanded && (
        <div className="mt-4 space-y-2">
          {WARMUP_ITEMS.map((item) => (
            <button
              key={item.key}
              onClick={() => handleToggle(item.key)}
              disabled={isSaving}
              className={`w-full p-3 rounded-lg font-semibold transition-all text-left flex items-center gap-3 ${
                warmupData[item.key]
                  ? 'bg-green-500/20 text-green-300 border border-green-500/30'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              } disabled:opacity-50`}
            >
              <span className="text-xl">{item.emoji}</span>
              <span className="flex-1">{item.label}</span>
              {warmupData[item.key] && (
                <span className="text-lg">✓</span>
              )}
            </button>
          ))}

          {/* Warmup Tips */}
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 mt-4">
            <p className="text-blue-300 text-xs font-semibold mb-2">💡 Tips</p>
            <ul className="text-blue-200 text-xs space-y-1">
              <li>• 10-15 rotations per direction</li>
              <li>• Keep movements smooth and controlled</li>
              <li>• Light cardiovascular activity (2-3 min)</li>
            </ul>
          </div>
        </div>
      )}

      {/* Progress Bar */}
      {!isExpanded && (
        <div className="mt-3 w-full bg-slate-700 rounded-full h-2 overflow-hidden">
          <div
            className="bg-gradient-to-r from-blue-500 to-green-500 h-full transition-all duration-300"
            style={{
              width: `${(completedCount / WARMUP_ITEMS.length) * 100}%`,
            }}
          />
        </div>
      )}
    </div>
  );
}
