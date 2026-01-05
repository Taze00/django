/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,jsx}'
  ],
  theme: {
    extend: {
      colors: {
        primary: '#3b82f6',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
        bg: {
          dark: '#0f172a',
          card: '#1e293b',
          hover: '#334155',
        },
        text: {
          primary: '#f1f5f9',
          secondary: '#94a3b8',
        },
        border: '#334155'
      }
    }
  },
  darkMode: 'class',
  plugins: []
}
