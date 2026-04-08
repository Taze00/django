import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'

const DIFFICULTY_LABELS = { 1: '★ Leicht', 2: '★★ Mittel', 3: '★★★ Schwer' }
const DIFFICULTY_COLORS = { 1: 'text-green-400', 2: 'text-yellow-400', 3: 'text-red-400' }

export default function ContinentView() {
  const { continentSlug } = useParams()
  const [continent, setContinent] = useState(null)
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)

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
      <div className="text-blue-400 text-lg">Laden...</div>
    </div>
  )

  if (!continent) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950 text-gray-400">
      Kontinent nicht gefunden.
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-5xl mx-auto px-4 py-12">
        <Link to="/" className="text-blue-400 hover:text-blue-300 text-sm mb-6 inline-block">
          ← Zurück zur Übersicht
        </Link>

        {continent.cover_image && (
          <img
            src={continent.cover_image}
            alt={continent.name}
            className="w-full h-56 object-cover rounded-xl mb-6 opacity-80"
          />
        )}

        <h1 className="text-3xl font-bold mb-2">{continent.name}</h1>
        {continent.description && (
          <p className="text-gray-300 mb-6">{continent.description}</p>
        )}

        {/* Kurse */}
        {courses.length > 0 && (
          <div className="mb-10">
            <h2 className="text-xl font-semibold mb-4">🃏 Kurse</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {courses.map(course => (
                <Link
                  key={course.id}
                  to={`/practice/course/${course.id}`}
                  className="bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-blue-500 rounded-xl p-5 transition-all"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-lg leading-snug">{course.name}</h3>
                    <span className={`text-xs ml-3 shrink-0 ${DIFFICULTY_COLORS[course.difficulty]}`}>
                      {DIFFICULTY_LABELS[course.difficulty]}
                    </span>
                  </div>
                  {course.description && (
                    <p className="text-gray-400 text-sm mb-3 line-clamp-2">{course.description}</p>
                  )}
                  <div className="text-xs text-gray-500">
                    🃏 {course.clue_count} Karten
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {courses.length === 0 && (
          <div className="mb-10 bg-gray-800 border border-gray-700 rounded-xl p-6 text-gray-400 text-sm">
            Noch keine Kurse für {continent.name}. Im Admin unter "Courses" anlegen.
          </div>
        )}

        {/* Länder */}
        <div>
          <h2 className="text-xl font-semibold mb-4">🌍 Länder ({continent.countries.filter(c => c.clue_count > 0).length})</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {continent.countries.filter(c => c.clue_count > 0).map(country => (
              <Link
                key={country.slug}
                to={`/${continentSlug}/${country.slug}`}
                className="bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-blue-500 rounded-xl p-4 transition-all"
              >
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-3xl">{country.flag_emoji}</span>
                  <div>
                    <div className="font-semibold">{country.name}</div>
                    <div className={`text-xs ${DIFFICULTY_COLORS[country.difficulty]}`}>
                      {DIFFICULTY_LABELS[country.difficulty]}
                    </div>
                  </div>
                </div>
                <div className="text-xs text-gray-500 mt-1">{country.clue_count} Hinweise</div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
