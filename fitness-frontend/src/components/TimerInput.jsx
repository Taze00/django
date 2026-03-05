import { useState, useEffect } from 'react';

export default function TimerInput({ setNumber, exerciseName, progressionName, targetSeconds, lastTime, onComplete }) {
  const [seconds, setSeconds] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      setSeconds(s => s + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [isRunning]);

  const handleSubmit = async () => {
    setIsRunning(false);
    setIsSubmitting(true);
    try {
      await onComplete(seconds);
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatTime = (s) => {
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-slate-100 mb-2">
          {exerciseName}
        </h2>
        <p className="text-slate-300 text-lg">{progressionName}</p>
        <p className="text-slate-400 text-sm mt-2">
          Set {setNumber} of 3
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {targetSeconds && (
          <div className="bg-slate-700 rounded-lg p-4 text-center">
            <p className="text-slate-400 text-xs">Target</p>
            <p className="text-slate-100 text-xl font-bold">{targetSeconds}s</p>
          </div>
        )}
        {lastTime && (
          <div className="bg-slate-700 rounded-lg p-4 text-center">
            <p className="text-slate-400 text-xs">Last time</p>
            <p className="text-slate-100 text-xl font-bold">{formatTime(lastTime)}s</p>
          </div>
        )}
      </div>

      <div className="bg-slate-800 border-2 border-slate-700 rounded-lg p-8">
        <div className="text-center mb-8">
          <p className="text-slate-400 text-sm mb-4">Time held</p>
          <p className="text-7xl font-bold text-slate-100 font-mono">{formatTime(seconds)}</p>
        </div>

        <div className="flex gap-4 justify-center mb-6">
          <button
            onClick={() => {
              setIsRunning(!isRunning);
            }}
            className={`flex-1 py-4 font-bold rounded-lg text-lg ${
              isRunning
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            {isRunning ? 'Stop' : 'Start'}
          </button>
          <button
            onClick={() => setSeconds(0)}
            className="flex-1 py-4 bg-slate-700 hover:bg-slate-600 text-white font-bold rounded-lg text-lg"
          >
            Reset
          </button>
        </div>

        <button
          onClick={handleSubmit}
          disabled={isSubmitting || seconds === 0}
          className="w-full py-4 bg-emerald-500 hover:bg-emerald-600 disabled:bg-gray-600 text-white font-bold rounded-lg text-lg"
        >
          {isSubmitting ? 'Saving...' : `Complete Set ${setNumber}`}
        </button>
      </div>
    </div>
  );
}
