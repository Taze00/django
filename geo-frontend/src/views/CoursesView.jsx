import { useEffect, useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useLang } from '../LanguageContext'
import Header from '../Header'

// ── constants ─────────────────────────────────────────────────────────────────

const QUIZ_TYPES = ['flags', 'domains', 'capitals']

const TYPE_META = {
  flags: {
    icon: '🏳️',
    color: 'text-amber-400',
    bg: 'bg-amber-400/10',
    activeBg: 'bg-gradient-to-br from-amber-500/20 to-amber-900/10',
    border: 'border-amber-400/40',
    activeBorder: 'border-amber-400/70',
    glow: 'shadow-amber-500/10',
    label_de: 'Flaggen', label_en: 'Flags',
    desc_de: 'Erkenne Länder anhand ihrer Nationalflagge',
    desc_en: 'Identify countries by their national flag',
    example: '🇩🇪 🇫🇷 🇯🇵 🇧🇷',
  },
  domains: {
    icon: '🌐',
    color: 'text-blue-400',
    bg: 'bg-blue-400/10',
    activeBg: 'bg-gradient-to-br from-blue-500/20 to-blue-900/10',
    border: 'border-blue-400/40',
    activeBorder: 'border-blue-400/70',
    glow: 'shadow-blue-500/10',
    label_de: 'Domains', label_en: 'Domains',
    desc_de: 'Erkenne Länder an ihrer Google-Domain',
    desc_en: 'Identify countries by their Google domain',
    example: '.de  .fr  .jp  .br',
  },
  capitals: {
    icon: '🏛️',
    color: 'text-emerald-400',
    bg: 'bg-emerald-400/10',
    activeBg: 'bg-gradient-to-br from-emerald-500/20 to-emerald-900/10',
    border: 'border-emerald-400/40',
    activeBorder: 'border-emerald-400/70',
    glow: 'shadow-emerald-500/10',
    label_de: 'Hauptstädte', label_en: 'Capitals',
    desc_de: 'Ordne Ländern ihre Hauptstadt zu',
    desc_en: 'Match countries with their capital city',
    example: 'Berlin · Paris · Tokyo',
  },
}

const PROGRESS_FILTERS = {
  all:        { de: 'Alle',            en: 'All' },
  notStarted: { de: 'Nicht gestartet', en: 'Not started' },
  inProgress: { de: 'In Bearbeitung',  en: 'In progress' },
  done:       { de: 'Abgeschlossen',   en: 'Done' },
}

// ── helpers ───────────────────────────────────────────────────────────────────

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

// ── sub-components ────────────────────────────────────────────────────────────

function ProgressBar({ learned, total, color }) {
  const pct = total > 0 ? Math.round((learned / total) * 100) : 0
  const done = pct === 100
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${done ? 'bg-green-500' : color.replace('text-', 'bg-')}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-500 shrink-0 tabular-nums w-12 text-right">{learned}/{total}</span>
    </div>
  )
}

function FavButton({ isFav, onToggle }) {
  return (
    <button
      onClick={e => { e.preventDefault(); e.stopPropagation(); onToggle() }}
      className={`p-1.5 rounded-lg transition-all ${isFav ? 'text-yellow-400 bg-yellow-400/10' : 'text-gray-600 hover:text-yellow-400 hover:bg-yellow-400/10'}`}
      title={isFav ? 'Aus Favoriten entfernen' : 'Zu Favoriten hinzufügen'}
    >
      <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" viewBox="0 0 24 24" fill={isFav ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
      </svg>
    </button>
  )
}

function BadgePill({ children, color = 'gray' }) {
  const cls = {
    gray:   'bg-gray-800 text-gray-400 border border-gray-700',
    green:  'bg-green-500/15 text-green-400 border border-green-500/30',
    blue:   'bg-blue-500/15 text-blue-400 border border-blue-500/30',
    yellow: 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30',
  }[color] || 'bg-gray-800 text-gray-400'
  return <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>{children}</span>
}

// Quiz type card button (side-by-side grid)
function QuizTypeCard({ type, lang, active, onClick }) {
  const meta = TYPE_META[type]
  const label = lang === 'en' ? meta.label_en : meta.label_de
  const desc = lang === 'en' ? meta.desc_en : meta.desc_de
  return (
    <button
      onClick={onClick}
      className={`relative flex flex-col items-center gap-3 p-5 rounded-2xl border text-center transition-all duration-200 w-full overflow-hidden
        ${active
          ? `${meta.activeBg} ${meta.activeBorder} shadow-lg ${meta.glow}`
          : 'bg-gray-900 border-gray-800 hover:border-gray-600'
        }`}
    >
      {/* Background glow blob */}
      {active && (
        <div className={`absolute -top-8 left-1/2 -translate-x-1/2 w-32 h-32 rounded-full blur-3xl opacity-20 ${meta.color.replace('text-', 'bg-')}`} />
      )}
      <span className="text-4xl">{meta.icon}</span>
      <div>
        <div className={`font-bold text-base ${active ? meta.color : 'text-white'}`}>{label}</div>
        <div className="text-xs text-gray-500 mt-1 leading-snug">{desc}</div>
      </div>
      <div className={`text-xs font-mono tracking-wide mt-1 ${active ? meta.color : 'text-gray-600'} opacity-80`}>
        {meta.example}
      </div>
      {active && (
        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${meta.bg} ${meta.color} border ${meta.border}`}>
          ▾ {lang === 'en' ? 'selected' : 'ausgewählt'}
        </span>
      )}
    </button>
  )
}

// Continent card inside a quiz type
function ContinentCard({ course, meta, lang, isFav, onToggleFav }) {
  const learned = course.learned_count ?? 0
  const total = course.total_count ?? course.country_count ?? 0
  const displayName = course.continent_name
    ? (lang === 'de' && course.continent_name_de ? course.continent_name_de : course.continent_name)
    : (lang === 'en' ? 'General' : 'Allgemein')
  const done = learned >= total && total > 0
  return (
    <Link
      to={`/practice/course/${course.id}`}
      className={`flex flex-col gap-3 bg-gray-900/80 border rounded-xl px-4 py-4 transition-all group hover:scale-[1.01] ${
        done ? 'border-green-500/30 hover:border-green-400/50' : `border-gray-800 hover:${meta.border}`
      }`}
    >
      <div className="flex items-center gap-2">
        <span className={`text-sm font-bold flex-1 ${done ? 'text-green-400' : 'text-white'}`}>{displayName}</span>
        {done && <BadgePill color="green">✓ {lang === 'en' ? 'Done' : 'Fertig'}</BadgePill>}
        <FavButton isFav={isFav} onToggle={() => onToggleFav(course.id)} />
      </div>
      <ProgressBar learned={learned} total={total} color={meta.color} />
      <div className="text-xs text-gray-600">{total} {lang === 'en' ? 'countries' : 'Länder'}</div>
    </Link>
  )
}

// Quiz type expanded section with continent grid
function QuizTypeSection({ type, courses, lang, favs, onToggleFav }) {
  const meta = TYPE_META[type]
  const byContinent = {}
  const order = []
  for (const c of courses) {
    const key = c.continent_name || '__general__'
    if (!byContinent[key]) { byContinent[key] = c; order.push(key) }
  }

  if (order.length === 0) return (
    <div className="text-gray-600 text-sm text-center py-8 italic">
      {lang === 'en' ? 'No courses available yet.' : 'Noch keine Kurse verfügbar.'}
    </div>
  )

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {order.map(key => (
        <ContinentCard
          key={key}
          course={byContinent[key]}
          meta={meta}
          lang={lang}
          isFav={favs.has(byContinent[key].id)}
          onToggleFav={onToggleFav}
        />
      ))}
    </div>
  )
}

// Clue course card
function ClueCard({ course, lang, isFav, onToggleFav }) {
  const learned = course.learned_count ?? 0
  const total = course.total_count ?? 0
  const creator = extractCreator(course.description)
  const contName = lang === 'de' && course.continent_name_de
    ? course.continent_name_de
    : (course.continent_name || (lang === 'en' ? 'General' : 'Allgemein'))
  const done = learned >= total && total > 0
  const pct = total > 0 ? Math.round((learned / total) * 100) : 0

  return (
    <Link
      to={`/practice/course/${course.id}`}
      className={`flex flex-col gap-3 bg-gray-900 border rounded-xl px-4 py-4 transition-all hover:scale-[1.01] ${
        done
          ? 'border-green-500/30 hover:border-green-400/50'
          : 'border-gray-800 hover:border-purple-400/40'
      }`}
    >
      {/* Header row */}
      <div className="flex items-start gap-2">
        <div className="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center shrink-0 text-base">
          🔍
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-white truncate text-sm leading-tight">{course.name}</div>
          <div className="flex items-center gap-1.5 mt-1 flex-wrap">
            <BadgePill>{contName}</BadgePill>
            {creator && <BadgePill>{lang === 'en' ? 'by' : 'von'} {creator}</BadgePill>}
          </div>
        </div>
        <FavButton isFav={isFav} onToggle={() => onToggleFav(course.id)} />
      </div>

      {/* Progress */}
      <ProgressBar learned={learned} total={total} color="text-purple-400" />

      {/* Footer */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-600">{total} {lang === 'en' ? 'clues' : 'Clues'}</span>
        {done
          ? <BadgePill color="green">✓ {lang === 'en' ? 'Complete' : 'Abgeschlossen'}</BadgePill>
          : pct > 0
            ? <BadgePill color="blue">{pct}% {lang === 'en' ? 'done' : 'erledigt'}</BadgePill>
            : <span className="text-xs text-gray-600">{lang === 'en' ? 'Not started' : 'Nicht gestartet'}</span>
        }
      </div>
    </Link>
  )
}

// Active filter chip
function FilterChip({ label, onRemove }) {
  return (
    <span className="flex items-center gap-1 px-2.5 py-1 bg-blue-900/40 border border-blue-600/50 rounded-full text-xs text-blue-300">
      {label}
      <button onClick={onRemove} className="hover:text-white transition-colors ml-0.5">
        <svg xmlns="http://www.w3.org/2000/svg" className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
      </button>
    </span>
  )
}

// ── main view ─────────────────────────────────────────────────────────────────

export default function CoursesView({ onLogout }) {
  const { t, lang } = useLang()
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeQuizType, setActiveQuizType] = useState(null)
  const [favs, setFavs] = useState(getFavs)

  const [searchQ, setSearchQ] = useState('')
  const [filterContinent, setFilterContinent] = useState('')
  const [filterCreator, setFilterCreator] = useState('')
  const [filterProgress, setFilterProgress] = useState('all')
  const [filterFavs, setFilterFavs] = useState(false)

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

  const creators = useMemo(() => {
    const set = new Set()
    for (const c of clueCourses) {
      const cr = extractCreator(c.description)
      if (cr) set.add(cr)
    }
    return [...set].sort()
  }, [clueCourses])

  const filteredClues = useMemo(() => {
    let list = clueCourses
    if (filterFavs) list = list.filter(c => favs.has(c.id))
    if (searchQ.trim()) list = list.filter(c => c.name.toLowerCase().includes(searchQ.toLowerCase()))
    if (filterContinent === '__general__') list = list.filter(c => !c.continent_name)
    else if (filterContinent) list = list.filter(c => c.continent_name === filterContinent)
    if (filterCreator) list = list.filter(c => extractCreator(c.description) === filterCreator)
    if (filterProgress !== 'all') {
      list = list.filter(c => progressStatus(c.learned_count ?? 0, c.total_count ?? 0) === filterProgress)
    }
    return list
  }, [clueCourses, searchQ, filterContinent, filterCreator, filterProgress, filterFavs, favs])

  const favCourses = useMemo(() => courses.filter(c => favs.has(c.id)), [courses, favs])

  const activeFilters = []
  if (searchQ.trim()) activeFilters.push({ key: 'search', label: `"${searchQ}"`, clear: () => setSearchQ('') })
  if (filterContinent) {
    const label = filterContinent === '__general__'
      ? (lang === 'en' ? 'General' : 'Allgemein')
      : (continents.find(([k]) => k === filterContinent)?.[1] || filterContinent)
    activeFilters.push({ key: 'continent', label, clear: () => setFilterContinent('') })
  }
  if (filterCreator) activeFilters.push({ key: 'creator', label: `${lang === 'en' ? 'by' : 'von'} ${filterCreator}`, clear: () => setFilterCreator('') })
  if (filterProgress !== 'all') activeFilters.push({ key: 'progress', label: PROGRESS_FILTERS[filterProgress][lang], clear: () => setFilterProgress('all') })
  if (filterFavs) activeFilters.push({ key: 'favs', label: `⭐ ${lang === 'en' ? 'Favourites' : 'Favoriten'}`, clear: () => setFilterFavs(false) })

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950">
      <div className="text-blue-400 text-lg">{t.loading}</div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Header onLogout={onLogout} />

      {/* Hero banner */}
      <div className="relative bg-gradient-to-b from-gray-900 to-gray-950 border-b border-gray-800 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,_rgba(59,130,246,0.08),_transparent_60%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(168,85,247,0.06),_transparent_60%)]" />
        <div className="relative max-w-6xl mx-auto px-4 sm:px-8 py-10">
          <div className="flex items-end justify-between gap-4 flex-wrap">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-3xl">📚</span>
                <h1 className="text-3xl font-bold text-white">
                  {lang === 'en' ? 'Courses' : 'Kurse'}
                </h1>
              </div>
              <p className="text-gray-400 text-sm max-w-xl">
                {lang === 'en'
                  ? 'Train flags, domains, and capitals by continent — or dive into curated photo clue courses to master GeoGuessr.'
                  : 'Trainiere Flaggen, Domains und Hauptstädte nach Kontinent — oder lerne mit kuratierten Foto-Clue-Kursen.'}
              </p>
            </div>
            <div className="flex items-center gap-3 text-sm text-gray-500">
              <span className="px-3 py-1.5 rounded-lg bg-gray-800 border border-gray-700">
                {courses.length} {lang === 'en' ? 'courses total' : 'Kurse gesamt'}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="w-full max-w-6xl mx-auto px-4 sm:px-8 py-8 space-y-10">

        {/* ── Favourites strip ── */}
        {favCourses.length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-yellow-400 text-lg">⭐</span>
              <h2 className="text-base font-bold text-white">{lang === 'en' ? 'Favourites' : 'Favoriten'}</h2>
              <span className="text-xs text-gray-600 ml-1">{lang === 'en' ? '— your starred courses' : '— deine gespeicherten Kurse'}</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {favCourses.map(course => {
                const learned = course.learned_count ?? 0
                const total = course.total_count ?? course.country_count ?? 0
                const meta = TYPE_META[course.course_type] || TYPE_META['flags']
                const isClue = course.course_type === 'clues'
                const contName = lang === 'de' && course.continent_name_de
                  ? course.continent_name_de
                  : (course.continent_name || (lang === 'en' ? 'General' : 'Allgemein'))
                return (
                  <Link key={course.id} to={`/practice/course/${course.id}`}
                    className="flex flex-col gap-3 bg-gray-900 border border-yellow-400/20 hover:border-yellow-400/50 rounded-xl px-4 py-4 transition-all hover:scale-[1.01]">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">{isClue ? '🔍' : meta.icon}</span>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-white truncate text-sm">{course.name}</div>
                        <div className="text-xs text-gray-500 mt-0.5">{contName}</div>
                      </div>
                      <FavButton isFav={true} onToggle={() => toggleFav(course.id)} />
                    </div>
                    <ProgressBar learned={learned} total={total} color={isClue ? 'text-purple-400' : meta.color} />
                  </Link>
                )
              })}
            </div>
          </section>
        )}

        {/* ── Quiz type tabs: Flags / Domains / Capitals ── */}
        <section>
          <div className="mb-5">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              🎯 {lang === 'en' ? 'Quiz Categories' : 'Quiz-Kategorien'}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {lang === 'en'
                ? 'Pick a category, then select a continent to start.'
                : 'Wähle eine Kategorie, dann einen Kontinent zum Starten.'}
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3">
            {QUIZ_TYPES.map(type => (
              <QuizTypeCard
                key={type}
                type={type}
                lang={lang}
                active={activeQuizType === type}
                onClick={() => setActiveQuizType(activeQuizType === type ? null : type)}
              />
            ))}
          </div>

          {activeQuizType && (
            <div className="mt-4">
              <QuizTypeSection
                type={activeQuizType}
                courses={quizCourses.filter(c => c.course_type === activeQuizType)}
                lang={lang}
                favs={favs}
                onToggleFav={toggleFav}
              />
            </div>
          )}
        </section>

        {/* Divider */}
        <div className="border-t border-gray-800" />

        {/* ── Clue courses ── */}
        <section>
          <div className="mb-5">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              🔍 {lang === 'en' ? 'Clue Courses' : 'Clue-Kurse'}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {lang === 'en'
                ? 'Photo-based courses — recognize countries by landscape, bollards, road signs, and more.'
                : 'Foto-basierte Kurse — erkenne Länder an Landschaft, Poller, Straßenschilder und mehr.'}
            </p>
          </div>

          {/* Search + filters */}
          <div className="flex flex-col gap-3 mb-5 p-4 bg-gray-900/50 border border-gray-800 rounded-2xl">
            <input
              className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 text-sm"
              placeholder={lang === 'en' ? '🔎  Search courses by name...' : '🔎  Kurse nach Name suchen...'}
              value={searchQ}
              onChange={e => setSearchQ(e.target.value)}
            />

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <select
                className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                value={filterContinent}
                onChange={e => setFilterContinent(e.target.value)}
              >
                <option value="">{lang === 'en' ? '🌍 All continents' : '🌍 Alle Kontinente'}</option>
                <option value="__general__">{lang === 'en' ? '🌐 General (world-wide)' : '🌐 Allgemein (weltweit)'}</option>
                {continents.map(([key, name]) => <option key={key} value={key}>{name}</option>)}
              </select>

              <select
                className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                value={filterCreator}
                onChange={e => setFilterCreator(e.target.value)}
              >
                <option value="">{lang === 'en' ? '👤 All creators' : '👤 Alle Ersteller'}</option>
                {creators.map(cr => <option key={cr} value={cr}>👤 {cr}</option>)}
              </select>

              <select
                className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500"
                value={filterProgress}
                onChange={e => setFilterProgress(e.target.value)}
              >
                {Object.entries(PROGRESS_FILTERS).map(([key, lbl]) => (
                  <option key={key} value={key}>{lbl[lang]}</option>
                ))}
              </select>

              <button
                onClick={() => setFilterFavs(f => !f)}
                className={`px-3 py-2 rounded-lg text-sm font-semibold border transition-all ${
                  filterFavs
                    ? 'bg-yellow-400/10 border-yellow-400/40 text-yellow-400'
                    : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500 hover:text-gray-200'
                }`}
              >
                ⭐ {lang === 'en' ? 'Favourites' : 'Favoriten'}
              </button>
            </div>

            {/* Active chips + count row */}
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <div className="flex flex-wrap gap-2 items-center">
                {activeFilters.map(f => <FilterChip key={f.key} label={f.label} onRemove={f.clear} />)}
                {activeFilters.length > 0 && (
                  <button
                    onClick={() => { setSearchQ(''); setFilterContinent(''); setFilterCreator(''); setFilterProgress('all'); setFilterFavs(false) }}
                    className="text-xs text-gray-500 hover:text-gray-300 transition-colors underline underline-offset-2"
                  >
                    {lang === 'en' ? 'Clear all' : 'Alle entfernen'}
                  </button>
                )}
              </div>
              {clueCourses.length > 0 && (
                <span className="text-xs text-gray-600 shrink-0">
                  {filteredClues.length === clueCourses.length
                    ? `${clueCourses.length} ${lang === 'en' ? 'courses' : 'Kurse'}`
                    : `${filteredClues.length} / ${clueCourses.length} ${lang === 'en' ? 'courses' : 'Kurse'}`}
                </span>
              )}
            </div>
          </div>

          {/* Clue course grid */}
          {filteredClues.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-16 text-center">
              <span className="text-4xl opacity-30">🔍</span>
              <p className="text-gray-500 text-sm">
                {activeFilters.length > 0
                  ? (lang === 'en' ? 'No courses match your filters.' : 'Keine Kurse passen zu deinen Filtern.')
                  : (lang === 'en' ? 'No clue courses available yet.' : 'Noch keine Clue-Kurse verfügbar.')}
              </p>
              {activeFilters.length > 0 && (
                <button
                  onClick={() => { setSearchQ(''); setFilterContinent(''); setFilterCreator(''); setFilterProgress('all'); setFilterFavs(false) }}
                  className="text-xs text-blue-400 hover:text-blue-300 underline underline-offset-2"
                >
                  {lang === 'en' ? 'Clear filters' : 'Filter entfernen'}
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {filteredClues.map(course => (
                <ClueCard
                  key={course.id}
                  course={course}
                  lang={lang}
                  isFav={favs.has(course.id)}
                  onToggleFav={() => toggleFav(course.id)}
                />
              ))}
            </div>
          )}
        </section>

      </div>
    </div>
  )
}
