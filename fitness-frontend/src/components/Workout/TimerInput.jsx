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
  const { addSet } = useWorkoutStore();
  const [phase, setPhase] = useState('ready'); // 'ready' | 'countdown' | 'timing' | 'stopped'
  const [countdownValue, setCountdownValue] = useState(3);
  const [seconds, setSeconds] = useState(existingSet?.seconds || 0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [intervalId, setIntervalId] = useState(null);

  // For drop sets, we might use a different progression
  const [dropSetProgressionId, setDropSetProgressionId] = useState(
    existingSet?.drop_set_progression || userProgression?.current_progression || null
  );

  const currentProgression = Array.isArray(exercise?.progressions)
    ? exercise.progressions.find(
        (p) => p?.id === userProgression?.current_progression
      )
    : null;

  // Get available progressions for drop set
  const availableProgressions = currentProgression
    ? (exercise?.progressions || []).filter(
        (p) => p?.level < currentProgression.level
      )
    : [];

  // Countdown effect
  useEffect(() => {
    if (phase === 'countdown') {
      if (countdownValue > 0) {
        const timer = setTimeout(() => {
          setCountdownValue(countdownValue - 1);
        }, 1000);
        return () => clearTimeout(timer);
      } else {
        // Countdown finished, auto-start timing
        setPhase('timing');
      }
    }
  }, [phase, countdownValue]);

  // Timing effect
  useEffect(() => {
    if (phase === 'timing') {
      const interval = setInterval(() => {
        setSeconds((s) => s + 1);
      }, 1000);
      setIntervalId(interval);
      return () => clearInterval(interval);
    }
  }, [phase]);

  // Cleanup on unmount
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
        null, // reps = null for timed exercises
        setNumber,
        isDropSet,
        seconds // pass seconds instead
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

  const targetSeconds = currentProgression?.target_seconds || 30;

  const formatTime = (totalSeconds) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-4">
      {/* Target Info Box */}
      {currentProgression && (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 flex items-center justify-between">
          <div>
            <p className="text-blue-300 text-xs font-semibold uppercase">Target Zeit</p>
            <p className="text-white font-bold text-sm mt-0.5">
              {targetSeconds} Sekunden
            </p>
          </div>
          <div className="text-right">
            <p className="text-slate-400 text-xs">Aktuell:</p>
            <p className={`text-lg font-bold ${seconds >= targetSeconds ? 'text-green-400' : 'text-slate-300'}`}>
              {formatTime(seconds)}
            </p>
          </div>
        </div>
      )}

      {/* Countdown Display */}
      {phase === 'countdown' && (
        <div className="text-center bg-slate-800/50 rounded-xl p-8 border border-slate-700 space-y-4">
          <div className="text-9xl font-bold text-blue-400 animate-pulse font-mono">
            {countdownValue}
          </div>
          <p className="text-slate-400 text-sm">Bereite dich vor...</p>
        </div>
      )}

      {/* Timer Display */}
      {(phase === 'timing' || phase === 'stopped') && (
        <div className="text-center bg-slate-800/50 rounded-xl p-8 border border-slate-700 space-y-4">
          <p className="text-slate-400 text-xs uppercase mb-2">Zeit</p>
          <div className="text-7xl font-bold text-blue-400 font-mono">
            {formatTime(seconds)}
          </div>
          <p className="text-slate-400 text-xs mt-2">Sekunden</p>
          {seconds >= targetSeconds && (
            <p className="text-green-400 text-xs font-bold mt-1">✓ Target erreicht!</p>
          )}
        </div>
      )}

      {/* Ready State - Show Start Button */}
      {phase === 'ready' && (
        <button
          onClick={handleStart}
          disabled={isLoading}
          className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 disabled:from-slate-600 disabled:to-slate-700 text-white font-bold py-3 px-4 rounded-lg transition-all duration-200 active:scale-95"
        >
          Start Timer (3-2-1)
        </button>
      )}

      {/* Countdown/Timing State - Show Stop Button */}
      {(phase === 'countdown' || phase === 'timing') && (
        <button
          onClick={handleStop}
          className="w-full bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white font-bold py-3 px-4 rounded-lg transition-all duration-200 active:scale-95"
        >
          ⏹ Stop & Save
        </button>
      )}

      {/* Stopped State - Show Save Button */}
      {phase === 'stopped' && (
        <div className="space-y-2">
          <button
            onClick={() => setPhase('timing')}
            className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white font-bold py-3 px-4 rounded-lg transition-all duration-200 active:scale-95"
          >
            ▶ Resume Timer
          </button>
          <button
            onClick={() => setPhase('ready')}
            className="w-full bg-slate-600 hover:bg-slate-500 text-white font-bold py-2 px-4 rounded-lg transition-all"
          >
            ↻ Reset
          </button>
        </div>
      )}

      {/* Drop Set Progression Selector */}
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

      {/* Error Message */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-300 px-3 py-2 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Save Button */}
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
