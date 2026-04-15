import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
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
        <svg xmlns="http://www.w3.org/2000/svg" className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5" style={{color:'var(--muted)'}} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
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
          placeholder={lang === 'en' ? 'Search countries…' : 'Länder suchen…'}
          autoComplete="off"
          className="w-full sm:w-64 lg:w-80 pl-9 pr-3 py-2 text-sm font-code"
          style={{
            background: 'transparent',
            borderBottom: '1px solid var(--line-strong)',
            borderTop: 'none', borderLeft: 'none', borderRight: 'none',
            color: 'var(--text)',
          }}
        />
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 w-3 h-3 border border-t-transparent rounded-full animate-spin" style={{borderColor:'var(--gold)'}} />
        )}
      </div>
      {results.length > 0 && (
        <div className="absolute left-0 top-full mt-1 w-80 border z-50 overflow-hidden"
          style={{background:'var(--ink-soft)', borderColor:'var(--line-strong)'}}>
          {results.map(country => (
            <button key={country.slug} onMouseDown={() => handleSelect(country)}
              className="w-full flex items-center gap-3 px-4 py-3 transition-colors text-left"
              onMouseEnter={e => e.currentTarget.style.background='var(--ink-raised)'}
              onMouseLeave={e => e.currentTarget.style.background=''}
            >
              <span className="shrink-0 flex items-center justify-center" style={{width:'28px', height:'20px'}}>
                <img src={flagUrl(country.flag_emoji)} alt={country.name} className="object-contain" style={{maxWidth:'28px', maxHeight:'20px'}} />
              </span>
              <span className="flex-1 text-sm" style={{color:'var(--text)'}}>{lang === 'de' && country.name_de ? country.name_de : country.name}</span>
              {country.domain && (
                <span className="font-code text-xs shrink-0" style={{color:'var(--gold)'}}>{country.domain}</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function CoursesDropdown({ lang }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  const location = useLocation()

  useEffect(() => { setOpen(false) }, [location.pathname])

  useEffect(() => {
    function handle(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [])

  const isActive = ['/courses', '/create-course', '/my-courses'].some(p => location.pathname.startsWith(p))

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-code transition-colors"
        style={{color: isActive ? 'var(--gold)' : 'var(--muted)'}}
        onMouseEnter={e => { if (!isActive) e.currentTarget.style.color = 'var(--text)' }}
        onMouseLeave={e => { if (!isActive) e.currentTarget.style.color = 'var(--muted)' }}
      >
        {lang === 'en' ? 'Courses' : 'Kurse'}
        <svg className="w-3 h-3 transition-transform duration-200" style={{transform: open ? 'rotate(180deg)' : ''}} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="absolute left-0 top-full mt-px w-56 z-50 overflow-hidden"
          style={{background:'var(--ink-soft)', border:'1px solid var(--line-strong)'}}>
          {[
            { to: '/courses', icon: '▶', label_de: 'Alle Kurse', label_en: 'All Courses' },
            { to: '/create-course', icon: '+', label_de: 'Kurs erstellen', label_en: 'Create Course' },
            { to: '/my-courses', icon: '★', label_de: 'Meine Kurse', label_en: 'My Courses' },
          ].map((item, i, arr) => {
            const isCurrent = location.pathname.startsWith(item.to)
            return (
              <Link key={item.to} to={item.to}
                className="flex items-center gap-3 px-4 py-3 text-sm font-code"
                style={{
                  color: isCurrent ? 'var(--gold)' : 'var(--muted)',
                  borderBottom: i < arr.length - 1 ? '1px solid var(--line)' : 'none',
                  borderLeft: `2px solid ${isCurrent ? 'var(--gold)' : 'transparent'}`,
                  background: isCurrent ? 'rgba(212,168,75,0.06)' : 'transparent',
                  transition: 'color 0.15s, border-left-color 0.15s, background 0.15s',
                }}
                onMouseEnter={e => {
                  if (!isCurrent) {
                    e.currentTarget.style.color = 'var(--text)'
                    e.currentTarget.style.borderLeftColor = 'var(--gold)'
                    e.currentTarget.style.background = 'rgba(212,168,75,0.06)'
                  }
                }}
                onMouseLeave={e => {
                  if (!isCurrent) {
                    e.currentTarget.style.color = 'var(--muted)'
                    e.currentTarget.style.borderLeftColor = 'transparent'
                    e.currentTarget.style.background = 'transparent'
                  }
                }}
              >
                <span className="shrink-0 w-3.5 text-center" style={{color:'var(--gold)'}}>{item.icon}</span>
                {lang === 'en' ? item.label_en : item.label_de}
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default function Header({ onLogout }) {
  const { lang } = useLang()
  const location = useLocation()

  return (
    <header className="sticky top-0 z-50 w-full cart-bg" style={{borderBottom:'1px solid var(--line)', background:'rgba(12,11,20,0.95)', backdropFilter:'blur(12px)'}}>
      <div className="max-w-7xl mx-auto px-5 sm:px-10 h-14 flex items-center gap-6">

        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 shrink-0">
          <div className="w-7 h-7 flex items-center justify-center border" style={{borderColor:'var(--line-strong)'}}>
            <svg viewBox="0 0 24 24" fill="none" className="w-4 h-4" style={{color:'var(--gold)'}}>
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M2 12h20M12 2a15 15 0 010 20M12 2a15 15 0 000 20" stroke="currentColor" strokeWidth="1.5"/>
            </svg>
          </div>
          <span className="font-display text-lg font-bold tracking-tight" style={{color:'var(--text)'}}>
            Clue<span style={{color:'var(--gold)'}}>Less</span>
          </span>
        </Link>

        {/* Nav */}
        <nav className="hidden md:flex items-center gap-1">
          <CoursesDropdown lang={lang} />
        </nav>

        {/* Search */}
        <div className="flex-1 hidden sm:flex justify-end">
          <SearchBar />
        </div>

        {/* Right */}
        <div className="flex items-center gap-2 shrink-0">
          <LangToggle />
          {onLogout && (
            <button
              onClick={onLogout}
              className="px-3 py-1.5 text-xs font-code uppercase tracking-widest transition-all border"
              style={{color:'var(--muted)', borderColor:'var(--line)', background:'transparent'}}
              onMouseEnter={e => { e.currentTarget.style.color='var(--text)'; e.currentTarget.style.borderColor='var(--line-strong)' }}
              onMouseLeave={e => { e.currentTarget.style.color='var(--muted)'; e.currentTarget.style.borderColor='var(--line)' }}
            >
              Exit
            </button>
          )}
        </div>
      </div>

      {/* Mobile search */}
      <div className="sm:hidden px-5 pb-2.5">
        <SearchBar />
      </div>
    </header>
  )
}
