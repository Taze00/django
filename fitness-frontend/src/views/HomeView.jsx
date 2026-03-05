import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useWorkoutStore } from '../stores/workoutStore';

export default function HomeView() {
  const navigate = useNavigate();
  const user = useAuthStore(state => state.user);
  const logout = useAuthStore(state => state.logout);
  const exercises = useWorkoutStore(state => state.exercises);
  const userProgressions = useWorkoutStore(state => state.userProgressions);
  const isLoading = useWorkoutStore(state => state.isLoading);

  const handleStartWorkout = () => {
    navigate('/workout');
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getExerciseEmoji = (name) => {
    return name.includes('Push') ? '📍' : '🔝';
  };

  const getProgressionColor = (index) => {
    const colors = [
      'from-slate-700 to-slate-800',
      'from-blue-700/40 to-blue-800/40',
    ];
    return colors[index % colors.length];
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-900 to-blue-900/20">
      {/* Animated background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl animate-pulse-soft"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl animate-pulse-soft" style={{ animationDelay: '1s' }}></div>
      </div>

      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-slate-800/30 border-b border-slate-700/30">
        <div className="max-w-2xl mx-auto px-4 py-5 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
              Calisthenics
            </h1>
            <p className="text-slate-400 text-xs mt-0.5">Level up your strength</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-semibold text-slate-100">{user?.username}</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors duration-200"
              title="Logout"
            >
              🚪
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative max-w-2xl mx-auto px-4 py-8 pb-32">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="text-center">
              <div className="text-4xl mb-4 animate-bounce">⏳</div>
              <p className="text-slate-400">Loading your workouts...</p>
            </div>
          </div>
        ) : (
          <>
            {/* Progress Section */}
            <div className="mb-8 animate-fade-in">
              <h2 className="text-3xl font-bold text-slate-100 mb-2">Today's Workout</h2>
              <p className="text-slate-400">Check your current levels</p>
            </div>

            {/* Exercise Cards */}
            <div className="space-y-4 mb-8 animate-fade-in" style={{ animationDelay: '0.1s' }}>
              {exercises.map((exercise, idx) => {
                const prog = userProgressions[String(exercise.id)];
                return (
                  <div
                    key={exercise.id}
                    className={`group bg-gradient-to-br ${getProgressionColor(idx)} border border-slate-600/30 rounded-2xl p-6 backdrop-blur-sm hover:border-slate-500/50 transition-all duration-300 hover:shadow-lg cursor-pointer transform hover:scale-105`}
                    style={{ animationDelay: `${0.2 + idx * 0.1}s` }}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-3xl">{getExerciseEmoji(exercise.name)}</span>
                          <div>
                            <h3 className="text-lg font-bold text-slate-100">
                              {exercise.name}
                            </h3>
                          </div>
                        </div>
                        {prog ? (
                          <div className="ml-12">
                            <p className="text-slate-400 text-sm mb-1">Current Level</p>
                            <p className="text-emerald-400 font-bold text-lg">
                              {prog.current_progression.name}
                            </p>
                            <p className="text-slate-500 text-xs mt-2">
                              Target: {prog.current_progression.target_value}
                              {prog.current_progression.target_type === 'reps' ? ' reps' : 's'}
                            </p>
                          </div>
                        ) : (
                          <p className="text-slate-500 text-sm ml-12">Loading...</p>
                        )}
                      </div>
                      <div className="text-2xl opacity-0 group-hover:opacity-100 transition-opacity">
                        →
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Motivational Section */}
            <div className="bg-gradient-to-r from-blue-600/20 to-emerald-600/20 border border-emerald-500/30 rounded-2xl p-6 mb-8 animate-slide-up text-center">
              <p className="text-slate-300 text-sm mb-2">Ready to push yourself?</p>
              <p className="text-slate-200 font-semibold">Every rep brings you closer to your goals</p>
            </div>
          </>
        )}
      </main>

      {/* Start Workout Button */}
      <button
        onClick={handleStartWorkout}
        className="fixed bottom-6 left-1/2 transform -translate-x-1/2 w-11/12 max-w-sm py-4 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-700 hover:to-emerald-600 text-white font-bold rounded-xl text-lg shadow-2xl hover:shadow-glow transition-all duration-300 transform hover:scale-105 active:scale-95 flex items-center justify-center gap-2 group"
      >
        <span className="text-2xl group-hover:animate-bounce">💪</span>
        Start Workout
      </button>
    </div>
  );
}
