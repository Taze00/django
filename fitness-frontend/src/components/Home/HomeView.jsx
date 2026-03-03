import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWorkoutStore } from '../../store/workoutStore';
import { useAuthStore } from '../../store/authStore';
import { WEEK_DAYS, isRestDay } from '../../constants/schedule';
import Header from '../Layout/Header';

export default function HomeView() {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const exercises = useWorkoutStore((state) => state.exercises);
  const userProgressions = useWorkoutStore((state) => state.userProgressions);
  const lastPerformances = useWorkoutStore((state) => state.lastPerformances);
  const initialize = useWorkoutStore((state) => state.initialize);
  const isLoading = useWorkoutStore((state) => state.isLoading);

  useEffect(() => {
    initialize();
  }, []);

  const userName = user?.first_name || user?.email?.split('@')[0] || 'Friend';

  const now = new Date();
  const todayDay = now.getDay() === 0 ? 7 : now.getDay();

  const getTodaysExercises = () => {
    if (isRestDay(todayDay)) return [];
    return (exercises || []).filter(e => e.name === 'Push-up' || e.name === 'Pull-up');
  };

  const todaysExercises = getTodaysExercises();
  const isTodayRestDay = todaysExercises.length === 0;
  const estimatedMinutes = 25;

  // Get progress data - directly from userProgressions
  const getProgressData = () => {
    // Map exercise names to exercise IDs
    const exerciseIds = {
      'Push-up': 1,
      'Pull-up': 2,
    };

    return Object.entries(exerciseIds).map(([name, id]) => {
      const prog = userProgressions?.[String(id)];
      if (!prog) return null;

      const details = prog.current_progression_details;
      return {
        name,
        level: details?.level || 1,
        sessions: prog.sessions_at_target || 0,
        sessionsRequired: details?.sessions_required || 3,
      };
    }).filter(Boolean);
  };

  // Get personal records (best performance values)
  const getPersonalRecords = () => {
    const records = {};
    
    Object.values(lastPerformances || {}).forEach(perf => {
      const exerciseId = perf.exercise_id;
      const exerciseName = exercises?.find(e => e.id === exerciseId)?.name;
      
      if (!exerciseName) return;
      
      if (!records[exerciseName]) {
        records[exerciseName] = perf;
      } else {
        // Keep the higher value
        if (perf.last_reps && (!records[exerciseName].last_reps || perf.last_reps > records[exerciseName].last_reps)) {
          records[exerciseName].last_reps = perf.last_reps;
        }
        if (perf.last_seconds && (!records[exerciseName].last_seconds || perf.last_seconds > records[exerciseName].last_seconds)) {
          records[exerciseName].last_seconds = perf.last_seconds;
        }
      }
    });

    return Object.entries(records).map(([name, rec]) => {
      const value = rec.last_reps ? `${rec.last_reps} reps` : `${rec.last_seconds}s`;
      return { name, value };
    });
  };

  // Wait for progressions to be loaded before rendering
  if (isLoading || Object.keys(userProgressions || {}).length === 0) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center pb-24">
        <div className="text-center">
          <div className="text-white mb-2">Loading your progress...</div>
          <div className="animate-pulse text-slate-400">⏳</div>
        </div>
      </div>
    );
  }

  const progressData = getProgressData();
  const personalRecords = getPersonalRecords();

  return (
    <div className="min-h-screen bg-slate-900 pb-24">
      <Header title={`Hi, ${userName}!`} icon="🏠" />

      <div className="p-4 space-y-4">
        {/* Date Info */}
        <p className="text-slate-400 text-xs">
          {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
        </p>

        {/* This Week */}
        <div className="bg-slate-800 rounded-xl p-3 border border-slate-700">
          <h2 className="text-xs font-bold text-slate-300 mb-2 uppercase">This Week</h2>
          <div className="flex gap-1">
            {WEEK_DAYS.map((d) => (
              <div
                key={d.number}
                className={`flex flex-col items-center p-1 rounded-lg flex-1 transition-all text-xs ${
                  d.number === todayDay
                    ? 'bg-blue-500/30 border border-blue-500/50'
                    : 'bg-slate-700/30 border border-slate-700/30'
                }`}
              >
                <span className="text-slate-300 mb-0.5 font-semibold text-xs">{d.day}</span>
                <span className="text-sm">{d.hasWorkout ? '💪' : '😎'}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Rest Day or Today's Workout */}
        {isTodayRestDay ? (
          <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 text-center">
            <p className="text-2xl mb-2">😎</p>
            <h3 className="text-base font-bold text-white mb-1">Rest Day!</h3>
            <p className="text-slate-300 text-xs">Recover & recharge</p>
          </div>
        ) : (
          <div className="bg-slate-800 rounded-xl p-3 border border-slate-700">
            <h2 className="text-xs font-bold text-slate-300 mb-2 uppercase">Today's Workout</h2>
            <div className="space-y-2 mb-3">
              {todaysExercises.map((exercise) => {
                const userProg = userProgressions?.[String(exercise.id)];
                const progression = userProg?.current_progression_details;
                return (
                  <div key={exercise.id} className="bg-slate-700/30 border border-slate-600/30 rounded-lg p-2">
                    <p className="font-semibold text-white text-xs">{exercise.name}</p>
                    <p className="text-slate-400 text-xs">Level {progression?.level || '?'} • {progression?.name || 'N/A'}</p>
                  </div>
                );
              })}
            </div>
            <div className="flex gap-2 mb-3 text-xs">
              <div className="flex-1 text-center">
                <p className="text-slate-400 font-semibold">SETS</p>
                <p className="text-white font-bold">6</p>
              </div>
              <div className="flex-1 text-center">
                <p className="text-slate-400 font-semibold">TIME</p>
                <p className="text-white font-bold">~{estimatedMinutes}m</p>
              </div>
            </div>
            <button
              onClick={() => navigate('/workout')}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-4 rounded-lg transition-all text-sm"
            >
              ▶ Start Workout
            </button>
          </div>
        )}

        {/* Progress Tracking */}
        <div className="grid grid-cols-2 gap-3">
          {progressData.map((prog) => (
            <div key={prog.name} className="bg-slate-800 rounded-xl p-3 border border-slate-700">
              <p className="text-xs text-slate-400 font-semibold mb-1">{prog.name}</p>
              <p className="text-lg font-bold text-white">Level {prog.level}</p>
            </div>
          ))}
        </div>

        {/* Personal Records */}
        {personalRecords.length > 0 && (
          <div className="bg-slate-800 rounded-xl p-3 border border-slate-700">
            <h2 className="text-xs font-bold text-slate-300 mb-2 uppercase">Personal Records</h2>
            <div className="space-y-2">
              {personalRecords.map((record) => (
                <div key={record.name} className="flex justify-between items-center bg-slate-700/30 p-2 rounded-lg">
                  <span className="text-xs text-slate-300 font-semibold">{record.name}</span>
                  <span className="text-xs text-blue-400 font-bold">{record.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
