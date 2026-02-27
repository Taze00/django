import React, { Suspense, lazy, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Login } from './components/Auth/Login';
import { ProtectedRoute } from './components/Auth/ProtectedRoute';
import { useAuth } from './hooks/useAuth';
import MainLayout from './components/Layout/MainLayout';
import OfflineIndicator from './components/Layout/OfflineIndicator';
import WorkoutView from './components/Workout/WorkoutView';

// Lazy load profile view for code splitting
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

// Error boundary
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-slate-900 p-4">
          <div className="bg-red-500/10 border border-red-500 p-6 rounded-lg max-w-md">
            <h2 className="text-red-400 font-bold mb-2">App Error</h2>
            <p className="text-red-300 text-sm mb-4">{this.state.error?.message}</p>
            <button
              onClick={() => window.location.reload()}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
            >
              Reload App
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export const App = () => {
  const { isAuthenticated } = useAuth();

  // Force Service Worker update check
  useEffect(() => {
    // Check if there's a new Service Worker available
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then(registration => {
        // Check for updates immediately
        registration.update().then(() => {
          // Listen for new Service Worker waiting
          registration.onupdatefound = () => {
            const newWorker = registration.installing;
            newWorker.onstatechange = () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // New Service Worker is ready - reload the page
                console.log('[App] New Service Worker available, reloading...');
                window.location.reload();
              }
            };
          };
        }).catch(err => {
          console.error('[App] Service Worker update check failed:', err);
        });
      }).catch(err => {
        console.error('[App] Service Worker ready check failed:', err);
      });
    }
  }, []);

  return (
    <ErrorBoundary>
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
    </ErrorBoundary>
  );
};
