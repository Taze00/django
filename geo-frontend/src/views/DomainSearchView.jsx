import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useLang } from '../LanguageContext'

function flagUrl(val) {
  if (!val) return null
  if (val.codePointAt(0) >= 0x1F1E0) {
    const iso = [...val].map(c => String.fromCharCode(c.codePointAt(0) - 0x1F1E6 + 65)).join('').toLowerCase()
    return 'https://flagcdn.com/w80/' + iso + '.png'
  }
  return 'https://flagcdn.com/w80/' + val.toLowerCase() + '.png'
}

export default function SearchView() {
  const { t } = useLang()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const debounceRef = useRef(null)

  useEffect(() => {
    if (!query.trim()) {
      setResults(null)
      return
    }
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        const res = await api.search(query.trim())
        const data = await res.json()
        setResults(data)
      } catch {
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 250)
    return () => clearTimeout(debounceRef.current)
  }, [query])

  function handleKeyDown(e) {
    if (e.key === 'Enter' && results && results.length === 1) {
      navigate(`/${results[0].continent_slug ?? ''}/${results[0].slug}`.replace('//', '/'))
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-2xl mx-auto px-4 py-12">
        <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-gray-300 hover:text-white border border-gray-600 hover:border-gray-400 rounded-lg px-3 py-1.5 mb-8 transition-all min-w-[5rem]">
          <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg>
          {t.back}
        </Link>

        <h1 className="text-3xl font-bold mb-2">Search</h1>
        <p className="text-gray-400 text-sm mb-8">Search by country name or domain – e.g. <span className="font-mono text-blue-400">Germany</span>, <span className="font-mono text-blue-400">de</span>, <span className="font-mono text-blue-400">.co.uk</span></p>

        <div className="relative mb-6">
          <svg xmlns="http://www.w3.org/2000/svg" className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
          </svg>
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Germany, .de, co.uk…"
            autoFocus
            autoComplete="off"
            className="w-full pl-11 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:border-blue-500"
          />
          {loading && (
            <div className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          )}
        </div>

        {results !== null && (
          results.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              No results for <span className="font-mono text-gray-400">"{query}"</span>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {results.map(country => (
                <Link
                  key={country.slug}
                  to={`/${country.slug}`}
                  className="flex items-center gap-4 bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-blue-500 rounded-xl p-4 transition-all"
                >
                  <img src={flagUrl(country.flag_emoji)} alt={country.name} className="h-10 rounded shadow shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold">{country.name}</div>
                    <div className="text-xs text-gray-400">{country.clue_count} clues</div>
                  </div>
                  {country.domain && (
                    <span className="font-mono text-blue-400 text-sm shrink-0">google{country.domain}</span>
                  )}
                </Link>
              ))}
            </div>
          )
        )}
      </div>
    </div>
  )
}
