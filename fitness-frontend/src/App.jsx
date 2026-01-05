import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Login } from './components/Auth/Login';
import { ProtectedRoute } from './components/Auth/ProtectedRoute';
import { useAuth } from './hooks/useAuth';
import MainLayout from './components/Layout/MainLayout';
import OfflineIndicator from './components/Layout/OfflineIndicator';
import WorkoutView from './components/Workout/WorkoutView';
import StatsView from './components/Stats/StatsView';
import ProfileView from './components/Profile/ProfileView';

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
                <StatsView />
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <MainLayout>
                <ProfileView />
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
