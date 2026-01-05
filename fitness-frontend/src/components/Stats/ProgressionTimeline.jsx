import { useEffect } from 'react';
import { useStatsStore } from '../../store/statsStore';

export default function ProgressionTimeline({ exerciseId }) {
  const { progressionHistory, fetchProgressionHistory, isLoading } = useStatsStore();

  useEffect(() => {
    if (exerciseId) {
      fetchProgressionHistory(exerciseId);
    }
  }, [exerciseId, fetchProgressionHistory]);

  if (isLoading) {
    return (
      <div className="bg-slate-800 rounded-2xl p-4 mx-4 mb-4 border border-slate-700">
        <p className="text-slate-400 text-center">Loading...</p>
      </div>
    );
  }

  if (!progressionHistory || !progressionHistory.progressions || progressionHistory.progressions.length === 0) {
    return (
      <div className="bg-slate-800 rounded-2xl p-4 mx-4 mb-4 border border-slate-700">
        <p className="text-slate-400 text-center">No progression history yet</p>
      </div>
    );
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: '2-digit',
    });
  };

  return (
    <div className="bg-slate-800 rounded-2xl p-4 mx-4 mb-20 border border-slate-700">
      <h3 className="text-white font-bold mb-4">🎯 Progression History</h3>
      <div className="space-y-4">
        {progressionHistory.progressions.map((prog, idx) => (
          <div key={idx} className="flex items-start gap-3 pb-4 border-b border-slate-700 last:border-b-0">
            <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-300 font-bold text-sm flex-shrink-0">
              {prog.level}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2 mb-1">
                <p className="text-white font-semibold truncate">
                  {prog.progression_name}
                </p>
                {!prog.ended_at && (
                  <span className="text-green-400 text-sm font-semibold flex-shrink-0">
                    ✓ Current
                  </span>
                )}
              </div>
              <p className="text-slate-400 text-xs">
                {formatDate(prog.started_at)}
                {prog.ended_at && ` - ${formatDate(prog.ended_at)}`}
              </p>
              <p className="text-slate-500 text-xs mt-1">
                {prog.total_workouts} workout{prog.total_workouts !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
