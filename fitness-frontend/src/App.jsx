import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { useWorkoutStore } from './stores/workoutStore';
import LoginView from './views/LoginView';
import HomeView from './views/HomeView';
import WorkoutView from './views/WorkoutView';

function PrivateRoute({ children }) {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  return isAuthenticated ? children : <Navigate to="/login" />;
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
        <Route
          path="/"
          element={
            <PrivateRoute>
              <HomeView />
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
      </Routes>
    </Router>
  );
}

export default App;
