import { useEffect } from 'react';
import { useAuthStore } from '../stores/authStore';
import { useWorkoutStore } from '../stores/workoutStore';

export default function HomeView() {
  const user = useAuthStore(state => state.user);
  const logout = useAuthStore(state => state.logout);
  const exercises = useWorkoutStore(state => state.exercises);
  const userProgressions = useWorkoutStore(state => state.userProgressions);
  const isLoading = useWorkoutStore(state => state.isLoading);

  useEffect(() => {
    // Initialize on mount
  }, []);

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-slate-100">Fitness Tracker</h1>
          <div className="flex items-center gap-4">
            <span className="text-slate-300">{user?.username}</span>
            <button
              onClick={logout}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8 pb-20">
        {isLoading ? (
          <div className="text-center text-slate-300 py-12">
            Loading exercises...
          </div>
        ) : (
          <>
            <h2 className="text-xl font-semibold text-slate-100 mb-6">
              Your Progress
            </h2>
            
            <div className="grid gap-4">
              {exercises.map(exercise => {
                const prog = userProgressions[String(exercise.id)];
                return (
                  <div key={exercise.id} className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-slate-100 mb-2">
                      {exercise.name}
                    </h3>
                    {prog ? (
                      <p className="text-slate-300">
                        Current Level: <span className="text-slate-100 font-semibold">
                          {prog.current_progression.name}
                        </span>
                      </p>
                    ) : (
                      <p className="text-slate-400 text-sm">Loading...</p>
                    )}
                  </div>
                );
              })}
            </div>

            <button className="fixed bottom-6 left-1/2 transform -translate-x-1/2 w-11/12 max-w-sm py-4 bg-emerald-500 hover:bg-emerald-600 text-white font-bold rounded-lg text-lg">
              Start Workout
            </button>
          </>
        )}
      </main>
    </div>
  );
}
