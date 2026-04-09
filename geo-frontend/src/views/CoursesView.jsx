import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useLang } from '../LanguageContext'

const COURSE_TYPE_ORDER = ['flags', 'domains', 'capitals', 'clues']

const COURSE_TYPE_LABELS_DE = { flags: 'Flaggen', domains: 'Domains', capitals: 'Hauptstädte', clues: 'Clues' }
const COURSE_TYPE_LABELS_EN = { flags: 'Flags', domains: 'Domains', capitals: 'Capitals', clues: 'Clues' }

const COURSE_TYPE_DESC_DE = {
  flags:    'Erkenne Länder an ihrer Flagge',
  domains:  'Erkenne Länder an ihrer Google-Domain',
  capitals: 'Welche Stadt ist die Hauptstadt?',
  clues:    'Lerne typische GeoGuessr-Hinweise',
}
const COURSE_TYPE_DESC_EN = {
  flags:    'Identify countries by their flag',
  domains:  'Identify countries by their Google domain',
  capitals: 'What city is the capital?',
  clues:    'Learn typical GeoGuessr clues',
}

const TYPE_STYLES = {
  flags:    { color: 'text-amber-400',   bg: 'bg-amber-400/10',  border: 'border-amber-400/30',  icon: '🏳️' },
  domains:  { color: 'text-blue-400',    bg: 'bg-blue-400/10',   border: 'border-blue-400/30',   icon: '🌐' },
  capitals: { color: 'text-emerald-400', bg: 'bg-emerald-400/10',border: 'border-emerald-400/30',icon: '🏛️' },
  clues:    { color: 'text-purple-400',  bg: 'bg-purple-400/10', border: 'border-purple-400/30', icon: '🔍' },
}

export default function CoursesView() {
  const { t, lang } = useLang()
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeType, setActiveType] = useState('flags')
  const typeLabels = lang === 'en' ? COURSE_TYPE_LABELS_EN : COURSE_TYPE_LABELS_DE
  const typeDesc = lang === 'en' ? COURSE_TYPE_DESC_EN : COURSE_TYPE_DESC_DE

  useEffect(() => {
    api.getAllCourses()
      .then(r => r.json())
      .then(data => { const list = data.results ?? data; setCourses(Array.isArray(list) ? list : []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  // Group by continent
  const continentOrder = []
  const byContinent = {}
  for (const course of courses) {
    const key = course.continent_name
    if (!byContinent[key]) { byContinent[key] = {}; continentOrder.push(key) }
    byContinent[key][course.course_type] = course
  }

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950">
      <div className="text-blue-400 text-lg">{t.loading}</div>
    </div>
  )

  const s = TYPE_STYLES[activeType]

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="w-full max-w-6xl mx-auto px-6 py-12 sm:py-16 sm:px-16">

        {/* Header */}
        <div className="grid grid-cols-[2.25rem_1fr_2.25rem] items-center mb-10">
          <Link to="/" className="inline-flex items-center justify-center w-9 h-9 text-gray-400 hover:text-white border border-gray-700 hover:border-gray-500 rounded-lg transition-all">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg>
          </Link>
          <h1 className="text-3xl font-bold text-center">{lang === 'en' ? 'Courses' : 'Kurse'}</h1>
        </div>

        {/* Tabs */}
        <div className="grid grid-cols-4 gap-2 sm:gap-4 mb-6 sm:mb-8">
          {COURSE_TYPE_ORDER.map(type => {
            const ts = TYPE_STYLES[type]
            const active = activeType === type
            return (
              <button
                key={type}
                onClick={() => setActiveType(type)}
                className={`flex flex-col items-center gap-1.5 py-3 px-2 sm:py-5 rounded-xl border text-sm font-semibold transition-all ${
                  active
                    ? `${ts.bg} ${ts.border} ${ts.color}`
                    : 'bg-gray-900 border-gray-800 text-gray-500 hover:border-gray-600 hover:text-gray-300'
                }`}
              >
                <span className="text-xl sm:text-2xl">{ts.icon}</span>
                <span className="text-xs sm:text-sm">{typeLabels[type]}</span>
              </button>
            )
          })}
        </div>

        {/* Active type description */}
        <p className={`text-sm text-center mb-6 ${s.color}`}>{typeDesc[activeType]}</p>

        {/* Continent list */}
        {continentOrder.length === 0 ? (
          <div className="text-gray-500 text-center py-20">{t.noCourses}</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {continentOrder.map(continentName => {
              const course = byContinent[continentName][activeType]
              const displayName = lang === 'de' && course?.continent_name_de ? course.continent_name_de : continentName
              if (!course) return (
                <div key={continentName} className="flex items-center gap-4 bg-gray-900 border border-gray-800 rounded-xl px-5 py-5 opacity-30 cursor-default">
                  <span className="font-semibold text-white flex-1 text-lg">{displayName}</span>
                </div>
              )
              const dest = activeType === 'clues' ? `/${course.continent_slug}?courses=1` : `/practice/course/${course.id}`
              const learned = course.learned_count ?? 0
              const total = course.total_count ?? course.country_count ?? 0
              const pct = total > 0 ? Math.round((learned / total) * 100) : 0
              const done = pct === 100
              return (
                <Link
                  key={continentName}
                  to={dest}
                  className={`flex flex-col gap-3 bg-gray-900 hover:${s.bg} border border-gray-800 hover:${s.border} rounded-xl px-5 py-4 transition-all group`}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white flex-1 text-lg">{displayName}</span>
                    {done && <span className="text-xs text-green-400 font-semibold">✓</span>}
                    <svg xmlns="http://www.w3.org/2000/svg" className={`w-4 h-4 text-gray-600 group-hover:${s.color} transition-colors shrink-0`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" /></svg>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${done ? 'bg-green-500' : s.color.replace('text-', 'bg-')}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-500 shrink-0">{learned}/{total}</span>
                  </div>
                </Link>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
