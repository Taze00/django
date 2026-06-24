import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { initServiceWorker } from './utils/notify'

// Minimalen Service Worker registrieren (nur Benachrichtigungen, kein Prompt).
// Die Permission-Abfrage passiert separat per Tap (Profil).
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => { initServiceWorker() })
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
