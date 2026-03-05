/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'dark-bg': '#0f172a',
        'dark-secondary': '#1e293b',
        'dark-surface': '#334155',
      }
    },
  },
  plugins: [],
  darkMode: 'selector',
}
