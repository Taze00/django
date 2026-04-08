import { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import HomeView from './views/HomeView'
import ContinentView from './views/ContinentView'
import CountryView from './views/CountryView'
import PracticeView from './views/PracticeView'
import CoursePracticeView from './views/CoursePracticeView'
import LoginView from './views/LoginView'

function useAuth() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('access_token'))

  function login(access, refresh) {
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
    setIsLoggedIn(true)
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setIsLoggedIn(false)
  }

  return { isLoggedIn, login, logout }
}

function ProtectedRoute({ isLoggedIn, children }) {
  if (!isLoggedIn) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  const { isLoggedIn, login, logout } = useAuth()

  return (
    <BrowserRouter basename="/geo">
      <Routes>
        <Route path="/login" element={
          isLoggedIn ? <Navigate to="/" replace /> : <LoginView onLogin={login} />
        } />
        <Route path="/" element={
          <ProtectedRoute isLoggedIn={isLoggedIn}>
            <HomeView onLogout={logout} />
          </ProtectedRoute>
        } />
        <Route path="/practice" element={
          <ProtectedRoute isLoggedIn={isLoggedIn}><PracticeView /></ProtectedRoute>
        } />
        <Route path="/practice/course/:courseId" element={
          <ProtectedRoute isLoggedIn={isLoggedIn}><CoursePracticeView /></ProtectedRoute>
        } />
        <Route path="/:continentSlug" element={
          <ProtectedRoute isLoggedIn={isLoggedIn}><ContinentView /></ProtectedRoute>
        } />
        <Route path="/:continentSlug/:countrySlug" element={
          <ProtectedRoute isLoggedIn={isLoggedIn}><CountryView /></ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  )
}
