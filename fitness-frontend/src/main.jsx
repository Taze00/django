import React from 'react'
import ReactDOM from 'react-dom/client'
import { App } from './App'
import './index.css'

// Register Service Worker for offline functionality
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/fitness/sw.js', {
      scope: '/fitness/'
    }).then(reg => {
      console.log('[SW] Registered successfully with scope:', reg.scope);
    }).catch(err => {
      console.error('[SW] Registration failed:', err);
    });
  });
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
