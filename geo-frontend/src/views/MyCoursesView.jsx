import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useLang } from '../LanguageContext'
import Header from '../Header'

const LABELS = {
  de: {
    title: 'Meine Kurse',
    empty: 'Du hast noch keine Kurse erstellt.',
    createBtn: '+ Kurs erstellen',
    clues: (n) => `${n} Clues`,
    play: 'Spielen',
    edit: 'Bearbeiten',
    delete: 'Löschen',
    confirmDelete: 'Wirklich löschen?',
    yes: 'Ja, löschen',
    no: 'Abbrechen',
    editName: 'Name',
    editDesc: 'Beschreibung',
    save: 'Speichern',
    saving: 'Speichern...',
    cancel: 'Abbrechen',
  },
  en: {
    title: 'My courses',
    empty: 'You have not created any courses yet.',
    createBtn: '+ Create course',
    clues: (n) => `${n} clues`,
    play: 'Play',
    edit: 'Edit',
    delete: 'Delete',
    confirmDelete: 'Really delete?',
    yes: 'Yes, delete',
    no: 'Cancel',
    editName: 'Name',
    editDesc: 'Description',
    save: 'Save',
    saving: 'Saving...',
    cancel: 'Cancel',
  },
}

function CourseRow({ course, lbl, onDeleted, onUpdated }) {
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editName, setEditName] = useState(course.name)
  const [editDesc, setEditDesc] = useState(course.description)
  const [saving, setSaving] = useState(false)

  async function handleDelete() {
    await api.deleteCourse(course.id)
    onDeleted(course.id)
  }

  async function handleSave() {
    setSaving(true)
    try {
      await api.updateCourse(course.id, { name: editName.trim(), description: editDesc.trim() })
      onUpdated({ ...course, name: editName.trim(), description: editDesc.trim() })
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  if (editing) {
    return (
      <div className="bg-gray-900 border border-blue-600 rounded-xl p-4 flex flex-col gap-3">
        <input
          className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
          value={editName}
          onChange={e => setEditName(e.target.value)}
          placeholder={lbl.editName}
        />
        <textarea
          className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500 resize-none"
          value={editDesc}
          onChange={e => setEditDesc(e.target.value)}
          placeholder={lbl.editDesc}
          rows={3}
        />
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            disabled={saving || !editName.trim()}
            className="flex-1 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 rounded-lg text-sm font-semibold transition-colors"
          >
            {saving ? lbl.saving : lbl.save}
          </button>
          <button
            onClick={() => setEditing(false)}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-sm transition-colors"
          >
            {lbl.cancel}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl px-5 py-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-white text-lg truncate">{course.name}</div>
          <div className="text-xs text-gray-500 mt-0.5">{lbl.clues(course.clue_count)}</div>
          {course.description && (
            <p className="text-gray-400 text-sm mt-1 line-clamp-2">{course.description}</p>
          )}
        </div>
        <div className="flex gap-2 shrink-0">
          <button
            onClick={() => setEditing(true)}
            className="p-1.5 text-gray-500 hover:text-blue-400 transition-colors rounded"
            title={lbl.edit}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
          </button>
          {confirmDelete ? (
            <div className="flex items-center gap-1">
              <button onClick={handleDelete} className="px-2 py-1 bg-red-600 hover:bg-red-500 rounded text-xs font-semibold transition-colors">{lbl.yes}</button>
              <button onClick={() => setConfirmDelete(false)} className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs transition-colors">{lbl.no}</button>
            </div>
          ) : (
            <button
              onClick={() => setConfirmDelete(true)}
              className="p-1.5 text-gray-500 hover:text-red-400 transition-colors rounded"
              title={lbl.delete}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
            </button>
          )}
        </div>
      </div>
      <Link
        to={`/practice/course/${course.id}`}
        className="w-full py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-semibold text-center transition-colors"
      >
        {lbl.play}
      </Link>
    </div>
  )
}

export default function MyCoursesView({ onLogout }) {
  const { lang } = useLang()
  const lbl = LABELS[lang]
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getMyCourses()
      .then(r => r.json())
      .then(data => { setCourses(Array.isArray(data) ? data : []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950">
      <div className="text-blue-400 text-lg">...</div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Header onLogout={onLogout} />
      <div className="w-full max-w-3xl mx-auto px-6 py-12 sm:py-16 sm:px-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">{lbl.title}</h1>
          <Link
            to="/create-course"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-xl text-sm font-semibold transition-colors"
          >
            {lbl.createBtn}
          </Link>
        </div>

        {courses.length === 0 ? (
          <div className="text-gray-500 text-center py-20 flex flex-col items-center gap-4">
            <span>{lbl.empty}</span>
            <Link to="/create-course" className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-semibold transition-colors text-white">
              {lbl.createBtn}
            </Link>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {courses.map(course => (
              <CourseRow
                key={course.id}
                course={course}
                lbl={lbl}
                onDeleted={id => setCourses(cs => cs.filter(c => c.id !== id))}
                onUpdated={updated => setCourses(cs => cs.map(c => c.id === updated.id ? updated : c))}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
