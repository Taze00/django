import { useEffect, useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useLang } from '../LanguageContext'
import Header from '../Header'

const QUIZ_TYPES = ['flags', 'domains', 'capitals']

const TYPE_META = {
  flags: {
    icon: '🏳️',
    color: '#d4a84b',
    label_de: 'Flaggen', label_en: 'Flags',
    desc_de: 'Erkenne Länder anhand ihrer Nationalflagge',
    desc_en: 'Identify countries by their national flag',
  },
  domains: {
    icon: '🌐',
    color: '#7c9fc4',
    label_de: 'Domains', label_en: 'Domains',
    desc_de: 'Erkenne Länder an ihrer Google-Domain',
    desc_en: 'Identify countries by their Google domain',
  },
  capitals: {
    icon: '🏛️',
    color: '#5a9e6f',
    label_de: 'Hauptstädte', label_en: 'Capitals',
    desc_de: 'Ordne Ländern ihre Hauptstadt zu',
    desc_en: 'Match countries with their capital city',
  },
}

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

function ThinProgress({ learned, total, color }) {
  const pct = total > 0 ? Math.round((learned / total) * 100) : 0
  return (
    <div className="relative h-px w-full" style={{background:'var(--line-strong)'}}>
      <div style={{
        position:'absolute', inset:0, width:`${pct}%`,
        background: pct === 100 ? '#5a9e6f' : color,
        transition:'width 0.5s cubic-bezier(0.16,1,0.3,1)',
      }} />
    </div>
  )
}

function FavButton({ isFav, onToggle }) {
  return (
    <button
      onClick={e => { e.preventDefault(); e.stopPropagation(); onToggle() }}
      className="p-1 transition-colors"
      style={{color: isFav ? 'var(--gold)' : 'var(--line-strong)'}}
      onMouseEnter={e => { if (!isFav) e.currentTarget.style.color='var(--gold)' }}
      onMouseLeave={e => { if (!isFav) e.currentTarget.style.color='var(--line-strong)' }}
    >
      <svg className="w-3 h-3" viewBox="0 0 24 24" fill={isFav ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
      </svg>
    </button>
  )
}

function QuizRow({ type, courses, lang, favs, onToggleFav }) {
  const meta = TYPE_META[type]
  const label = lang === 'en' ? meta.label_en : meta.label_de
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-px" style={{background:'var(--line)'}}>
      {courses.map(course => {
        const learned = course.learned_count ?? 0
        const total = course.total_count ?? course.country_count ?? 0
        const done = learned >= total && total > 0
        const pct = total > 0 ? Math.round((learned / total) * 100) : 0
        const displayName = course.continent_name
          ? (lang === 'de' && course.continent_name_de ? course.continent_name_de : course.continent_name)
          : (lang === 'en' ? 'General' : 'Allgemein')
        return (
          <Link key={course.id} to={`/practice/course/${course.id}`}
            className="flex flex-col gap-4 p-5 transition-colors group"
            style={{background:'var(--ink-soft)'}}
            onMouseEnter={e => e.currentTarget.style.background='var(--ink-raised)'}
            onMouseLeave={e => e.currentTarget.style.background='var(--ink-soft)'}
          >
            <div className="flex items-center justify-between">
              <span className="font-display font-bold text-base" style={{color: done ? '#5a9e6f' : 'var(--text)'}}>{displayName}</span>
              <div className="flex items-center gap-2">
                {done && <span className="font-code text-xs" style={{color:'#5a9e6f'}}>✓</span>}
                {!done && pct > 0 && <span className="font-code text-xs tabular-nums" style={{color: meta.color}}>{pct}%</span>}
                <FavButton isFav={favs.has(course.id)} onToggle={() => onToggleFav(course.id)} />
              </div>
            </div>
            <ThinProgress learned={learned} total={total} color={meta.color} />
            <span className="font-code text-xs" style={{color:'var(--muted)'}}>
              {learned}/{total} {lang === 'en' ? 'countries' : 'Länder'}
            </span>
          </Link>
        )
      })}
    </div>
  )
}

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
      className="flex flex-col gap-4 p-5 border-l-2 transition-all group"
      style={{
        background:'var(--ink-soft)',
        borderLeftColor: done ? '#5a9e6f' : 'var(--accent)',
        borderTop:'1px solid var(--line)',
        borderRight:'1px solid var(--line)',
        borderBottom:'1px solid var(--line)',
      }}
      onMouseEnter={e => e.currentTarget.style.background='var(--ink-raised)'}
      onMouseLeave={e => e.currentTarget.style.background='var(--ink-soft)'}
    >
      <div className="flex items-start gap-2">
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm leading-tight truncate" style={{color:'var(--text)'}}>{course.name}</div>
          <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
            <span className="font-code text-xs px-1.5 py-0.5" style={{
              border:'1px solid var(--line-strong)', color:'var(--muted)', background:'var(--ink)'
            }}>
              {contName}
            </span>
            {creator && (
              <span className="font-code text-xs" style={{color:'var(--muted)'}}>
                {lang === 'en' ? 'by' : 'von'} {creator}
              </span>
            )}
          </div>
        </div>
        <FavButton isFav={isFav} onToggle={() => onToggleFav(course.id)} />
      </div>
      <ThinProgress learned={learned} total={total} color="var(--accent)" />
      <div className="flex items-center justify-between">
        <span className="font-code text-xs" style={{color:'var(--muted)'}}>{total} {lang === 'en' ? 'clues' : 'Clues'}</span>
        {done
          ? <span className="font-code text-xs" style={{color:'#5a9e6f'}}>✓</span>
          : pct > 0
            ? <span className="font-code text-xs tabular-nums" style={{color:'var(--gold)'}}>{pct}%</span>
            : null
        }
      </div>
    </Link>
  )
}

function SectionLabel({ text }) {
  return (
    <div className="flex items-center gap-3">
      <div className="h-px w-6" style={{background:'var(--gold)'}} />
      <span className="font-code text-xs uppercase tracking-widest" style={{color:'var(--gold)'}}>{text}</span>
      <div className="flex-1 h-px" style={{background:'var(--line)'}} />
    </div>
  )
}

export default function CoursesView({ onLogout }) {
  const { lang } = useLang()
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeQuizType, setActiveQuizType] = useState(null)
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
  }, [clueCourses, searchQ, filterContinent, filterProgress, favs])

  const hasActiveFilters = searchQ.trim() || filterContinent || filterProgress !== 'all'

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen cart-bg" style={{background:'var(--ink)'}}>
      <div className="w-8 h-8 border-t border-r rounded-full animate-spin" style={{borderColor:'var(--gold)'}} />
    </div>
  )

  const selectStyle = {
    background: 'var(--ink)', border: '1px solid var(--line-strong)',
    color: 'var(--text)', padding: '8px 12px', fontSize: '13px',
    fontFamily: "'DM Mono', monospace", width: '100%', outline: 'none',
  }

  return (
    <div className="min-h-screen cart-bg" style={{background:'var(--ink)'}}>
      <Header onLogout={onLogout} />

      {/* Page header */}
      <div className="relative overflow-hidden" style={{borderBottom:'1px solid var(--line)'}}>
        <div className="absolute inset-0 pointer-events-none" style={{
          background: 'radial-gradient(ellipse 80% 60% at 80% 0%, rgba(212,168,75,0.05) 0%, transparent 70%)'
        }} />
        <div className="max-w-7xl mx-auto px-5 sm:px-10 py-12 anim-0">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-px w-6" style={{background:'var(--gold)'}} />
            <span className="font-code text-xs uppercase tracking-widest" style={{color:'var(--gold)'}}>
              {lang === 'en' ? 'Training Library' : 'Trainings-Bibliothek'}
            </span>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-end gap-4 justify-between">
            <h1 className="font-display text-5xl sm:text-6xl font-black" style={{color:'var(--text)'}}>
              {lang === 'en' ? 'Courses' : 'Kurse'}
            </h1>
            <div className="flex gap-3">
              <Link to="/create-course"
                className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-semibold border transition-all font-code"
                style={{borderColor:'var(--line-strong)', color:'var(--muted)', background:'var(--ink-soft)'}}
                onMouseEnter={e => { e.currentTarget.style.borderColor='var(--gold)'; e.currentTarget.style.color='var(--text)' }}
                onMouseLeave={e => { e.currentTarget.style.borderColor='var(--line-strong)'; e.currentTarget.style.color='var(--muted)' }}
              >
                + {lang === 'en' ? 'New Course' : 'Neuer Kurs'}
              </Link>
              <Link to="/my-courses"
                className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-semibold border transition-all font-code"
                style={{borderColor:'var(--line-strong)', color:'var(--muted)', background:'var(--ink-soft)'}}
                onMouseEnter={e => { e.currentTarget.style.borderColor='var(--gold)'; e.currentTarget.style.color='var(--text)' }}
                onMouseLeave={e => { e.currentTarget.style.borderColor='var(--line-strong)'; e.currentTarget.style.color='var(--muted)' }}
              >
                ★ {lang === 'en' ? 'My Courses' : 'Meine Kurse'}
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-5 sm:px-10 py-12 space-y-14">

        {/* ── Quiz Categories ── */}
        <section className="anim-1">
          <SectionLabel text={lang === 'en' ? 'Quiz' : 'Quiz'} />

          {/* 3 type tabs */}
          <div className="mt-6 grid grid-cols-3 gap-px" style={{background:'var(--line)'}}>
            {QUIZ_TYPES.map(type => {
              const meta = TYPE_META[type]
              const label = lang === 'en' ? meta.label_en : meta.label_de
              const active = activeQuizType === type
              return (
                <button key={type}
                  onClick={() => setActiveQuizType(active ? null : type)}
                  className="flex flex-col items-start gap-2 px-5 py-4 transition-colors text-left"
                  style={{background: active ? 'var(--ink-raised)' : 'var(--ink-soft)'}}
                  onMouseEnter={e => { if (!active) e.currentTarget.style.background='var(--ink-raised)' }}
                  onMouseLeave={e => { if (!active) e.currentTarget.style.background='var(--ink-soft)' }}
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="font-display font-bold text-sm" style={{color: active ? meta.color : 'var(--text)'}}>
                      {label}
                    </span>
                    <svg className="w-3 h-3 transition-transform duration-200" style={{
                      color: active ? meta.color : 'var(--muted)',
                      transform: active ? 'rotate(180deg)' : 'rotate(0deg)'
                    }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                  <span className="font-code text-xs leading-snug" style={{color:'var(--muted)'}}>
                    {lang === 'en' ? meta.desc_en : meta.desc_de}
                  </span>
                  {active && (
                    <div className="w-6 h-0.5 mt-1" style={{background: meta.color}} />
                  )}
                </button>
              )
            })}
          </div>

          {activeQuizType && (
            <div className="mt-px" style={{border:'1px solid var(--line)', borderTop:'none'}}>
              <QuizRow
                type={activeQuizType}
                courses={quizCourses.filter(c => c.course_type === activeQuizType)}
                lang={lang}
                favs={favs}
                onToggleFav={toggleFav}
              />
              {quizCourses.filter(c => c.course_type === activeQuizType).length === 0 && (
                <div className="py-10 text-center font-code text-xs" style={{color:'var(--muted)'}}>
                  — {lang === 'en' ? 'no courses yet' : 'noch keine Kurse'} —
                </div>
              )}
            </div>
          )}
        </section>

        <div className="divider-gold" />

        {/* ── Clue Courses ── */}
        <section className="anim-2">
          <SectionLabel text={lang === 'en' ? 'Clue Courses' : 'Clue-Kurse'} />

          <p className="text-sm mt-3 mb-8" style={{color:'var(--muted)'}}>
            {lang === 'en'
              ? 'Photo-based — recognize countries by landscape, bollards, road signs, and more.'
              : 'Foto-basiert — erkenne Länder an Landschaft, Poller, Straßenschilder und mehr.'}
          </p>

          {/* Filters — compact inline row */}
          <div className="flex flex-wrap gap-2 mb-6 items-center">
            <div className="relative flex-1 min-w-48">
              <svg xmlns="http://www.w3.org/2000/svg" className="absolute left-3 top-1/2 -translate-y-1/2 w-3 h-3" style={{color:'var(--muted)'}} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
              </svg>
              <input
                style={{...selectStyle, paddingLeft:'32px'}}
                placeholder={lang === 'en' ? 'Search courses…' : 'Kurse suchen…'}
                value={searchQ}
                onChange={e => setSearchQ(e.target.value)}
              />
            </div>

            <select style={{...selectStyle, flex:'0 0 160px', width:'auto'}} value={filterContinent} onChange={e => setFilterContinent(e.target.value)}>
              <option value="">{lang === 'en' ? 'All regions' : 'Alle Regionen'}</option>
              <option value="__general__">{lang === 'en' ? 'General' : 'Allgemein'}</option>
              {continents.map(([key, name]) => <option key={key} value={key}>{name}</option>)}
            </select>

            <select style={{...selectStyle, flex:'0 0 150px', width:'auto'}} value={filterProgress} onChange={e => setFilterProgress(e.target.value)}>
              <option value="all">{lang === 'en' ? 'All progress' : 'Alle'}</option>
              <option value="notStarted">{lang === 'en' ? 'Not started' : 'Nicht gestartet'}</option>
              <option value="inProgress">{lang === 'en' ? 'In progress' : 'In Bearbeitung'}</option>
              <option value="done">{lang === 'en' ? 'Done' : 'Fertig'}</option>
            </select>

            <div className="flex items-center gap-3 ml-auto">
              <span className="font-code text-xs" style={{color:'var(--muted)'}}>
                {filteredClues.length === clueCourses.length
                  ? `${clueCourses.length} ${lang === 'en' ? 'courses' : 'Kurse'}`
                  : `${filteredClues.length} / ${clueCourses.length}`}
              </span>
              {hasActiveFilters && (
                <button
                  onClick={() => { setSearchQ(''); setFilterContinent(''); setFilterProgress('all') }}
                  className="font-code text-xs underline underline-offset-2"
                  style={{color:'var(--muted)'}}
                  onMouseEnter={e => e.currentTarget.style.color='var(--text)'}
                  onMouseLeave={e => e.currentTarget.style.color='var(--muted)'}
                >
                  {lang === 'en' ? 'Clear' : 'Zurücksetzen'}
                </button>
              )}
            </div>
          </div>

          {filteredClues.length === 0 ? (
            <div className="py-20 text-center font-code text-xs" style={{color:'var(--muted)'}}>
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
        </section>
      </div>
    </div>
  )
}
