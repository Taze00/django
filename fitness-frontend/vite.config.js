import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/static/fitness/',
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Calisthenics Tracker',
        short_name: 'Fitness',
        description: 'Track your calisthenics workouts with progressive overload',
        theme_color: '#0f172a',
        background_color: '#0f172a',
        display: 'standalone',
        scope: '/fitness/',
        start_url: '/fitness/',
        icons: [
          {
            src: '/static/fitness/icons/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/static/fitness/icons/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      },
      workbox: {
        runtimeCaching: [
          // Fonts - cache with long expiration
          {
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365
              }
            }
          },
          // Avatars - NetworkFirst to always get fresh avatar images
          {
            urlPattern: /\/media\/avatars\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'avatar-cache-v3',
              expiration: {
                maxEntries: 20,
                maxAgeSeconds: 60 * 60 * 24 * 30
              },
              networkTimeoutSeconds: 2
            }
          },
          // User Profile - NetworkFirst for always fresh user data
          {
            urlPattern: /\/api\/fitness\/user\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'user-cache-v3',
              expiration: {
                maxEntries: 5,
                maxAgeSeconds: 60 * 5
              },
              networkTimeoutSeconds: 3
            }
          },
          // Other API Calls - StaleWhileRevalidate for fresh data but offline support
          {
            urlPattern: /\/api\/fitness\/.*/i,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'api-cache-v3',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 * 7
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          }
        ]
      }
    })
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  }
})
