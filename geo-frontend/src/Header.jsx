import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LangToggle, useLang } from './LanguageContext'
import { api } from './api'

function flagUrl(val) {
  if (!val) return null
  if (val.codePointAt(0) >= 0x1F1E0) {
    const iso = [...val].map(c => String.fromCharCode(c.codePointAt(0) - 0x1F1E6 + 65)).join('').toLowerCase()
    return 'https://flagcdn.com/w80/' + iso + '.png'
  }
  return 'https://flagcdn.com/w80/' + val.toLowerCase() + '.png'
}

function SearchBar() {
  const { lang } = useLang()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const debounceRef = useRef(null)
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

  useEffect(() => {
    function handle(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) setResults([])
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [])

  function handleSelect(country) {
    setQuery('')
    setResults([])
    navigate(`/${country.continent_slug}/${country.slug}`)
  }

  return (
    <div ref={containerRef} className="relative w-full sm:w-auto">
      <div className="relative">
        <svg xmlns="http://www.w3.org/2000/svg" className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
        </svg>
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Escape') { setQuery(''); setResults([]) }
            if (e.key === 'Enter' && results.length === 1) handleSelect(results[0])
          }}
          placeholder="Germany, .de…"
          autoComplete="off"
          className="w-full sm:w-56 lg:w-72 pl-8 pr-3 py-1.5 bg-gray-800 border border-gray-700 focus:border-blue-500 rounded-lg text-white placeholder-gray-600 focus:outline-none text-base sm:text-sm"
        />
        {loading && <div className="absolute right-3 top-1/2 -translate-y-1/2 w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />}
      </div>
      {results.length > 0 && (
        <div className="absolute left-0 top-full mt-1 w-72 bg-gray-800 border border-gray-700 rounded-xl shadow-xl z-50 overflow-hidden">
          {results.map(country => (
            <button key={country.slug} onMouseDown={() => handleSelect(country)} className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-gray-700 transition-colors text-left">
              <img src={flagUrl(country.flag_emoji)} alt={country.name} className="h-6 rounded shadow shrink-0" />
              <span className="flex-1 text-sm font-medium">{lang === 'de' && country.name_de ? country.name_de : country.name}</span>
              {country.domain && <span className="font-mono text-blue-400 text-xs shrink-0">{country.domain}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Header({ onLogout }) {
  return (
    <header className="sticky top-0 z-50 w-full bg-gray-950/90 backdrop-blur border-b border-gray-800">
      <div className="max-w-6xl mx-auto px-4 sm:px-8 h-14 flex items-center gap-3">
        <Link to="/" className="flex items-center gap-2 shrink-0">
          <img src="/static/geo/favicon.svg" alt="ClueLess" className="w-8 h-8 rounded-lg" />
          <span className="text-xl font-black tracking-tight">Clue<span className="text-teal-400">Less</span></span>
        </Link>

        <div className="flex-1 hidden sm:flex justify-center">
          <SearchBar />
        </div>

        <div className="flex items-center gap-2 shrink-0 ml-auto">
          <LangToggle />
          {onLogout && (
            <button
              onClick={onLogout}
              className="flex items-center justify-center text-gray-400 hover:text-white border border-gray-600 hover:border-gray-400 rounded-lg p-1.5 transition-all"
              title="Logout"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h6a2 2 0 012 2v1" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Mobile search row */}
      <div className="sm:hidden px-4 pb-2">
        <SearchBar />
      </div>
    </header>
  )
}
