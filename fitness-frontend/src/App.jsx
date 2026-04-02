import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { useWorkoutStore } from './stores/workoutStore';
import BottomNav from './components/BottomNav';
import LoginView from './views/LoginView';
import RegisterView from './views/RegisterView';
import OnboardingView from './views/OnboardingView';
import HomeView from './views/HomeView';
import WorkoutView from './views/WorkoutView';
import ExercisesView from './views/ExercisesView';
import StatisticsView from './views/StatisticsView';
import ProfileView from './views/ProfileView';
import TrainingDaysView from './views/TrainingDaysView';
import SetProgressionView from './views/SetProgressionView';

function PrivateRoute({ children }) {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  return isAuthenticated ? children : <Navigate to="/login" />;
}

function PrivateLayout({ children }) {
  const location = useLocation();
  const isWorkout = location.pathname === '/workout';
  
  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <div style={{ flex: 1 }}>
        {children}
      </div>
      {!isWorkout && <BottomNav />}
    </div>
  );
}

function App() {
  const checkAuth = useAuthStore(state => state.checkAuth);
  const initialize = useWorkoutStore(state => state.initialize);
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (isAuthenticated) {
      initialize();
    }
  }, [isAuthenticated, initialize]);

  return (
    <Router basename="/fitness">
      <Routes>
        <Route path="/login" element={<LoginView />} />
        <Route path="/register" element={<RegisterView />} />
        <Route path="/onboarding" element={<OnboardingView />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <PrivateLayout>
                <HomeView />
              </PrivateLayout>
            </PrivateRoute>
          }
        />
        <Route
          path="/workout"
          element={
            <PrivateRoute>
              <WorkoutView />
            </PrivateRoute>
          }
        />
        <Route
          path="/exercises"
          element={
            <PrivateRoute>
              <PrivateLayout>
                <ExercisesView />
              </PrivateLayout>
            </PrivateRoute>
          }
        />
        <Route
          path="/statistics"
          element={
            <PrivateRoute>
              <PrivateLayout>
                <StatisticsView />
              </PrivateLayout>
            </PrivateRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <PrivateRoute>
              <PrivateLayout>
                <ProfileView />
              </PrivateLayout>
            </PrivateRoute>
          }
        />
        <Route
          path="/training-days"
          element={
            <PrivateRoute>
              <PrivateLayout>
                <TrainingDaysView />
              </PrivateLayout>
            </PrivateRoute>
          }
        />
        <Route
          path="/set-progression"
          element={
            <PrivateRoute>
              <PrivateLayout>
                <SetProgressionView />
              </PrivateLayout>
            </PrivateRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
