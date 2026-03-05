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

  const handleStartWorkout = () => navigate('/workout');
  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-900 to-slate-800 relative">
      {/* Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/8 rounded-full blur-3xl animate-pulse-soft"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-emerald-500/8 rounded-full blur-3xl animate-pulse-soft" style={{ animationDelay: '2s' }}></div>
      </div>

      {/* Header */}
      <header className="sticky top-0 z-40 backdrop-blur-md bg-slate-900/80 border-b border-slate-700/30">
        <div className="max-w-4xl mx-auto px-6 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-black bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-transparent">
              Calisthenics
            </h1>
            <p className="text-slate-400 text-xs font-medium mt-0.5">Progressive Bodyweight Training</p>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm font-bold text-slate-100 px-4 py-2 bg-slate-800/50 rounded-lg">
              {user?.username}
            </span>
            <button
              onClick={handleLogout}
              className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors duration-200 text-slate-300 hover:text-slate-100"
              title="Logout"
            >
              🚪
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative max-w-4xl mx-auto px-6 py-12 pb-32">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="text-5xl mb-4 animate-bounce">⏳</div>
            <p className="text-slate-400 font-medium">Loading your workouts...</p>
          </div>
        ) : (
          <>
            {/* Welcome Section */}
            <div className="mb-12 animate-fade-in">
              <h2 className="text-4xl font-black text-slate-100 mb-2">Today's Workout</h2>
              <p className="text-slate-400 text-lg">Check your current progression levels</p>
            </div>

            {/* Exercise Cards Grid */}
            <div className="grid gap-6 mb-12 animate-fade-in" style={{ animationDelay: '0.2s' }}>
              {exercises.map((exercise, idx) => {
                const prog = userProgressions[String(exercise.id)];
                const isFirst = idx === 0;

                return (
                  <div
                    key={exercise.id}
                    className={`group relative overflow-hidden rounded-2xl border transition-all duration-300 hover:scale-102 cursor-pointer animate-slide-up`}
                    style={{ animationDelay: `${0.1 * (idx + 1)}s` }}
                  >
                    {/* Gradient Background */}
                    <div className={`absolute inset-0 bg-gradient-to-br ${
                      isFirst 
                        ? 'from-emerald-600/25 via-emerald-700/15 to-slate-900/10' 
                        : 'from-blue-600/25 via-blue-700/15 to-slate-900/10'
                    }`}></div>

                    {/* Border */}
                    <div className={`absolute inset-0 border rounded-2xl ${
                      isFirst
                        ? 'border-emerald-500/30'
                        : 'border-blue-500/30'
                    }`}></div>

                    {/* Content */}
                    <div className="relative p-6 flex items-center gap-6">
                      <div className={`flex-shrink-0 w-16 h-16 rounded-xl flex items-center justify-center text-3xl font-bold ${
                        isFirst
                          ? 'bg-gradient-to-br from-emerald-500 to-emerald-600'
                          : 'bg-gradient-to-br from-blue-500 to-blue-600'
                      }`}>
                        {isFirst ? '💪' : '🔥'}
                      </div>

                      <div className="flex-1">
                        <h3 className="text-xl font-bold text-slate-100 mb-1">
                          {exercise.name}
                        </h3>
                        {prog ? (
                          <>
                            <p className="text-slate-400 text-sm mb-2">Current Level</p>
                            <p className={`font-bold text-lg ${
                              isFirst ? 'text-emerald-400' : 'text-blue-400'
                            }`}>
                              {prog.current_progression.name}
                            </p>
                            <p className="text-slate-500 text-xs mt-2 font-medium">
                              Target: {prog.current_progression.target_value}
                              {prog.current_progression.target_type === 'reps' ? ' reps' : 's'}
                            </p>
                          </>
                        ) : (
                          <p className="text-slate-500 text-sm">Loading...</p>
                        )}
                      </div>

                      <div className="text-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                        →
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Motivational Banner */}
            <div className="bg-gradient-to-r from-emerald-600/20 to-blue-600/20 border border-emerald-500/30 rounded-2xl p-8 text-center mb-8 animate-slide-up" style={{ animationDelay: '0.5s' }}>
              <h3 className="text-2xl font-bold text-slate-100 mb-2">Ready to push?</h3>
              <p className="text-slate-300 font-medium">Every set brings you closer to your goals</p>
            </div>
          </>
        )}
      </main>

      {/* Start Workout Button */}
      <button
        onClick={handleStartWorkout}
        className="fixed bottom-8 left-1/2 transform -translate-x-1/2 w-11/12 max-w-sm py-4 px-8 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-700 hover:to-emerald-600 text-white font-bold rounded-2xl text-lg shadow-2xl hover:shadow-glow transition-all duration-300 transform hover:scale-105 active:scale-95 flex items-center justify-center gap-3 group z-30"
      >
        <span className="text-2xl group-hover:scale-125 transition-transform duration-300">💪</span>
        <span>Start Workout</span>
      </button>
    </div>
  );
}
