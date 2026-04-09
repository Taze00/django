import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
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

const DIFFICULTY_LABELS = { 1: '★ Leicht', 2: '★★ Mittel', 3: '★★★ Schwer' }
const DIFFICULTY_LABELS_EN = { 1: '★ Easy', 2: '★★ Medium', 3: '★★★ Hard' }
const DIFFICULTY_COLORS = { 1: 'text-green-400', 2: 'text-yellow-400', 3: 'text-red-400' }

export default function ContinentView() {
  const { continentSlug } = useParams()
  const { t, lang } = useLang()
  const [searchParams] = useSearchParams()
  const coursesOnly = searchParams.get('courses') === '1'
  const [continent, setContinent] = useState(null)
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const diffLabels = lang === 'en' ? DIFFICULTY_LABELS_EN : DIFFICULTY_LABELS

  useEffect(() => {
    Promise.all([
      api.getContinent(continentSlug).then(r => r.json()),
      api.getCourses(continentSlug).then(r => r.json()),
    ]).then(([cont, coursesData]) => {
      setContinent(cont)
      setCourses(coursesData.results ?? coursesData)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [continentSlug])

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950">
      <div className="text-blue-400 text-lg">{t.loading}</div>
    </div>
  )

  if (!continent) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950 text-gray-400">
      {t.continentNotFound}
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="w-full max-w-6xl mx-auto px-6 py-12 sm:py-16 sm:px-16">
        <div className="grid grid-cols-[2.25rem_1fr_2.25rem] items-center mb-10">
          <Link to={coursesOnly ? '/courses' : '/'} className="inline-flex items-center justify-center w-9 h-9 text-gray-400 hover:text-white border border-gray-700 hover:border-gray-500 rounded-lg transition-all">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg>
          </Link>
          <h1 className="text-3xl font-bold text-center">{lang === 'de' && continent.name_de ? continent.name_de : continent.name}</h1>
        </div>

        {courses.length > 0 && (
          <div className="mb-10">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {courses.map(course => (
                <Link
                  key={course.id}
                  to={`/practice/course/${course.id}`}
                  className="bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-blue-500 rounded-xl p-5 transition-all"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-lg leading-snug">{course.name}</h3>
                  </div>
                  {course.description && (
                    <p className="text-gray-400 text-sm mb-3 line-clamp-2">{course.description}</p>
                  )}
                  <div className="text-xs text-gray-500">
                    {t.cards(course.clue_count)}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {!coursesOnly && <div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...continent.countries].sort((a, b) => b.clue_count - a.clue_count).map(country => (
              <Link
                key={country.slug}
                to={`/${continentSlug}/${country.slug}`}
                className={`group border rounded-xl overflow-hidden transition-all ${
                  country.clue_count > 0
                    ? 'bg-gray-800 hover:bg-gray-700 border-gray-700 hover:border-blue-500'
                    : 'bg-gray-900 border-gray-800 opacity-50 hover:opacity-70'
                }`}
              >
                <div className="w-full h-32 bg-gradient-to-br from-gray-700 to-gray-900 flex items-center justify-center">
                  <img src={flagUrl(country.flag_emoji)} alt={country.name} className="h-16 rounded shadow-lg" />
                </div>
                <div className="p-3">
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <div className="font-semibold">{lang === 'de' && country.name_de ? country.name_de : country.name}</div>
                    {country.domain && (
                      <span className="font-mono text-xs text-blue-400 shrink-0">{country.domain}</span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500">{country.clue_count} {t.clues}</div>
                </div>
              </Link>
            ))}
          </div>
        </div>}
      </div>
    </div>
  )
}
