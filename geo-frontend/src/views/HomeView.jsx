import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

export default function HomeView({ onLogout }) {
  const [continents, setContinents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getContinents()
      .then(r => r.json())
      .then(data => { setContinents(data.results ?? data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950">
      <div className="text-blue-400 text-lg">Laden...</div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-5xl mx-auto px-4 py-12">
        <div className="mb-10 text-center relative">
          <h1 className="text-4xl font-bold mb-2">
            GeoGuessr <span className="text-blue-400">Trainer</span>
          </h1>
          <p className="text-gray-400">
            Wähle einen Kontinent um Kurse zu starten oder Länder nachzuschlagen.
          </p>
          <button
            onClick={onLogout}
            className="absolute right-0 top-0 text-xs text-gray-600 hover:text-gray-400 transition-colors"
          >
            Abmelden
          </button>
        </div>

        {continents.length === 0 ? (
          <div className="text-gray-500 text-center py-20">
            Noch keine Kontinente im System.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {continents.map(continent => (
              <Link
                key={continent.slug}
                to={`/${continent.slug}`}
                className="group relative rounded-xl overflow-hidden bg-gray-800 hover:bg-gray-700 transition-all border border-gray-700 hover:border-blue-500"
              >
                {continent.cover_image ? (
                  <img
                    src={continent.cover_image}
                    alt={continent.name}
                    className="w-full h-40 object-contain opacity-60 group-hover:opacity-80 transition-opacity"
                  />
                ) : (
                  <div className="w-full h-40 bg-gradient-to-br from-blue-900 to-gray-800 flex items-center justify-center">
                    <span className="text-5xl">🌐</span>
                  </div>
                )}
                <div className="p-4">
                  <h2 className="text-xl font-bold mb-1">{continent.name}</h2>
                  <div className="flex items-center gap-3 text-sm text-gray-500 mt-2">
                    <span>{continent.country_count} Länder</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
