import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'

const CATEGORY_LABELS = {
  car: '🚗 Fahrzeuge',
  infrastructure: '🏗️ Infrastruktur',
  vegetation: '🌿 Vegetation',
  signs: '🪧 Schilder',
  landscape: '🏔️ Landschaft',
  plates: '🔢 Nummernschilder',
  other: '📌 Sonstiges',
}

function ImportanceStars({ value }) {
  return (
    <span className="text-yellow-400">
      {'★'.repeat(value)}
      <span className="text-gray-600">{'★'.repeat(3 - value)}</span>
    </span>
  )
}

export default function CountryView() {
  const { continentSlug, countrySlug } = useParams()
  const [country, setCountry] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getCountry(countrySlug)
      .then(r => r.json())
      .then(data => { setCountry(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [countrySlug])

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950">
      <div className="text-blue-400 text-lg">Laden...</div>
    </div>
  )

  if (!country) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950 text-gray-400">
      Land nicht gefunden.
    </div>
  )

  // Group clues by category
  const byCategory = country.clues.reduce((acc, clue) => {
    if (!acc[clue.category]) acc[clue.category] = []
    acc[clue.category].push(clue)
    return acc
  }, {})

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-4xl mx-auto px-4 py-12">
        <Link to={`/${continentSlug}`} className="text-blue-400 hover:text-blue-300 text-sm mb-6 inline-block">
          ← Zurück zu {continentSlug}
        </Link>

        <div className="flex items-center gap-4 mb-4">
          <span className="text-6xl">{country.flag_emoji}</span>
          <div>
            <h1 className="text-3xl font-bold">{country.name}</h1>
            <div className="flex items-center gap-3 text-sm text-gray-400 mt-1">
              <span>{country.drive_side_display}</span>
              <span>·</span>
              <ImportanceStars value={country.difficulty} />
            </div>
          </div>
        </div>

        {country.short_summary && (
          <p className="text-gray-300 mb-8 leading-relaxed">{country.short_summary}</p>
        )}

        {country.clues.length === 0 ? (
          <div className="text-gray-500 text-center py-16">
            Noch keine Hinweise für dieses Land vorhanden.
          </div>
        ) : (
          Object.entries(byCategory).map(([category, clues]) => (
            <div key={category} className="mb-10">
              <h2 className="text-lg font-semibold text-blue-400 mb-4 border-b border-gray-800 pb-2">
                {CATEGORY_LABELS[category] || category}
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                {clues.map(clue => (
                  <div key={clue.id} className="bg-gray-800 rounded-xl overflow-hidden border border-gray-700">
                    {clue.image && (
                      <img
                        src={clue.image}
                        alt={clue.title}
                        className="w-full h-48 object-cover"
                      />
                    )}
                    <div className="p-4">
                      <div className="flex items-start justify-between mb-1">
                        <h3 className="font-semibold">{clue.title}</h3>
                        <ImportanceStars value={clue.importance} />
                      </div>
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
