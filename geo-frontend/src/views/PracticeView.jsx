import { useEffect, useState, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
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

export default function PracticeView() {
  const [searchParams] = useSearchParams()
  const continentParam = searchParams.get('continent') || ''

  const [clue, setClue] = useState(null)
  const [revealed, setRevealed] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [onlyUnknown, setOnlyUnknown] = useState(false)
  const [stats, setStats] = useState({ known: 0, unknown: 0 })
  const [error, setError] = useState(null)

  const loadClue = useCallback(async () => {
    setLoading(true)
    setRevealed(false)
    setError(null)
    try {
      const params = {}
      if (continentParam) params.continent = continentParam
      if (onlyUnknown) params.only_unknown = 'true'
      const res = await api.getPracticeClue(params)
      if (res.ok) {
        setClue(await res.json())
      } else {
        const data = await res.json()
        setError(data.detail || 'Keine Karten gefunden.')
        setClue(null)
      }
    } catch {
      setError('Fehler beim Laden.')
      setClue(null)
    }
    setLoading(false)
  }, [continentParam, onlyUnknown])

  useEffect(() => { loadClue() }, [loadClue])

  async function handleAnswer(known) {
    if (!clue || saving) return
    setSaving(true)
    await api.saveProgress(clue.id, known)
    setStats(s => ({
      known: s.known + (known ? 1 : 0),
      unknown: s.unknown + (known ? 0 : 1),
    }))
    setSaving(false)
    loadClue()
  }

  // Extract country name from clue title (format: "Country - Clue Type")
  const countryName = clue?.title?.includes(' - ')
    ? clue.title.split(' - ')[0]
    : null

  const isLoggedIn = !!localStorage.getItem('access_token')

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      {/* Header */}
      <div className="border-b border-gray-800 px-4 py-3 flex items-center justify-between">
        <Link to="/" className="text-blue-400 hover:text-blue-300 text-sm">← Übersicht</Link>
        <h1 className="text-lg font-semibold">🃏 Lernmodus</h1>
        <div className="flex items-center gap-3 text-sm">
          <span className="text-green-400">✓ {stats.known}</span>
          <span className="text-red-400">✗ {stats.unknown}</span>
        </div>
      </div>

      {/* Filter */}
      <div className="px-4 py-3 border-b border-gray-800 flex items-center gap-4 text-sm">
        {continentParam && (
          <span className="bg-blue-900 text-blue-300 px-3 py-1 rounded-full">
            📍 {continentParam}
          </span>
        )}
        {isLoggedIn && (
          <label className="flex items-center gap-2 text-gray-400 cursor-pointer">
            <input
              type="checkbox"
              checked={onlyUnknown}
              onChange={e => setOnlyUnknown(e.target.checked)}
              className="accent-blue-500"
            />
            Nur unbekannte Karten
          </label>
        )}
      </div>

      {/* Main Card */}
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-8">
        {loading ? (
          <div className="text-blue-400 text-lg">Lade Karte...</div>
        ) : error ? (
          <div className="text-center">
            <div className="text-gray-400 mb-4">{error}</div>
            <button
              onClick={loadClue}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm"
            >
              Nochmal versuchen
            </button>
          </div>
        ) : clue && (
          <div className="w-full max-w-2xl">
            {/* Image or placeholder */}
            {clue.image ? (
              <div className="mb-6 rounded-xl overflow-hidden">
                <img
                  src={clue.image}
                  alt="Hinweis"
                  className="w-full max-h-96 object-cover"
                />
              </div>
            ) : (
              <div className="mb-6 rounded-xl bg-gray-800 border border-gray-700 h-48 flex items-center justify-center">
                <span className="text-gray-600 text-sm">Kein Bild vorhanden</span>
              </div>
            )}

            {!revealed ? (
              <div className="text-center">
                <p className="text-gray-400 mb-6">Was siehst du hier? In welchem Land ist das?</p>
                <button
                  onClick={() => setRevealed(true)}
                  className="px-8 py-4 bg-blue-600 hover:bg-blue-500 rounded-xl text-lg font-semibold transition-colors"
                >
                  Aufdecken
                </button>
              </div>
            ) : (
              <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="mb-4">
                  {countryName && (
                    <div className="text-2xl font-bold text-white mb-1">{countryName}</div>
                  )}
                  <div className="text-xs text-blue-400 uppercase tracking-wider mb-1">
                    {CATEGORY_LABELS[clue.category] || clue.category}
                  </div>
                  <div className="text-lg font-semibold text-gray-200">{clue.title}</div>
                  <div className="text-yellow-400 text-sm mt-1">
                    {'★'.repeat(clue.importance)}
                    <span className="text-gray-600">{'★'.repeat(3 - clue.importance)}</span>
                    <span className="text-gray-400 ml-2">{clue.importance_display}</span>
                  </div>
                </div>
                <p className="text-gray-300 leading-relaxed mb-6">{clue.description}</p>

                {isLoggedIn ? (
                  <div className="flex gap-3">
                    <button
                      onClick={() => handleAnswer(false)}
                      disabled={saving}
                      className="flex-1 py-3 bg-red-900 hover:bg-red-800 border border-red-700 rounded-xl font-semibold transition-colors disabled:opacity-50"
                    >
                      ✗ Noch nicht
                    </button>
                    <button
                      onClick={() => handleAnswer(true)}
                      disabled={saving}
                      className="flex-1 py-3 bg-green-900 hover:bg-green-800 border border-green-700 rounded-xl font-semibold transition-colors disabled:opacity-50"
                    >
                      ✓ Kannte ich
                    </button>
                  </div>
                ) : (
                  <div className="text-center">
                    <button
                      onClick={loadClue}
                      className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-xl font-semibold transition-colors"
                    >
                      Nächste Karte →
                    </button>
                    <p className="text-gray-500 text-xs mt-2">
                      Einloggen um Fortschritt zu speichern
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
