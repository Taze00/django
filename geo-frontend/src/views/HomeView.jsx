import { useEffect, useState, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useLang, LangToggle } from '../LanguageContext'

function flagUrl(val) {
  if (!val) return null
  if (val.codePointAt(0) >= 0x1F1E0) {
    const iso = [...val].map(c => String.fromCharCode(c.codePointAt(0) - 0x1F1E6 + 65)).join('').toLowerCase()
    return 'https://flagcdn.com/w80/' + iso + '.png'
  }
  return 'https://flagcdn.com/w80/' + val.toLowerCase() + '.png'
}

function SearchBar() {
  const { t, lang } = useLang()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const debounceRef = useRef(null)
  const inputRef = useRef(null)
  const containerRef = useRef(null)

  useEffect(() => {
    if (!query.trim()) { setResults([]); return }
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        const res = await api.search(query.trim())
        const data = await res.json()
        setResults(data)
      } catch { setResults([]) }
      finally { setLoading(false) }
    }, 200)
    return () => clearTimeout(debounceRef.current)
  }, [query])

  // Close dropdown on outside click
  useEffect(() => {
    function handle(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setResults([])
      }
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [])

  function handleSelect(country) {
    setQuery('')
    setResults([])
    navigate(`/${country.continent_slug}/${country.slug}`)
  }

  function handleKeyDown(e) {
    if (e.key === 'Escape') { setQuery(''); setResults([]) }
    if (e.key === 'Enter' && results.length === 1) handleSelect(results[0])
  }

  return (
    <div ref={containerRef} className="relative">
      <div className="relative hidden sm:block">
        <svg xmlns="http://www.w3.org/2000/svg" className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
        </svg>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Germany, .de…"
          autoComplete="off"
          className="w-56 lg:w-72 pl-8 pr-3 py-1.5 bg-gray-800 border border-gray-700 focus:border-blue-500 rounded-lg text-sm text-white placeholder-gray-600 focus:outline-none"
        />
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
        )}
      </div>

      {results.length > 0 && (
        <div className="absolute left-0 top-full mt-1 w-72 bg-gray-800 border border-gray-700 rounded-xl shadow-xl z-50 overflow-hidden">
          {results.map(country => (
            <button
              key={country.slug}
              onMouseDown={() => handleSelect(country)}
              className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-gray-700 transition-colors text-left"
            >
              <img src={flagUrl(country.flag_emoji)} alt={country.name} className="h-6 rounded shadow shrink-0" />
              <span className="flex-1 text-sm font-medium">{lang === 'de' && country.name_de ? country.name_de : country.name}</span>
              {country.domain && (
                <span className="font-mono text-blue-400 text-xs shrink-0">{country.domain}</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default function HomeView({ onLogout }) {
  const { t, lang } = useLang()
  const [continents, setContinents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getContinents()
      .then(r => r.json())
      .then(data => { const list = data.results ?? data; setContinents(Array.isArray(list) ? list : []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950">
      <div className="text-blue-400 text-lg">{t.loading}</div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-950 text-white">

      {/* ── Top Navigation Bar ── */}
      <header className="sticky top-0 z-50 w-full bg-gray-950/90 backdrop-blur border-b border-gray-800">
        <div className="max-w-6xl mx-auto px-4 sm:px-8 h-16 flex items-center gap-4">

          {/* Logo */}
          <div className="flex items-center gap-3 shrink-0">
            <img src="/static/geo/favicon.svg" alt="ClueLess" className="w-10 h-10 rounded-xl" />
            <span className="text-2xl font-black tracking-tight">Clue<span className="text-teal-400">Less</span></span>
          </div>

          {/* Search — grows in middle */}
          <div className="flex-1 flex justify-center">
            <SearchBar />
          </div>

          {/* Right: Lang + Logout */}
          <div className="flex items-center gap-2 shrink-0">
            <LangToggle />
            <button
              onClick={onLogout}
              className="hidden sm:flex items-center gap-1.5 text-xs text-gray-400 hover:text-white border border-gray-600 hover:border-gray-400 rounded-lg px-3 py-1.5 transition-all"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h6a2 2 0 012 2v1" />
              </svg>
              {t.logout}
            </button>
            <button
              onClick={onLogout}
              className="sm:hidden flex items-center justify-center text-gray-400 hover:text-white border border-gray-600 hover:border-gray-400 rounded-lg p-1.5 transition-all"
              title={t.logout}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h6a2 2 0 012 2v1" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 sm:px-8 py-10">

        <div className="mb-10 bg-gray-900 border border-gray-800 rounded-2xl p-8 flex flex-col sm:flex-row items-center gap-6">
          <div className="flex-1">
            <h2 className="text-2xl font-bold mb-2">{t.learnTitle}</h2>
            <p className="text-gray-400 text-sm">{t.learnSubtitle}</p>
          </div>
          <Link
            to="/courses"
            className="shrink-0 px-8 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-semibold transition-colors min-w-[11rem] text-center"
          >
            {t.selectCourse}
          </Link>
        </div>

        {continents.length === 0 ? (
          <div className="text-gray-500 text-center py-20">
            {t.noContinents}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {continents.map(continent => (
              <Link
                key={continent.slug}
                to={`/${continent.slug}`}
                className="group relative rounded-xl overflow-hidden bg-gray-800 hover:bg-gray-700 transition-all border border-gray-700 hover:border-blue-500"
              >
                {continent.cover_image ? (
                  <img
                    src={continent.cover_image}
                    alt={continent.name}
                    className="w-full h-40 object-contain opacity-60 group-hover:opacity-80 transition-opacity"
                  />
                ) : (
                  <div className="w-full h-40 bg-gradient-to-br from-blue-900 to-gray-800 flex items-center justify-center">
                    <span className="text-5xl">🌐</span>
                  </div>
                )}
                <div className="p-4">
                  <h2 className="text-xl font-bold mb-1">{lang === 'de' && continent.name_de ? continent.name_de : continent.name}</h2>
                  <div className="flex items-center gap-3 text-sm text-gray-500 mt-2">
                    <span>{continent.country_count} {t.countries}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
