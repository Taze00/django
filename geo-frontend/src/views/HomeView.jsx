import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useLang } from '../LanguageContext'
import Header from '../Header'

export default function HomeView({ onLogout }) {
  const { t, lang } = useLang()
  const [continents, setContinents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getContinents()
      .then(r => r.json())
      .then(data => { const list = data.results ?? data; setContinents(Array.isArray(list) ? list : []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950">
      <div className="text-blue-400 text-lg">{t.loading}</div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Header onLogout={onLogout} />

      <div className="max-w-6xl mx-auto px-4 sm:px-8 py-10">
        <div className="mb-10 bg-gray-900 border border-gray-800 rounded-2xl p-8 flex flex-col sm:flex-row items-center gap-6">
          <div className="flex-1">
            <h2 className="text-2xl font-bold mb-2">{t.learnTitle}</h2>
            <p className="text-gray-400 text-sm">{t.learnSubtitle}</p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3 shrink-0">
            <Link to="/courses" className="px-8 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-semibold transition-colors min-w-[11rem] text-center">
              {t.selectCourse}
            </Link>
            <Link to="/create-course" className="px-8 py-3 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-xl font-semibold transition-colors min-w-[11rem] text-center text-gray-300">
              {lang === 'en' ? '+ Create course' : '+ Kurs erstellen'}
            </Link>
            <Link to="/my-courses" className="px-8 py-3 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-xl font-semibold transition-colors min-w-[11rem] text-center text-gray-300">
              {lang === 'en' ? 'My courses' : 'Meine Kurse'}
            </Link>
          </div>
        </div>

        {continents.length === 0 ? (
          <div className="text-gray-500 text-center py-20">{t.noContinents}</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {continents.map(continent => (
              <Link key={continent.slug} to={`/${continent.slug}`}
                className="group relative rounded-xl overflow-hidden bg-gray-800 hover:bg-gray-700 transition-all border border-gray-700 hover:border-blue-500">
                {continent.cover_image ? (
                  <img src={continent.cover_image} alt={continent.name} className="w-full h-40 object-contain opacity-60 group-hover:opacity-80 transition-opacity" />
                ) : (
                  <div className="w-full h-40 bg-gradient-to-br from-blue-900 to-gray-800 flex items-center justify-center">
                    <span className="text-5xl">🌐</span>
                  </div>
                )}
                <div className="p-4">
                  <h2 className="text-xl font-bold mb-1">{lang === 'de' && continent.name_de ? continent.name_de : continent.name}</h2>
                  <div className="flex items-center gap-3 text-sm text-gray-500 mt-2">
                    <span>{continent.country_count} {t.countries}</span>
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
