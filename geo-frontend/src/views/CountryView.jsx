import { useEffect, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useLang } from '../LanguageContext'

const CATEGORY_LABELS = {
  car: '🚗 Fahrzeuge',
  infrastructure: '🏗️ Infrastruktur',
  vegetation: '🌿 Vegetation',
  signs: '🪧 Schilder',
  landscape: '🏔️ Landschaft',
  plates: '🔢 Nummernschilder',
  other: '📌 Sonstiges',
}

const CATEGORY_LABELS_EN = {
  car: '🚗 Vehicles',
  infrastructure: '🏗️ Infrastructure',
  vegetation: '🌿 Vegetation',
  signs: '🪧 Signs',
  landscape: '🏔️ Landscape',
  plates: '🔢 License Plates',
  other: '📌 Other',
}

function flagUrl(val) {
  if (!val) return null
  if (val.codePointAt(0) >= 0x1F1E0) {
    const iso = [...val].map(c => String.fromCharCode(c.codePointAt(0) - 0x1F1E6 + 65)).join('').toLowerCase()
    return 'https://flagcdn.com/w80/' + iso + '.png'
  }
  return 'https://flagcdn.com/w80/' + val.toLowerCase() + '.png'
}

export default function CountryView() {
  const { continentSlug, countrySlug } = useParams()
  const { t, lang } = useLang()
  const [country, setCountry] = useState(null)
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const catLabels = lang === 'en' ? CATEGORY_LABELS_EN : CATEGORY_LABELS

  useEffect(() => {
    Promise.all([
      api.getCountry(countrySlug).then(r => r.json()),
      api.getCountryCourses(countrySlug).then(r => r.json()).catch(() => []),
    ]).then(([countryData, coursesData]) => {
      setCountry(countryData)
      setCourses(Array.isArray(coursesData) ? coursesData : (coursesData.results ?? []))
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [countrySlug])

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950">
      <div className="text-blue-400 text-lg">{t.loading}</div>
    </div>
  )

  if (!country) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950 text-gray-400">
      {t.countryNotFound}
    </div>
  )

  const flagImg = flagUrl(country.flag_emoji)

  const byCategory = country.clues.reduce((acc, clue) => {
    if (!acc[clue.category]) acc[clue.category] = []
    acc[clue.category].push(clue)
    return acc
  }, {})

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="w-full max-w-6xl mx-auto px-6 py-12 sm:py-16 sm:px-16">

        <div className="grid grid-cols-[2.25rem_1fr_2.25rem] items-center mb-10">
          <Link to={`/${continentSlug}`} className="inline-flex items-center justify-center w-9 h-9 text-gray-400 hover:text-white border border-gray-700 hover:border-gray-500 rounded-lg transition-all">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg>
          </Link>
          <div className="flex flex-col items-center gap-2">
            {flagImg && <img src={flagImg} alt={country.name} className="h-10 rounded shadow-lg" />}
            <h1 className="text-3xl font-bold text-center">{lang === 'de' && country.name_de ? country.name_de : country.name}</h1>
            <div className="flex items-center gap-3 text-sm text-gray-400">
              <span>{country.drive_side_display}</span>
              {country.domain && (
                <span className="font-mono text-blue-400 text-xs">{country.domain}</span>
              )}
            </div>
          </div>
        </div>

        {country.map_image && (
          <img
            src={country.map_image}
            alt={`Karte ${country.name}`}
            className="w-full h-56 object-contain rounded-xl mb-8 bg-gray-800"
          />
        )}

        {country.short_summary && (
          <p className="text-gray-300 mb-8 leading-relaxed">{country.short_summary}</p>
        )}

        {courses.length > 0 && (
          <div className="mb-8">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {courses.map(course => (
                <Link
                  key={course.id}
                  to={`/practice/course/${course.id}`}
                  className="bg-gray-900 hover:bg-gray-800 border border-gray-800 hover:border-blue-500 rounded-xl px-5 py-4 transition-all group flex items-center justify-between"
                >
                  <div>
                    <div className="font-semibold text-white">{course.name}</div>
                    {course.description && <p className="text-gray-500 text-xs mt-0.5">{course.description}</p>}
                  </div>
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-gray-600 group-hover:text-blue-400 transition-colors shrink-0 ml-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" /></svg>
                </Link>
              ))}
            </div>
          </div>
        )}

        {country.clues.length === 0 ? (
          <div className="text-gray-500 text-center py-16">
            {t.noClues}
          </div>
        ) : (
          Object.entries(byCategory).map(([category, clues]) => (
            <div key={category} className="mb-10">
              <h2 className="text-lg font-semibold text-blue-400 mb-4 border-b border-gray-800 pb-2">
                {catLabels[category] || category}
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                {clues.map(clue => (
                  <div key={clue.id} className="bg-gray-800 rounded-xl overflow-hidden border border-gray-700">
                    {clue.image && (
                      <img src={clue.image} alt={clue.title} className="w-full h-48 object-cover" />
                    )}
                    <div className="p-4">
                      <h3 className="font-semibold mb-1">{clue.title}</h3>
                      <p className="text-gray-400 text-sm leading-relaxed">{clue.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
