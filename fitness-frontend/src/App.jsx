import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { useWorkoutStore } from './stores/workoutStore';
import BottomNav from './components/BottomNav';
import IosInstallHint from './components/IosInstallHint';
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

// Wie lange die Auth-Pruefung laufen darf, bevor ueberhaupt etwas
// angezeigt wird. Sie ist in der Regel in deutlich unter 100ms durch
// (ein GET /user/ gegen den eigenen Server) - ein sofort gezeigter
// Ladeschirm waere dann nur ein Aufblitzen. Lieber kurz nichts.
const LADESCHIRM_VERZOEGERUNG_MS = 400;

function AuthPruefungLaeuft() {
  const [sichtbar, setSichtbar] = useState(false);

  useEffect(() => {
    const uhr = setTimeout(() => setSichtbar(true), LADESCHIRM_VERZOEGERUNG_MS);
    return () => clearTimeout(uhr);
  }, []);

  if (!sichtbar) return null;

  // Derselbe Ladeschirm wie in HomeView/WorkoutView, ohne Textzeile -
  // hier steht noch nicht fest, worauf gewartet wird.
  return (
    <div className="loading-shell">
      <div className="loading-logo">COR<span>VIS</span></div>
      <div className="loading-spinner" />
    </div>
  );
}

function PrivateRoute({ children }) {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  const authChecked = useAuthStore(state => state.authChecked);

  // Drei Zustaende, nicht zwei. Solange die Pruefung laeuft, wird weder
  // das Ziel gezeigt noch weitergeleitet.
  //
  // Vorher entschied diese Stelle allein an `isAuthenticated`, das auf
  // false startet - der erste Render warf damit JEDEN Reload auf
  // /login, bevor checkAuth() den Token ueberhaupt gesehen hatte. Und
  // LoginView holt einen nicht zurueck, es navigiert nur nach einem
  // abgeschickten Formular. Bei der installierten PWA traf das jeden
  // Kaltstart, weil start_url genau /corvis-app/ ist.
  if (!authChecked) return <AuthPruefungLaeuft />;

  // `replace`, damit die Weiterleitung keinen Eintrag in der History
  // hinterlaesst - sonst landet man mit "Zurueck" wieder auf der
  // geschuetzten Route und wird erneut umgeleitet.
  return isAuthenticated ? children : <Navigate to="/login" replace />;
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
    <Router basename="/corvis-app">
      <IosInstallHint />
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
