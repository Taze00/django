import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { useLang } from '../LanguageContext'
import Header from '../Header'

const CATEGORIES = ['car', 'infrastructure', 'vegetation', 'signs', 'landscape', 'plates', 'language', 'other']

const CATEGORY_LABELS_DE = { car: '🚗 Fahrzeuge', infrastructure: '🏗️ Infrastruktur', vegetation: '🌿 Vegetation', signs: '🪧 Schilder', landscape: '🏔️ Landschaft', plates: '🔢 Nummernschilder', language: '🔤 Sprache', other: '📌 Sonstiges' }
const CATEGORY_LABELS_EN = { car: '🚗 Vehicles', infrastructure: '🏗️ Infrastructure', vegetation: '🌿 Vegetation', signs: '🪧 Signs', landscape: '🏔️ Landscape', plates: '🔢 License Plates', language: '🔤 Language', other: '📌 Other' }

const FORM_LABELS = {
  de: { title: 'Titel', titlePlaceholder: 'z.B. Gelbe Nummernschilder', category: 'Kategorie', description: 'Beschreibung', descPlaceholder: 'Warum ist das ein Hinweis?', caption: 'Bildunterschrift / Frage (optional)', captionPlaceholder: 'z.B. Wo wird MPH benutzt?', imageLabel: 'Bild hochladen', imageChange: 'Bild ändern', imageDrop: 'Bild hier hineinziehen oder einfügen (Strg+V)', save: 'Speichern', saving: 'Speichern...', cancel: 'Abbrechen', addClue: 'Clue hinzufügen' },
  en: { title: 'Title', titlePlaceholder: 'e.g. Yellow license plates', category: 'Category', description: 'Description', descPlaceholder: 'Why is this a clue?', caption: 'Caption / Question (optional)', captionPlaceholder: 'e.g. Where is MPH used?', imageLabel: 'Upload image', imageChange: 'Change image', imageDrop: 'Drop image here or paste (Ctrl+V)', save: 'Save', saving: 'Saving...', cancel: 'Cancel', addClue: 'Add clue' },
}

function flagUrl(val) {
  if (!val) return null
  if (val.codePointAt(0) >= 0x1F1E0) {
    const iso = [...val].map(c => String.fromCharCode(c.codePointAt(0) - 0x1F1E6 + 65)).join('').toLowerCase()
    return 'https://flagcdn.com/w80/' + iso + '.png'
  }
  return 'https://flagcdn.com/w80/' + val.toLowerCase() + '.png'
}

const EMPTY_FORM = { title: '', category: 'other', description: '', question: '' }

function ImageDropZone({ imagePreview, onFile, lang }) {
  const fileRef = useRef()
  const dropRef = useRef()
  const [dragging, setDragging] = useState(false)
  const lbl = FORM_LABELS[lang]

  function handleFile(file) {
    if (file && file.type.startsWith('image/')) onFile(file)
  }

  useEffect(() => {
    function onPaste(e) {
      const item = [...(e.clipboardData?.items || [])].find(i => i.type.startsWith('image/'))
      if (item) handleFile(item.getAsFile())
    }
    window.addEventListener('paste', onPaste)
    return () => window.removeEventListener('paste', onPaste)
  }, [])

  return (
    <div
      ref={dropRef}
      onDragOver={e => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={e => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]) }}
      onClick={() => fileRef.current.click()}
      className={`w-full rounded-xl border-2 border-dashed cursor-pointer transition-all flex flex-col items-center justify-center gap-2 ${
        dragging ? 'border-blue-500 bg-blue-900/20' : 'border-gray-700 hover:border-gray-500 bg-gray-800/50'
      } ${imagePreview ? 'p-2' : 'py-8'}`}
    >
      {imagePreview ? (
        <img src={imagePreview} alt="preview" className="w-full h-40 object-contain rounded-lg" />
      ) : (
        <span className="text-gray-500 text-sm text-center px-4">{lbl.imageDrop}</span>
      )}
      <span className="text-blue-400 text-xs hover:text-blue-300 transition-colors">
        {imagePreview ? lbl.imageChange : lbl.imageLabel}
      </span>
      <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={e => handleFile(e.target.files[0])} />
    </div>
  )
}

function ClueForm({ initial = EMPTY_FORM, onSave, onCancel, saving, lang }) {
  const [form, setForm] = useState({ ...EMPTY_FORM, ...initial })
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(initial.image || null)
  const lbl = FORM_LABELS[lang]
  const catLabels = lang === 'en' ? CATEGORY_LABELS_EN : CATEGORY_LABELS_DE

  function set(field, val) { setForm(f => ({ ...f, [field]: val })) }

  function handleFile(file) {
    setImageFile(file)
    setImagePreview(URL.createObjectURL(file))
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 flex flex-col gap-3">
      <input
        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:border-blue-500"
        placeholder={`${lbl.title} *`}
        value={form.title}
        onChange={e => set('title', e.target.value)}
      />
      <select
        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
        value={form.category}
        onChange={e => set('category', e.target.value)}
      >
        {CATEGORIES.map(c => <option key={c} value={c}>{catLabels[c]}</option>)}
      </select>
      <textarea
        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none"
        placeholder={lbl.descPlaceholder}
        rows={3}
        value={form.description}
        onChange={e => set('description', e.target.value)}
      />
      <input
        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:border-blue-500"
        placeholder={lbl.captionPlaceholder}
        value={form.question}
        onChange={e => set('question', e.target.value)}
      />
      <ImageDropZone imagePreview={imagePreview} onFile={handleFile} lang={lang} />
      <div className="flex gap-2">
        <button
          onClick={() => onSave(form, imageFile)}
          disabled={saving || !form.title.trim()}
          className="flex-1 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 rounded-lg text-sm font-semibold transition-colors"
        >
          {saving ? lbl.saving : lbl.save}
        </button>
        <button onClick={onCancel} className="px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-sm transition-colors">
          {lbl.cancel}
        </button>
      </div>
    </div>
  )
}

function ClueCard({ clue, catLabels, onEdit, onDelete }) {
  const [confirmDelete, setConfirmDelete] = useState(false)
  return (
    <div className="bg-gray-800 rounded-xl overflow-hidden border border-gray-700">
      {clue.image && <img src={clue.image} alt={clue.title} className="w-full max-h-64 object-contain bg-gray-900" />}
      {clue.question && !clue.image && (
        <div className="w-full bg-gray-700 flex items-center justify-center px-4 py-6">
          <p className="text-white font-semibold text-center">{clue.question}</p>
        </div>
      )}
      <div className="p-4">
        <div className="flex items-start justify-between gap-2 mb-1">
          <h3 className="font-semibold">{clue.title}</h3>
          <div className="flex gap-1 shrink-0">
            <button onClick={() => onEdit(clue)} className="p-1.5 text-gray-500 hover:text-blue-400 transition-colors rounded">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
            </button>
            {confirmDelete ? (
              <div className="flex gap-1">
                <button onClick={() => onDelete(clue.id)} className="px-2 py-1 bg-red-600 hover:bg-red-500 rounded text-xs font-semibold">
                  {clue.id ? '✓' : '?'}
                </button>
                <button onClick={() => setConfirmDelete(false)} className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs">✕</button>
              </div>
            ) : (
              <button onClick={() => setConfirmDelete(true)} className="p-1.5 text-gray-500 hover:text-red-400 transition-colors rounded">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
              </button>
            )}
          </div>
        </div>
        {clue.question && clue.image && <p className="text-blue-300 text-xs mb-1 italic">{clue.question}</p>}
        {clue.description && <p className="text-gray-400 text-sm leading-relaxed">{clue.description}</p>}
      </div>
    </div>
  )
}

export default function CountryView({ onLogout }) {
  const { continentSlug, countrySlug } = useParams()
  const { t, lang } = useLang()
  const [country, setCountry] = useState(null)
  const [clues, setClues] = useState([])
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [editingClue, setEditingClue] = useState(null)
  const [saving, setSaving] = useState(false)
  const catLabels = lang === 'en' ? CATEGORY_LABELS_EN : CATEGORY_LABELS_DE
  const lbl = FORM_LABELS[lang]

  useEffect(() => {
    Promise.all([
      api.getCountry(countrySlug).then(r => r.json()),
      api.getCountryCourses(countrySlug).then(r => r.json()).catch(() => []),
    ]).then(([countryData, coursesData]) => {
      setCountry(countryData)
      setClues(countryData.clues || [])
      setCourses(Array.isArray(coursesData) ? coursesData : (coursesData.results ?? []))
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [countrySlug])

  async function handleCreate(form, imageFile) {
    setSaving(true)
    try {
      const res = await api.createClue(countrySlug, form)
      const newClue = await res.json()
      if (imageFile) {
        const imgRes = await api.uploadClueImage(newClue.id, imageFile)
        const updated = await imgRes.json()
        setClues(cs => [...cs, updated])
      } else {
        setClues(cs => [...cs, newClue])
      }
      setShowAddForm(false)
    } finally {
      setSaving(false)
    }
  }

  async function handleUpdate(form, imageFile) {
    setSaving(true)
    try {
      const res = await api.updateClue(editingClue.id, form)
      let updated = await res.json()
      if (imageFile) {
        const imgRes = await api.uploadClueImage(updated.id, imageFile)
        updated = await imgRes.json()
      }
      setClues(cs => cs.map(c => c.id === updated.id ? updated : c))
      setEditingClue(null)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(clueId) {
    await api.deleteClue(clueId)
    setClues(cs => cs.filter(c => c.id !== clueId))
  }

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950">
      <div className="text-blue-400 text-lg">{t.loading}</div>
    </div>
  )
  if (!country) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950 text-gray-400">{t.countryNotFound}</div>
  )

  const flagImg = flagUrl(country.flag_emoji)
  const byCategory = clues.reduce((acc, clue) => {
    if (!acc[clue.category]) acc[clue.category] = []
    acc[clue.category].push(clue)
    return acc
  }, {})

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Header onLogout={onLogout} />
      <div className="w-full max-w-6xl mx-auto px-6 py-12 sm:py-16 sm:px-16">

        <div className="grid grid-cols-[2.25rem_1fr_2.25rem] items-center mb-10">
          <Link to={`/${continentSlug}`} className="inline-flex items-center justify-center w-9 h-9 text-gray-400 hover:text-white border border-gray-700 hover:border-gray-500 rounded-lg transition-all">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg>
          </Link>
          <div className="flex flex-col items-center gap-2">
            {flagImg && <img src={flagImg} alt={country.name} className="h-10 rounded shadow-lg" />}
            <h1 className="text-3xl font-bold text-center">{lang === 'de' && country.name_de ? country.name_de : country.name}</h1>
            <div className="flex items-center gap-3 text-sm text-gray-400">
              <span>{country.drive_side === 'left' ? (lang === 'en' ? 'Drive left' : 'Linksverkehr') : (lang === 'en' ? 'Drive right' : 'Rechtsverkehr')}</span>
              {country.domain && <span className="font-mono text-blue-400 text-xs">{country.domain}</span>}
            </div>
          </div>
        </div>

        {country.map_image && (
          <img src={country.map_image} alt={`Karte ${country.name}`} className="w-full h-56 object-contain mb-8" />
        )}
        {country.short_summary && <p className="text-gray-300 mb-8 leading-relaxed">{country.short_summary}</p>}

        {courses.length > 0 && (
          <div className="mb-8">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {courses.map(course => (
                <Link key={course.id} to={`/practice/course/${course.id}`}
                  className="bg-gray-900 hover:bg-gray-800 border border-gray-800 hover:border-blue-500 rounded-xl px-5 py-4 transition-all group flex items-center justify-between">
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

        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold">Clues <span className="text-gray-500 font-normal text-base">({clues.length})</span></h2>
          {!showAddForm && (
            <button
              onClick={() => { setShowAddForm(true); setEditingClue(null) }}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-semibold transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" /></svg>
              {lbl.addClue}
            </button>
          )}
        </div>

        {showAddForm && (
          <div className="mb-8">
            <ClueForm onSave={handleCreate} onCancel={() => setShowAddForm(false)} saving={saving} lang={lang} />
          </div>
        )}

        {clues.length === 0 && !showAddForm ? (
          <div className="text-gray-500 text-center py-16">{t.noClues}</div>
        ) : (
          Object.entries(byCategory).map(([category, catClues]) => (
            <div key={category} className="mb-10">
              <h2 className="text-lg font-semibold text-blue-400 mb-4 border-b border-gray-800 pb-2">
                {catLabels[category] || category}
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                {catClues.map(clue => (
                  editingClue?.id === clue.id ? (
                    <ClueForm key={clue.id} initial={editingClue} onSave={handleUpdate} onCancel={() => setEditingClue(null)} saving={saving} lang={lang} />
                  ) : (
                    <ClueCard key={clue.id} clue={clue} catLabels={catLabels} onEdit={c => { setEditingClue(c); setShowAddForm(false) }} onDelete={handleDelete} />
                  )
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
