import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useLang } from '../LanguageContext'
import Header from '../Header'

const LABELS = {
  de: {
    title: 'Kurs erstellen',
    step1: '01 — Kurs benennen',
    step2: '02 — Clues auswählen',
    step3: '03 — Speichern',
    courseName: 'Kursname',
    courseNamePh: 'z.B. Indonesien Clues',
    description: 'Beschreibung (optional)',
    descPh: 'Kurze Beschreibung...',
    courseContinent: 'Kontinent (optional)',
    general: 'Allgemein',
    selectedClues: 'Ausgewählt',
    noneSelected: 'Noch keine Clues ausgewählt',
    noneSelectedHint: 'Wähle rechts Clues aus',
    removeAll: 'Alle entfernen',
    createBtn: (n) => `Kurs erstellen — ${n} Clues`,
    saving: 'Speichern...',
    filterContinent: 'Kontinent',
    allContinents: 'Alle',
    searchLabel: 'Suche',
    searchPh: 'z.B. Bollard, Indonesien...',
    searching: 'Suche...',
    noClues: 'Keine Clues gefunden',
    browseHint: 'Kontinent wählen oder suchen',
    available: 'Verfügbare Clues',
    missingName: 'Bitte einen Kursname angeben.',
    missingClues: 'Bitte mindestens einen Clue auswählen.',
  },
  en: {
    title: 'Create course',
    step1: '01 — Name your course',
    step2: '02 — Select clues',
    step3: '03 — Save',
    courseName: 'Course name',
    courseNamePh: 'e.g. Indonesia Clues',
    description: 'Description (optional)',
    descPh: 'Short description...',
    courseContinent: 'Continent (optional)',
    general: 'General',
    selectedClues: 'Selected',
    noneSelected: 'No clues selected yet',
    noneSelectedHint: 'Pick clues on the right',
    removeAll: 'Remove all',
    createBtn: (n) => `Create course — ${n} clues`,
    saving: 'Saving...',
    filterContinent: 'Continent',
    allContinents: 'All',
    searchLabel: 'Search',
    searchPh: 'e.g. Bollard, Indonesia...',
    searching: 'Searching...',
    noClues: 'No clues found',
    browseHint: 'Select a continent or search',
    available: 'Available clues',
    missingName: 'Please enter a course name.',
    missingClues: 'Please select at least one clue.',
  },
}

function inputStyle(focused) {
  return {
    background: 'var(--ink)',
    border: `1px solid ${focused ? 'var(--gold)' : 'var(--line-strong)'}`,
    color: 'var(--text)',
    padding: '10px 14px',
    fontSize: '14px',
    fontFamily: 'inherit',
    width: '100%',
    outline: 'none',
    transition: 'border-color 0.15s',
  }
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
  const [error, setError] = useState('')
  const [continents, setContinents] = useState([])

  const [nameFocused, setNameFocused] = useState(false)
  const [descFocused, setDescFocused] = useState(false)
  const [searchFocused, setSearchFocused] = useState(false)

  useEffect(() => {
    api.getContinents().then(r => r.json()).then(data => {
      setContinents(Array.isArray(data) ? data : (data.results ?? []))
    }).catch(() => {})
  }, [])

  useEffect(() => {
    const timer = setTimeout(() => {
      if (!filterContinent && searchQ.trim().length < 1) {
        setSearchResults([]); setHasSearched(false); return
      }
      setSearching(true); setHasSearched(true)
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
    if (!name.trim()) { setError(lbl.missingName); return }
    if (selectedClues.length === 0) { setError(lbl.missingClues); return }
    setError('')
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

  const selectStyle = {
    background: 'var(--ink)', border: '1px solid var(--line-strong)',
    color: 'var(--text)', padding: '10px 14px', fontSize: '13px',
    fontFamily: "'DM Mono', monospace", width: '100%', outline: 'none',
  }

  return (
    <div className="min-h-screen cart-bg" style={{background:'var(--ink)'}}>
      <Header onLogout={onLogout} />

      {/* Page header */}
      <div className="relative" style={{borderBottom:'1px solid var(--line)'}}>
        <div className="max-w-7xl mx-auto px-5 sm:px-10 py-10 anim-0">
          <div className="flex items-center gap-3 mb-2">
            <div className="h-px w-6" style={{background:'var(--gold)'}} />
            <span className="font-code text-xs uppercase tracking-widest" style={{color:'var(--gold)'}}>
              {lang === 'en' ? 'Course Builder' : 'Kurs-Editor'}
            </span>
          </div>
          <h1 className="font-display text-4xl sm:text-5xl font-black" style={{color:'var(--text)'}}>
            {lbl.title}
          </h1>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-5 sm:px-10 py-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-px" style={{background:'var(--line)'}}>

          {/* ── Left: Settings + Selected ── */}
          <div className="flex flex-col gap-0" style={{background:'var(--ink-soft)'}}>

            {/* Step 1 */}
            <div className="p-6 pb-5" style={{borderBottom:'1px solid var(--line)'}}>
              <div className="font-code text-xs uppercase tracking-widest mb-5" style={{color:'var(--gold)'}}>
                {lbl.step1}
              </div>
              <div className="flex flex-col gap-4">
                <div>
                  <label className="block font-code text-xs uppercase tracking-widest mb-2" style={{color:'var(--muted)'}}>{lbl.courseName}</label>
                  <input
                    style={inputStyle(nameFocused)}
                    placeholder={lbl.courseNamePh}
                    value={name}
                    onChange={e => setName(e.target.value)}
                    onFocus={() => setNameFocused(true)}
                    onBlur={() => setNameFocused(false)}
                  />
                </div>
                <div>
                  <label className="block font-code text-xs uppercase tracking-widest mb-2" style={{color:'var(--muted)'}}>{lbl.description}</label>
                  <textarea
                    style={{...inputStyle(descFocused), resize:'none'}}
                    placeholder={lbl.descPh}
                    rows={2}
                    value={description}
                    onChange={e => setDescription(e.target.value)}
                    onFocus={() => setDescFocused(true)}
                    onBlur={() => setDescFocused(false)}
                  />
                </div>
                <div>
                  <label className="block font-code text-xs uppercase tracking-widest mb-2" style={{color:'var(--muted)'}}>{lbl.courseContinent}</label>
                  <select style={selectStyle} value={courseContinent} onChange={e => setCourseContinent(e.target.value)}>
                    <option value="">{lbl.general}</option>
                    {continents.map(c => <option key={c.slug} value={c.slug}>{continentName(c)}</option>)}
                  </select>
                </div>
              </div>
            </div>

            {/* Step 2 — selected clues */}
            <div className="p-6 flex-1" style={{borderBottom:'1px solid var(--line)'}}>
              <div className="flex items-center justify-between mb-5">
                <div className="font-code text-xs uppercase tracking-widest" style={{color:'var(--gold)'}}>
                  {lbl.step2}
                  {selectedClues.length > 0 && (
                    <span className="ml-2 px-2 py-0.5 text-xs" style={{background:'rgba(212,168,75,0.15)', color:'var(--gold)'}}>
                      {selectedClues.length}
                    </span>
                  )}
                </div>
                {selectedClues.length > 0 && (
                  <button
                    onClick={() => setSelectedClues([])}
                    className="font-code text-xs transition-colors"
                    style={{color:'var(--muted)'}}
                    onMouseEnter={e => e.currentTarget.style.color='#e05a5a'}
                    onMouseLeave={e => e.currentTarget.style.color='var(--muted)'}
                  >
                    {lbl.removeAll}
                  </button>
                )}
              </div>

              {selectedClues.length === 0 ? (
                <div className="border border-dashed py-10 text-center" style={{borderColor:'var(--line-strong)'}}>
                  <div className="font-code text-sm" style={{color:'var(--muted)'}}>{lbl.noneSelected}</div>
                  <div className="font-code text-xs mt-1" style={{color:'var(--line-strong)'}}>{lbl.noneSelectedHint}</div>
                </div>
              ) : (
                <div className="flex flex-col gap-px max-h-72 overflow-y-auto" style={{background:'var(--line)'}}>
                  {selectedClues.map(clue => (
                    <div key={clue.id}
                      className="flex items-center gap-3 px-3 py-2.5"
                      style={{background:'var(--ink-soft)'}}
                    >
                      {clue.image
                        ? <img src={clue.image} alt="" className="w-9 h-9 object-contain shrink-0" style={{background:'var(--ink)'}} />
                        : <div className="w-9 h-9 shrink-0 flex items-center justify-center font-code text-xs" style={{background:'var(--ink)', color:'var(--muted)'}}>?</div>
                      }
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-semibold truncate" style={{color:'var(--text)'}}>{clue.title}</div>
                        <div className="font-code text-xs truncate" style={{color:'var(--muted)'}}>{clue.country_name}</div>
                      </div>
                      <button
                        onClick={() => toggleClue(clue)}
                        className="shrink-0 transition-colors p-1"
                        style={{color:'var(--muted)'}}
                        onMouseEnter={e => e.currentTarget.style.color='#e05a5a'}
                        onMouseLeave={e => e.currentTarget.style.color='var(--muted)'}
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Step 3 — save */}
            <div className="p-6">
              <div className="font-code text-xs uppercase tracking-widest mb-5" style={{color:'var(--gold)'}}>
                {lbl.step3}
              </div>
              {error && (
                <div className="font-code text-xs mb-4 px-3 py-2" style={{background:'rgba(224,90,90,0.1)', color:'#e05a5a', border:'1px solid rgba(224,90,90,0.3)'}}>
                  {error}
                </div>
              )}
              <button
                onClick={handleSave}
                disabled={saving}
                className="w-full py-3.5 font-semibold text-sm tracking-wide transition-all"
                style={{
                  background: saving ? 'rgba(212,168,75,0.2)' : 'var(--gold)',
                  color: saving ? 'var(--gold)' : 'var(--ink)',
                  opacity: saving ? 0.7 : 1,
                  fontFamily: "'DM Mono', monospace",
                }}
              >
                {saving ? lbl.saving : lbl.createBtn(selectedClues.length)}
              </button>
            </div>
          </div>

          {/* ── Right: Browse + select clues ── */}
          <div className="flex flex-col" style={{background:'var(--ink-soft)'}}>
            <div className="p-6" style={{borderBottom:'1px solid var(--line)'}}>
              <div className="font-code text-xs uppercase tracking-widest mb-5" style={{color:'var(--gold)'}}>
                {lbl.available}
              </div>
              <div className="flex flex-col gap-3">
                <div>
                  <label className="block font-code text-xs uppercase tracking-widest mb-2" style={{color:'var(--muted)'}}>{lbl.filterContinent}</label>
                  <select style={selectStyle} value={filterContinent} onChange={e => setFilterContinent(e.target.value)}>
                    <option value="">{lbl.allContinents}</option>
                    {continents.map(c => <option key={c.slug} value={c.slug}>{continentName(c)}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block font-code text-xs uppercase tracking-widest mb-2" style={{color:'var(--muted)'}}>{lbl.searchLabel}</label>
                  <div className="relative">
                    <svg xmlns="http://www.w3.org/2000/svg" className="absolute left-3.5 top-1/2 -translate-y-1/2 w-3 h-3" style={{color:'var(--muted)'}} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
                    </svg>
                    <input
                      style={{...inputStyle(searchFocused), paddingLeft:'32px'}}
                      placeholder={lbl.searchPh}
                      value={searchQ}
                      onChange={e => setSearchQ(e.target.value)}
                      onFocus={() => setSearchFocused(true)}
                      onBlur={() => setSearchFocused(false)}
                    />
                    {searching && (
                      <div className="absolute right-3 top-1/2 -translate-y-1/2 w-3 h-3 border border-t-transparent rounded-full animate-spin" style={{borderColor:'var(--gold)'}} />
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Clue list */}
            <div className="flex-1 overflow-y-auto" style={{maxHeight:'28rem'}}>
              {!hasSearched && (
                <div className="py-16 text-center">
                  <div className="font-code text-xs" style={{color:'var(--muted)'}}>{lbl.browseHint}</div>
                </div>
              )}
              {hasSearched && !searching && searchResults.length === 0 && (
                <div className="py-16 text-center">
                  <div className="font-code text-xs" style={{color:'var(--muted)'}}>{lbl.noClues}</div>
                </div>
              )}
              {searchResults.length > 0 && (
                <div className="flex flex-col gap-px" style={{background:'var(--line)'}}>
                  {searchResults.map(clue => {
                    const selected = selectedIds.has(clue.id)
                    return (
                      <button
                        key={clue.id}
                        onClick={() => toggleClue(clue)}
                        className="flex items-center gap-3 px-4 py-3 text-left w-full transition-colors"
                        style={{background: selected ? 'rgba(212,168,75,0.07)' : 'var(--ink-soft)'}}
                        onMouseEnter={e => { if (!selected) e.currentTarget.style.background='var(--ink-raised)' }}
                        onMouseLeave={e => { if (!selected) e.currentTarget.style.background='var(--ink-soft)' }}
                      >
                        {clue.image
                          ? <img src={clue.image} alt="" className="w-11 h-11 object-contain shrink-0" style={{background:'var(--ink)'}} />
                          : <div className="w-11 h-11 shrink-0 flex items-center justify-center font-code text-xs" style={{background:'var(--ink)', color:'var(--muted)'}}>?</div>
                        }
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-semibold truncate" style={{color:'var(--text)'}}>{clue.title}</div>
                          <div className="font-code text-xs truncate mt-0.5" style={{color:'var(--muted)'}}>{clue.country_name}</div>
                          {clue.question && <div className="font-code text-xs truncate mt-0.5" style={{color:'var(--accent)'}}>{clue.question}</div>}
                        </div>
                        <div
                          className="shrink-0 w-5 h-5 flex items-center justify-center transition-all"
                          style={{
                            border: `1.5px solid ${selected ? 'var(--gold)' : 'var(--line-strong)'}`,
                            background: selected ? 'var(--gold)' : 'transparent',
                          }}
                        >
                          {selected && (
                            <svg className="w-3 h-3" style={{color:'var(--ink)'}} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                        </div>
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
