import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useLang } from '../LanguageContext'
import Header from '../Header'

const LABELS = {
  de: {
    title: 'Kurs erstellen',
    courseName: 'Kursname *',
    courseNamePh: 'z.B. Indonesien Clues',
    description: 'Beschreibung',
    descPh: 'Kurze Beschreibung...',
    courseContinent: 'Kontinent des Kurses (optional)',
    general: 'Allgemein',
    selectedClues: 'Ausgewählte Clues',
    noneSelected: 'Noch keine Clues ausgewählt — rechts filtern',
    removeAll: 'Alle entfernen',
    createBtn: (n) => `Kurs erstellen (${n} Clues)`,
    saving: 'Speichern...',
    filterContinent: 'Nach Kontinent filtern',
    allContinents: 'Alle Kontinente',
    searchLabel: 'Nach Land oder Titel suchen',
    searchPh: 'z.B. Bollard, Indonesia...',
    searching: 'Suche...',
    noClues: 'Keine Clues gefunden',
    browseHint: 'Kontinent wählen oder suchen um Clues zu sehen',
  },
  en: {
    title: 'Create course',
    courseName: 'Course name *',
    courseNamePh: 'e.g. Indonesia Clues',
    description: 'Description',
    descPh: 'Short description...',
    courseContinent: 'Course continent (optional)',
    general: 'General',
    selectedClues: 'Selected clues',
    noneSelected: 'No clues selected yet — filter on the right',
    removeAll: 'Remove all',
    createBtn: (n) => `Create course (${n} clues)`,
    saving: 'Saving...',
    filterContinent: 'Filter by continent',
    allContinents: 'All continents',
    searchLabel: 'Search by country or title',
    searchPh: 'e.g. Bollard, Indonesia...',
    searching: 'Searching...',
    noClues: 'No clues found',
    browseHint: 'Select a continent or search to see clues',
  },
}

export default function CourseBuilderView({ onLogout }) {
  const navigate = useNavigate()
  const { lang } = useLang()
  const lbl = LABELS[lang]

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [courseContinent, setCourseContinent] = useState('')
  const [selectedClues, setSelectedClues] = useState([])

  const [filterContinent, setFilterContinent] = useState('')
  const [searchQ, setSearchQ] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  const [saving, setSaving] = useState(false)
  const [continents, setContinents] = useState([])

  useEffect(() => {
    api.getContinents().then(r => r.json()).then(data => {
      setContinents(Array.isArray(data) ? data : (data.results ?? []))
    }).catch(() => {})
  }, [])

  // Trigger search when continent filter changes or search query changes
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!filterContinent && searchQ.trim().length < 1) {
        setSearchResults([])
        setHasSearched(false)
        return
      }
      setSearching(true)
      setHasSearched(true)
      api.searchClues(searchQ, '', filterContinent)
        .then(r => r.json())
        .then(data => { setSearchResults(Array.isArray(data) ? data : []); setSearching(false) })
        .catch(() => setSearching(false))
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQ, filterContinent])

  function toggleClue(clue) {
    setSelectedClues(cs =>
      cs.find(c => c.id === clue.id) ? cs.filter(c => c.id !== clue.id) : [...cs, clue]
    )
  }

  async function handleSave() {
    if (!name.trim() || selectedClues.length === 0) return
    setSaving(true)
    try {
      const cont = continents.find(c => c.slug === courseContinent)
      const res = await api.createCourse({
        name: name.trim(),
        description: description.trim(),
        continent_id: cont?.id || null,
        clue_ids: selectedClues.map(c => c.id),
      })
      const data = await res.json()
      navigate(`/practice/course/${data.id}`)
    } finally {
      setSaving(false)
    }
  }

  const selectedIds = new Set(selectedClues.map(c => c.id))

  function continentName(c) {
    return lang === 'de' && c.name_de ? c.name_de : c.name
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Header onLogout={onLogout} />
      <div className="w-full max-w-6xl mx-auto px-6 py-12 sm:py-16 sm:px-16">
        <h1 className="text-3xl font-bold text-center mb-10">{lbl.title}</h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

          {/* Left: course settings + selected clues */}
          <div className="flex flex-col gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">{lbl.courseName}</label>
              <input
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                placeholder={lbl.courseNamePh}
                value={name}
                onChange={e => setName(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">{lbl.description}</label>
              <textarea
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none"
                placeholder={lbl.descPh}
                rows={2}
                value={description}
                onChange={e => setDescription(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">{lbl.courseContinent}</label>
              <select
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white focus:outline-none focus:border-blue-500"
                value={courseContinent}
                onChange={e => setCourseContinent(e.target.value)}
              >
                <option value="">{lbl.general}</option>
                {continents.map(c => (
                  <option key={c.slug} value={c.slug}>{continentName(c)}</option>
                ))}
              </select>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm text-gray-400">{lbl.selectedClues} ({selectedClues.length})</label>
                {selectedClues.length > 0 && (
                  <button onClick={() => setSelectedClues([])} className="text-xs text-gray-500 hover:text-red-400 transition-colors">{lbl.removeAll}</button>
                )}
              </div>
              {selectedClues.length === 0 ? (
                <div className="text-gray-600 text-sm py-4 text-center border border-dashed border-gray-800 rounded-xl">
                  {lbl.noneSelected}
                </div>
              ) : (
                <div className="flex flex-col gap-2 max-h-72 overflow-y-auto pr-1">
                  {selectedClues.map(clue => (
                    <div key={clue.id} className="flex items-center gap-3 bg-gray-800 rounded-lg px-3 py-2">
                      {clue.image
                        ? <img src={clue.image} alt="" className="w-10 h-10 object-contain bg-gray-700 rounded shrink-0" />
                        : <div className="w-10 h-10 bg-gray-700 rounded flex items-center justify-center shrink-0 text-gray-500 text-xs">{clue.question ? '?' : '📷'}</div>
                      }
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-semibold truncate">{clue.title}</div>
                        <div className="text-xs text-gray-500 truncate">{clue.country_name}</div>
                      </div>
                      <button onClick={() => toggleClue(clue)} className="text-gray-600 hover:text-red-400 transition-colors shrink-0">
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={handleSave}
              disabled={saving || !name.trim() || selectedClues.length === 0}
              className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 rounded-xl font-semibold transition-colors"
            >
              {saving ? lbl.saving : lbl.createBtn(selectedClues.length)}
            </button>
          </div>

          {/* Right: filter + clue list */}
          <div className="flex flex-col gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">{lbl.filterContinent}</label>
              <select
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white focus:outline-none focus:border-blue-500"
                value={filterContinent}
                onChange={e => setFilterContinent(e.target.value)}
              >
                <option value="">{lbl.allContinents}</option>
                {continents.map(c => (
                  <option key={c.slug} value={c.slug}>{continentName(c)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">{lbl.searchLabel}</label>
              <input
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                placeholder={lbl.searchPh}
                value={searchQ}
                onChange={e => setSearchQ(e.target.value)}
              />
            </div>

            <div className="flex flex-col gap-2 max-h-[28rem] overflow-y-auto pr-1">
              {searching && <div className="text-gray-500 text-sm text-center py-4">{lbl.searching}</div>}
              {!searching && !hasSearched && (
                <div className="text-gray-600 text-sm text-center py-8">{lbl.browseHint}</div>
              )}
              {!searching && hasSearched && searchResults.length === 0 && (
                <div className="text-gray-600 text-sm text-center py-4">{lbl.noClues}</div>
              )}
              {searchResults.map(clue => {
                const selected = selectedIds.has(clue.id)
                return (
                  <button
                    key={clue.id}
                    onClick={() => toggleClue(clue)}
                    className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-all border ${
                      selected ? 'bg-blue-900/40 border-blue-600' : 'bg-gray-800 border-gray-700 hover:border-gray-500'
                    }`}
                  >
                    {clue.image
                      ? <img src={clue.image} alt="" className="w-12 h-12 object-contain bg-gray-700 rounded shrink-0" />
                      : <div className="w-12 h-12 bg-gray-700 rounded flex items-center justify-center shrink-0 text-gray-500 text-lg">{clue.question ? '?' : '📷'}</div>
                    }
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-semibold truncate">{clue.title}</div>
                      <div className="text-xs text-gray-500 truncate">{clue.country_name}</div>
                      {clue.question && <div className="text-xs text-blue-400 truncate mt-0.5">{clue.question}</div>}
                    </div>
                    <div className={`w-5 h-5 rounded-full border-2 shrink-0 flex items-center justify-center transition-colors ${
                      selected ? 'bg-blue-600 border-blue-600' : 'border-gray-600'
                    }`}>
                      {selected && (
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                      )}
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
