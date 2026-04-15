import { useEffect, useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useLang } from '../LanguageContext'
import Header from '../Header'

const QUIZ_TYPES = ['flags', 'domains', 'capitals']

const TYPE_META = {
  flags: {
    color: '#d4a84b',
    label_de: 'Flaggen', label_en: 'Flags',
    hint_de: 'Länder an ihrer Nationalflagge erkennen',
    hint_en: 'Recognize countries by their flag',
    glyph: '⚑',
  },
  domains: {
    color: '#7c9fc4',
    label_de: 'Domains', label_en: 'Domains',
    hint_de: 'Länder an ihrer Google-Domain erkennen',
    hint_en: 'Recognize countries by Google domain',
    glyph: '.cc',
  },
  capitals: {
    color: '#5a9e6f',
    label_de: 'Hauptstädte', label_en: 'Capitals',
    hint_de: 'Länder ihrer Hauptstadt zuordnen',
    hint_en: 'Match countries with their capital',
    glyph: '★',
  },
  clues: {
    color: '#c8863c',
    label_de: 'Clue-Kurse', label_en: 'Clue Courses',
    hint_de: 'Foto-basierte Kurse mit visuellen Hinweisen',
    hint_en: 'Photo-based courses with visual clues',
    glyph: '◈',
  },
}

const ALL_SECTIONS = ['flags', 'domains', 'capitals', 'clues']

function getFavs() {
  try { return new Set(JSON.parse(localStorage.getItem('geo_fav_courses') || '[]')) } catch { return new Set() }
}
function saveFavs(set) {
  localStorage.setItem('geo_fav_courses', JSON.stringify([...set]))
}
function progressStatus(learned, total) {
  if (total === 0) return 'notStarted'
  if (learned >= total) return 'done'
  if (learned > 0) return 'inProgress'
  return 'notStarted'
}
function extractCreator(description) {
  const match = (description || '').match(/Created by ([^\n\r]+)/)
  return match ? match[1].trim() : null
}

function Bar({ pct, color }) {
  return (
    <div className="relative h-px w-full" style={{background:'var(--line-strong)'}}>
      <div style={{
        position:'absolute', top:0, left:0, bottom:0,
        width:`${pct}%`,
        background: pct === 100 ? '#5a9e6f' : color,
        transition:'width 0.6s cubic-bezier(0.16,1,0.3,1)',
      }} />
    </div>
  )
}

function QuizCard({ course, meta, lang }) {
  const learned = course.learned_count ?? 0
  const total = course.total_count ?? course.country_count ?? 0
  const pct = total > 0 ? Math.round((learned / total) * 100) : 0
  const done = pct === 100 && total > 0
  const name = course.continent_name
    ? (lang === 'de' && course.continent_name_de ? course.continent_name_de : course.continent_name)
    : (lang === 'en' ? 'General' : 'Allgemein')

  return (
    <Link
      to={`/practice/course/${course.id}`}
      className="group flex flex-col gap-3 p-4 relative overflow-hidden"
      style={{background:'var(--ink-soft)', border:'1px solid var(--line)'}}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = meta.color + '55'
        e.currentTarget.style.background = 'var(--ink-raised)'
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = 'var(--line)'
        e.currentTarget.style.background = 'var(--ink-soft)'
      }}
    >
      <div className="absolute top-0 left-0 w-full h-0.5 scale-x-0 origin-left group-hover:scale-x-100 transition-transform duration-300"
        style={{background: meta.color}} />
      <div className="flex items-center justify-between">
        <span className="font-display font-bold text-sm" style={{color: done ? '#5a9e6f' : 'var(--text)'}}>{name}</span>
        {done
          ? <span className="font-code text-xs" style={{color:'#5a9e6f'}}>✓</span>
          : pct > 0 ? <span className="font-code text-xs tabular-nums" style={{color: meta.color}}>{pct}%</span>
          : <span className="font-code text-xs" style={{color:'var(--line-strong)'}}>—</span>}
      </div>
      <Bar pct={pct} color={meta.color} />
      <span className="font-code text-xs" style={{color:'var(--muted)'}}>{learned}/{total} {lang === 'en' ? 'countries' : 'Länder'}</span>
    </Link>
  )
}

function ClueCard({ course, lang, isFav, onToggleFav }) {
  const learned = course.learned_count ?? 0
  const total = course.total_count ?? 0
  const pct = total > 0 ? Math.round((learned / total) * 100) : 0
  const done = pct === 100 && total > 0
  const creator = extractCreator(course.description)
  const meta = TYPE_META.clues
  const contName = lang === 'de' && course.continent_name_de
    ? course.continent_name_de
    : (course.continent_name || (lang === 'en' ? 'General' : 'Allgemein'))

  return (
    <Link
      to={`/practice/course/${course.id}`}
      className="group flex flex-col gap-3 p-4 relative overflow-hidden"
      style={{background:'var(--ink-soft)', border:'1px solid var(--line)'}}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = (done ? '#5a9e6f' : meta.color) + '55'
        e.currentTarget.style.background = 'var(--ink-raised)'
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = 'var(--line)'
        e.currentTarget.style.background = 'var(--ink-soft)'
      }}
    >
      <div className="absolute top-0 left-0 w-full h-0.5 scale-x-0 origin-left group-hover:scale-x-100 transition-transform duration-300"
        style={{background: done ? '#5a9e6f' : meta.color}} />
      <div className="flex items-start gap-2">
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm leading-snug truncate" style={{color:'var(--text)'}}>{course.name}</div>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className="font-code text-xs" style={{color:'var(--muted)'}}>{contName}</span>
            {creator && <span className="font-code text-xs" style={{color:'var(--line-strong)'}}>· {creator}</span>}
          </div>
        </div>
        <button
          onClick={e => { e.preventDefault(); e.stopPropagation(); onToggleFav() }}
          className="p-0.5 shrink-0 transition-colors"
          style={{color: isFav ? 'var(--gold)' : 'var(--line-strong)'}}
          onMouseEnter={e => { if (!isFav) e.currentTarget.style.color='var(--gold)' }}
          onMouseLeave={e => { if (!isFav) e.currentTarget.style.color='var(--line-strong)' }}
        >
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill={isFav ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
          </svg>
        </button>
      </div>
      <Bar pct={pct} color={meta.color} />
      <div className="flex items-center justify-between">
        <span className="font-code text-xs" style={{color:'var(--muted)'}}>{total} {lang === 'en' ? 'clues' : 'Clues'}</span>
        {done
          ? <span className="font-code text-xs" style={{color:'#5a9e6f'}}>✓</span>
          : pct > 0 ? <span className="font-code text-xs tabular-nums" style={{color: meta.color}}>{pct}%</span>
          : null}
      </div>
    </Link>
  )
}

export default function CoursesView({ onLogout }) {
  const { lang } = useLang()
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [active, setActive] = useState('flags')
  const [favs, setFavs] = useState(getFavs)
  const [searchQ, setSearchQ] = useState('')
  const [filterContinent, setFilterContinent] = useState('')
  const [filterProgress, setFilterProgress] = useState('all')

  useEffect(() => {
    api.getAllCourses()
      .then(r => r.json())
      .then(data => { const list = data.results ?? data; setCourses(Array.isArray(list) ? list : []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  function toggleFav(id) {
    setFavs(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      saveFavs(next)
      return next
    })
  }

  const quizCourses = useMemo(() => courses.filter(c => QUIZ_TYPES.includes(c.course_type)), [courses])
  const clueCourses = useMemo(() => courses.filter(c => c.course_type === 'clues'), [courses])

  const continents = useMemo(() => {
    const seen = new Map()
    for (const c of clueCourses) {
      if (c.continent_name && !seen.has(c.continent_name)) {
        seen.set(c.continent_name, lang === 'de' && c.continent_name_de ? c.continent_name_de : c.continent_name)
      }
    }
    return [...seen.entries()].sort((a, b) => a[1].localeCompare(b[1]))
  }, [clueCourses, lang])

  const filteredClues = useMemo(() => {
    let list = clueCourses
    if (searchQ.trim()) list = list.filter(c => c.name.toLowerCase().includes(searchQ.toLowerCase()))
    if (filterContinent === '__general__') list = list.filter(c => !c.continent_name)
    else if (filterContinent) list = list.filter(c => c.continent_name === filterContinent)
    if (filterProgress !== 'all') list = list.filter(c => progressStatus(c.learned_count ?? 0, c.total_count ?? 0) === filterProgress)
    return list
  }, [clueCourses, searchQ, filterContinent, filterProgress])

  const hasActiveFilters = searchQ.trim() || filterContinent || filterProgress !== 'all'

  const quizCount = useMemo(() => {
    const map = {}
    for (const t of QUIZ_TYPES) map[t] = quizCourses.filter(c => c.course_type === t).length
    return map
  }, [quizCourses])

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen cart-bg" style={{background:'var(--ink)'}}>
      <div className="w-8 h-8 border-t border-r rounded-full animate-spin" style={{borderColor:'var(--gold)'}} />
    </div>
  )

  const activeMeta = TYPE_META[active]
  const activeQuizCourses = quizCourses.filter(c => c.course_type === active)

  const selectStyle = {
    background: 'var(--ink)', border: '1px solid var(--line-strong)',
    color: 'var(--text)', padding: '8px 12px', fontSize: '13px',
    fontFamily: "'DM Mono', monospace", outline: 'none',
  }

  return (
    <div className="min-h-screen cart-bg" style={{background:'var(--ink)'}}>
      <Header onLogout={onLogout} />

      {/* Slim top bar */}
      <div style={{borderBottom:'1px solid var(--line)'}}>
        <div className="max-w-7xl mx-auto px-5 sm:px-10 py-6 flex items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="h-px w-6" style={{background:'var(--gold)'}} />
            <h1 className="font-display text-2xl font-black" style={{color:'var(--text)'}}>
              {lang === 'en' ? 'Courses' : 'Kurse'}
            </h1>
          </div>
          <div className="flex gap-2">
            <Link to="/create-course"
              className="px-3.5 py-1.5 font-code text-xs uppercase tracking-widest border transition-all"
              style={{borderColor:'var(--line-strong)', color:'var(--muted)', background:'transparent'}}
              onMouseEnter={e => { e.currentTarget.style.borderColor='var(--gold)'; e.currentTarget.style.color='var(--gold)' }}
              onMouseLeave={e => { e.currentTarget.style.borderColor='var(--line-strong)'; e.currentTarget.style.color='var(--muted)' }}
            >
              + {lang === 'en' ? 'New' : 'Neu'}
            </Link>
            <Link to="/my-courses"
              className="px-3.5 py-1.5 font-code text-xs uppercase tracking-widest border transition-all"
              style={{borderColor:'var(--line-strong)', color:'var(--muted)', background:'transparent'}}
              onMouseEnter={e => { e.currentTarget.style.borderColor='var(--gold)'; e.currentTarget.style.color='var(--gold)' }}
              onMouseLeave={e => { e.currentTarget.style.borderColor='var(--line-strong)'; e.currentTarget.style.color='var(--muted)' }}
            >
              ★ {lang === 'en' ? 'Mine' : 'Meine'}
            </Link>
          </div>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="max-w-7xl mx-auto px-5 sm:px-10">
        <div className="flex" style={{minHeight:'calc(100vh - 120px)'}}>

          {/* Sidebar */}
          <aside className="hidden md:flex flex-col w-56 shrink-0 py-10 pr-8"
            style={{borderRight:'1px solid var(--line)'}}>
            <span className="font-code text-xs uppercase tracking-widest mb-4" style={{color:'var(--muted)'}}>
              {lang === 'en' ? 'Category' : 'Kategorie'}
            </span>
            <nav className="flex flex-col">
              {ALL_SECTIONS.map((type, i) => {
                const meta = TYPE_META[type]
                const label = lang === 'en' ? meta.label_en : meta.label_de
                const isActive = active === type
                const count = type === 'clues' ? clueCourses.length : (quizCount[type] ?? 0)
                return (
                  <button
                    key={type}
                    onClick={() => setActive(type)}
                    className="group relative flex items-center justify-between py-3.5 px-0 text-left transition-all duration-150"
                    style={{
                      borderTop: i > 0 ? '1px solid var(--line)' : 'none',
                      color: isActive ? meta.color : 'var(--muted)',
                    }}
                    onMouseEnter={e => { if (!isActive) e.currentTarget.style.color = 'var(--text)' }}
                    onMouseLeave={e => { if (!isActive) e.currentTarget.style.color = 'var(--muted)' }}
                  >
                    {isActive && (
                      <div className="absolute -right-8 top-1/2 -translate-y-1/2 w-1 h-6"
                        style={{background: meta.color}} />
                    )}
                    <div className="flex items-center gap-3">
                      <span className="font-code text-base w-6 text-center shrink-0"
                        style={{color: isActive ? meta.color : 'var(--line-strong)'}}>
                        {meta.glyph}
                      </span>
                      <span className="font-semibold text-sm">{label}</span>
                    </div>
                    {count > 0 && (
                      <span className="font-code text-xs tabular-nums"
                        style={{color: isActive ? meta.color : 'var(--line-strong)'}}>
                        {count}
                      </span>
                    )}
                  </button>
                )
              })}
            </nav>
            <div className="mt-auto pt-8" style={{borderTop:'1px solid var(--line)'}}>
              <Link to="/create-course"
                className="flex items-center gap-2 py-2 font-code text-xs transition-colors"
                style={{color:'var(--muted)'}}
                onMouseEnter={e => e.currentTarget.style.color='var(--gold)'}
                onMouseLeave={e => e.currentTarget.style.color='var(--muted)'}
              >
                <span style={{color:'var(--line-strong)'}}>+</span>
                {lang === 'en' ? 'Create course' : 'Kurs erstellen'}
              </Link>
              <Link to="/my-courses"
                className="flex items-center gap-2 py-2 font-code text-xs transition-colors"
                style={{color:'var(--muted)'}}
                onMouseEnter={e => e.currentTarget.style.color='var(--gold)'}
                onMouseLeave={e => e.currentTarget.style.color='var(--muted)'}
              >
                <span style={{color:'var(--line-strong)'}}>★</span>
                {lang === 'en' ? 'My courses' : 'Meine Kurse'}
              </Link>
            </div>
          </aside>

          {/* Content panel */}
          <main className="flex-1 py-10 md:pl-10 min-w-0">
            {/* Section header */}
            <div className="mb-8">
              <div className="flex items-end gap-4 justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-code text-lg" style={{color: activeMeta.color}}>{activeMeta.glyph}</span>
                    <h2 className="font-display text-3xl font-black" style={{color:'var(--text)'}}>
                      {lang === 'en' ? activeMeta.label_en : activeMeta.label_de}
                    </h2>
                  </div>
                  <p className="font-code text-xs" style={{color:'var(--muted)'}}>
                    {lang === 'en' ? activeMeta.hint_en : activeMeta.hint_de}
                  </p>
                </div>
                {/* Mobile: icon row */}
                <div className="flex md:hidden gap-1">
                  {ALL_SECTIONS.map(type => (
                    <button key={type}
                      onClick={() => setActive(type)}
                      className="w-8 h-8 font-code text-xs flex items-center justify-center border transition-all"
                      style={{
                        borderColor: active === type ? TYPE_META[type].color : 'var(--line)',
                        color: active === type ? TYPE_META[type].color : 'var(--muted)',
                        background: active === type ? 'var(--ink-raised)' : 'transparent',
                      }}
                    >
                      {TYPE_META[type].glyph}
                    </button>
                  ))}
                </div>
              </div>
              <div className="h-px mt-6" style={{background:`linear-gradient(to right, ${activeMeta.color}88, transparent)`}} />
            </div>

            {/* Quiz grid */}
            {active !== 'clues' && (
              activeQuizCourses.length === 0 ? (
                <div className="py-24 text-center font-code text-xs" style={{color:'var(--muted)'}}>
                  — {lang === 'en' ? 'no courses yet' : 'noch keine Kurse'} —
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {activeQuizCourses.map(course => (
                    <QuizCard key={course.id} course={course} meta={activeMeta} lang={lang} />
                  ))}
                </div>
              )
            )}

            {/* Clue courses */}
            {active === 'clues' && (
              <>
                <div className="flex flex-wrap gap-2 mb-6 items-center">
                  <div className="relative flex-1 min-w-40">
                    <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-3 h-3" style={{color:'var(--muted)'}} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
                    </svg>
                    <input
                      style={{...selectStyle, paddingLeft:'30px', width:'100%'}}
                      placeholder={lang === 'en' ? 'Search…' : 'Suchen…'}
                      value={searchQ}
                      onChange={e => setSearchQ(e.target.value)}
                    />
                  </div>
                  <select style={{...selectStyle, flex:'0 0 auto'}} value={filterContinent} onChange={e => setFilterContinent(e.target.value)}>
                    <option value="">{lang === 'en' ? 'All regions' : 'Alle Regionen'}</option>
                    <option value="__general__">{lang === 'en' ? 'General' : 'Allgemein'}</option>
                    {continents.map(([key, name]) => <option key={key} value={key}>{name}</option>)}
                  </select>
                  <select style={{...selectStyle, flex:'0 0 auto'}} value={filterProgress} onChange={e => setFilterProgress(e.target.value)}>
                    <option value="all">{lang === 'en' ? 'All' : 'Alle'}</option>
                    <option value="notStarted">{lang === 'en' ? 'Not started' : 'Neu'}</option>
                    <option value="inProgress">{lang === 'en' ? 'In progress' : 'Laufend'}</option>
                    <option value="done">{lang === 'en' ? 'Done' : 'Fertig'}</option>
                  </select>
                  <div className="flex items-center gap-3 ml-auto shrink-0">
                    <span className="font-code text-xs" style={{color:'var(--muted)'}}>
                      {filteredClues.length === clueCourses.length
                        ? `${clueCourses.length}`
                        : `${filteredClues.length} / ${clueCourses.length}`}
                    </span>
                    {hasActiveFilters && (
                      <button
                        onClick={() => { setSearchQ(''); setFilterContinent(''); setFilterProgress('all') }}
                        className="font-code text-xs underline underline-offset-2 transition-colors"
                        style={{color:'var(--muted)'}}
                        onMouseEnter={e => e.currentTarget.style.color='var(--text)'}
                        onMouseLeave={e => e.currentTarget.style.color='var(--muted)'}
                      >
                        {lang === 'en' ? 'Clear' : 'Reset'}
                      </button>
                    )}
                  </div>
                </div>
                {filteredClues.length === 0 ? (
                  <div className="py-24 text-center font-code text-xs" style={{color:'var(--muted)'}}>
                    — {lang === 'en' ? 'no results' : 'keine Ergebnisse'} —
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {filteredClues.map(course => (
                      <ClueCard key={course.id} course={course} lang={lang}
                        isFav={favs.has(course.id)} onToggleFav={() => toggleFav(course.id)} />
                    ))}
                  </div>
                )}
              </>
            )}
          </main>
        </div>
      </div>
    </div>
  )
}
