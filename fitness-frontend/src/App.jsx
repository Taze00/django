import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import { Login } from './components/Auth/Login';
import { ProtectedRoute } from './components/Auth/ProtectedRoute';
import { useAuth } from './hooks/useAuth';
import MainLayout from './components/Layout/MainLayout';
import OfflineIndicator from './components/Layout/OfflineIndicator';
import WorkoutView from './components/Workout/WorkoutView';

// Lazy load stats and profile views for code splitting
const StatsView = lazy(() => import('./components/Stats/StatsView'));
const ProfileView = lazy(() => import('./components/Profile/ProfileView'));

// Simple loading component
const LoadingScreen = () => (
  <div className="flex items-center justify-center min-h-screen bg-slate-900">
    <div className="text-center">
      <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
      <p className="text-slate-300">Lade...</p>
    </div>
  </div>
);

export const App = () => {
  const { isAuthenticated } = useAuth();

  return (
    <Router basename="/fitness">
      <OfflineIndicator />
      <Routes>
        {/* Auth Routes */}
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to="/" /> : <Login />}
        />

        {/* Protected Routes with MainLayout */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout>
                <WorkoutView />
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/stats"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Suspense fallback={<LoadingScreen />}>
                  <StatsView />
                </Suspense>
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Suspense fallback={<LoadingScreen />}>
                  <ProfileView />
                </Suspense>
              </MainLayout>
            </ProtectedRoute>
          }
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
};
