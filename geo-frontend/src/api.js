const BASE_URL = '/geo/api'

function getToken() {
  return localStorage.getItem('access_token')
}

async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })

  if (res.status === 401) {
    const refresh = localStorage.getItem('refresh_token')
    if (refresh) {
      const r = await fetch('/api/token/refresh/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      })
      if (r.ok) {
        const data = await r.json()
        localStorage.setItem('access_token', data.access)
        headers['Authorization'] = `Bearer ${data.access}`
        return fetch(`${BASE_URL}${path}`, { ...options, headers })
      }
    }
    // Refresh failed or no token — clear storage and redirect to login
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    window.location.href = '/geo/'
    return res
  }
  return res
}

export const api = {
  getContinents: () => apiFetch('/continents/'),
  getContinent: (slug) => apiFetch(`/continents/${slug}/`),
  getCourses: (continentSlug) => apiFetch(`/continents/${continentSlug}/courses/`),
  getCountry: (slug) => apiFetch(`/countries/${slug}/`),
  getCountryCourses: (slug) => apiFetch(`/countries/${slug}/courses/`),
  getCourseAllClues: (courseId) => apiFetch(`/practice/course/${courseId}/all/`),
  getPracticeClue: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return apiFetch(`/practice/${qs ? '?' + qs : ''}`)
  },
  getPracticeCourseClue: (courseId) => apiFetch(`/practice/course/${courseId}/`),
  saveProgress: (clueId, known) => apiFetch('/progress/', {
    method: 'POST',
    body: JSON.stringify({ clue: clueId, known }),
  }),
  getProgress: () => apiFetch('/progress/'),
  getAllCourses: () => apiFetch('/courses/'),
  getCourseProgress: (courseId) => apiFetch(`/course-progress/${courseId}/`),
  saveCourseCardProgress: (courseId, countryId, stage, streak, learned) => apiFetch(`/course-progress/${courseId}/`, {
    method: 'POST',
    body: JSON.stringify({ country_id: countryId, stage, streak, learned }),
  }),
  search: (q) => apiFetch(`/search/?q=${encodeURIComponent(q)}`),
  searchDomain: (q) => apiFetch(`/domain-search/?q=${encodeURIComponent(q)}`),
}
