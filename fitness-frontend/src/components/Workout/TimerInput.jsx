import { useState, useEffect } from 'react';
import { useWorkoutStore } from '../../store/workoutStore';

export default function TimerInput({
  exercise,
  setNumber,
  userProgression,
  existingSet,
  onCompleted,
  isDropSet = false,
}) {
  const lastPerformances = useWorkoutStore((state) => state.lastPerformances);
  const addSet = useWorkoutStore((state) => state.addSet);
  const [phase, setPhase] = useState('ready');
  const [countdownValue, setCountdownValue] = useState(3);
  const [seconds, setSeconds] = useState(existingSet?.seconds || 0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [intervalId, setIntervalId] = useState(null);
  const [editSeconds, setEditSeconds] = useState(null); // For manual time entry

  const [dropSetProgressionId, setDropSetProgressionId] = useState(
    existingSet?.drop_set_progression || userProgression?.current_progression || null
  );

  const currentProgression = Array.isArray(exercise?.progressions)
    ? exercise.progressions.find(
        (p) => p?.id === userProgression?.current_progression
      )
    : null;

  const availableProgressions = currentProgression
    ? (exercise?.progressions || []).filter(
        (p) => p?.level < currentProgression.level
      )
    : [];

  // Get last performance for this progression
  // currentProgression.id is a number, but lastPerformances keys are strings
  const lastPerf = currentProgression ? lastPerformances?.[String(currentProgression.id)] : null;

  useEffect(() => {
    if (phase === 'countdown') {
      if (countdownValue > 0) {
        const timer = setTimeout(() => {
          setCountdownValue(countdownValue - 1);
        }, 1000);
        return () => clearTimeout(timer);
      } else {
        setPhase('timing');
      }
    }
  }, [phase, countdownValue]);

  useEffect(() => {
    if (phase === 'timing') {
      const interval = setInterval(() => {
        setSeconds((s) => s + 1);
      }, 1000);
      setIntervalId(interval);
      return () => clearInterval(interval);
    }
  }, [phase]);

  useEffect(() => {
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [intervalId]);

  const handleStart = () => {
    setPhase('countdown');
    setCountdownValue(3);
  };

  const handleStop = () => {
    if (intervalId) clearInterval(intervalId);
    setPhase('stopped');
  };

  const handleSave = async () => {
    if (seconds === 0) {
      setError('Bitte halte mindestens 1 Sekunde');
      return;
    }

    if (!userProgression) {
      setError('Progression-Daten nicht geladen - bitte aktualisiere die Seite');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const progressionId = isDropSet ? dropSetProgressionId : userProgression.current_progression;

      if (!progressionId) {
        setError('Progression nicht gefunden - bitte aktualisiere die Seite');
        return;
      }

      const result = await addSet(
        exercise.id,
        progressionId,
        null,
        setNumber,
        isDropSet,
        seconds
      );

      if (result) {
        onCompleted(setNumber, { isUpdate: !!existingSet, seconds: seconds });
      } else {
        setError('Fehler beim Speichern - bitte versuche es erneut');
      }
    } catch (err) {
      console.error('Error saving set:', err);
      setError('Fehler beim Speichern - bitte überprüfe deine Verbindung');
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (totalSeconds) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-4">
      {/* Last Time Info */}
      {lastPerf && !isDropSet && (
        <div className="bg-slate-700/30 border border-slate-600/30 rounded-lg p-3">
          <p className="text-slate-400 text-xs font-semibold mb-1">LAST TIME</p>
          <p className="text-white text-lg font-bold">{formatTime(lastPerf.last_seconds)}</p>
        </div>
      )}
      {!lastPerf && !isDropSet && (
        <div className="bg-slate-700/30 border border-slate-600/30 rounded-lg p-3">
          <p className="text-slate-400 text-xs font-semibold">FIRST TIME AT THIS LEVEL!</p>
        </div>
      )}

      {phase === 'countdown' && (
        <div className="text-center bg-slate-800/50 rounded-xl p-5 border border-slate-700 space-y-2">
          <div className="text-8xl font-bold text-blue-400 animate-pulse font-mono">
            {countdownValue}
          </div>
          <p className="text-slate-400 text-xs">Bereite dich vor...</p>
        </div>
      )}

      {(phase === 'timing' || phase === 'stopped') && (
        <div className="text-center bg-slate-800/50 rounded-xl p-5 border border-slate-700 space-y-2">
          <p className="text-slate-400 text-xs uppercase">Zeit</p>
          <div className="text-6xl font-bold text-blue-400 font-mono">
            {formatTime(seconds)}
          </div>
        </div>
      )}

      {phase === 'ready' && (
        <button
          onClick={handleStart}
          disabled={isLoading}
          className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 disabled:from-slate-600 disabled:to-slate-700 text-white font-bold py-3 px-4 rounded-lg transition-all duration-200 active:scale-95"
        >
          Start Timer (3-2-1)
        </button>
      )}

      {(phase === 'countdown' || phase === 'timing') && (
        <div className="space-y-2">
          <button
            onClick={handleStop}
            className="w-full bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white font-bold py-3 px-4 rounded-lg transition-all duration-200 active:scale-95"
          >
            ✓ Stop & Save
          </button>
          <button
            onClick={() => {
              setPhase('ready');
              setSeconds(0);
              setCountdownValue(3);
            }}
            className="w-full bg-slate-600 hover:bg-slate-500 text-white font-bold py-2 px-4 rounded-lg transition-all text-sm"
          >
            ↻ Reset
          </button>
        </div>
      )}

      {phase === 'stopped' && !editSeconds && (
        <div className="space-y-2">
          <button
            onClick={() => setEditSeconds(seconds)}
            className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white font-bold py-3 px-4 rounded-lg transition-all duration-200 active:scale-95"
          >
            ✏️ Edit Time
          </button>
          <button
            onClick={() => {
              setPhase('ready');
              setSeconds(0);
              setCountdownValue(3);
            }}
            className="w-full bg-slate-600 hover:bg-slate-500 text-white font-bold py-2 px-4 rounded-lg transition-all"
          >
            ↻ Reset
          </button>
        </div>
      )}

      {phase === 'stopped' && editSeconds !== null && (
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-slate-300">Edit Time (seconds)</label>
          <div className="flex gap-2 items-center">
            <input
              type="number"
              min="1"
              value={editSeconds}
              onChange={(e) => setEditSeconds(Number(e.target.value))}
              className="flex-1 px-3 py-2 bg-slate-600 border border-slate-500 rounded-lg text-white text-center"
              disabled={isLoading}
            />
            <span className="text-slate-400 text-sm min-w-16">
              = {formatTime(editSeconds)}
            </span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setSeconds(editSeconds) || setEditSeconds(null)}
              className="flex-1 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white font-bold py-2 px-3 rounded-lg transition-all text-sm"
            >
              ✓ Accept
            </button>
            <button
              onClick={() => setEditSeconds(null)}
              className="flex-1 bg-slate-600 hover:bg-slate-500 text-white font-bold py-2 px-3 rounded-lg transition-all text-sm"
            >
              ✕ Cancel
            </button>
          </div>
        </div>
      )}

      {isDropSet && availableProgressions.length > 0 && (
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-slate-300">
            Drop Set Progression
          </label>
          <select
            value={dropSetProgressionId}
            onChange={(e) => setDropSetProgressionId(Number(e.target.value))}
            disabled={isLoading}
            className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded-lg text-white disabled:opacity-50"
          >
            {availableProgressions.map((prog) => (
              <option key={prog.id} value={prog.id}>
                {prog.name} (Level {prog.level})
              </option>
            ))}
          </select>
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-300 px-3 py-2 rounded-lg text-sm">
          {error}
        </div>
      )}

      {phase === 'stopped' && (
        <button
          onClick={handleSave}
          disabled={isLoading || seconds === 0}
          className="w-full bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 disabled:from-slate-600 disabled:to-slate-700 text-white font-bold py-3 px-4 rounded-lg transition-all duration-200 active:scale-95"
        >
          {isLoading ? (
            <span className="flex items-center justify-center">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></span>
              Speichern...
            </span>
          ) : existingSet?.seconds ? (
            `✓ Update Set ${setNumber}`
          ) : (
            `✓ Save Set ${setNumber}`
          )}
        </button>
      )}
    </div>
  );
}
