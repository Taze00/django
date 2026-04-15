import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useLang } from '../LanguageContext'
import Header from '../Header'

const LABELS = {
  de: {
    title: 'Meine Kurse',
    subtitle: 'Kurse die du erstellt hast',
    empty: 'Du hast noch keine Kurse erstellt.',
    createBtn: 'Kurs erstellen',
    clues: (n) => `${n} Clues`,
    play: 'Training starten',
    edit: 'Bearbeiten',
    delete: 'Löschen',
    confirmDelete: 'Wirklich löschen?',
    yes: 'Löschen',
    no: 'Abbrechen',
    editName: 'Name',
    editDesc: 'Beschreibung',
    save: 'Speichern',
    saving: 'Speichern...',
    cancel: 'Abbrechen',
  },
  en: {
    title: 'My courses',
    subtitle: 'Courses you have created',
    empty: 'You have not created any courses yet.',
    createBtn: 'Create course',
    clues: (n) => `${n} clues`,
    play: 'Start training',
    edit: 'Edit',
    delete: 'Delete',
    confirmDelete: 'Really delete?',
    yes: 'Delete',
    no: 'Cancel',
    editName: 'Name',
    editDesc: 'Description',
    save: 'Save',
    saving: 'Saving...',
    cancel: 'Cancel',
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

function CourseRow({ course, lbl, onDeleted, onUpdated }) {
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editName, setEditName] = useState(course.name)
  const [editDesc, setEditDesc] = useState(course.description || '')
  const [saving, setSaving] = useState(false)
  const [nameFocused, setNameFocused] = useState(false)
  const [descFocused, setDescFocused] = useState(false)

  const learned = course.learned_count ?? 0
  const total = course.total_count ?? course.clue_count ?? 0
  const pct = total > 0 ? Math.round((learned / total) * 100) : 0
  const done = learned >= total && total > 0

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
      <div className="p-5 flex flex-col gap-4" style={{background:'var(--ink-soft)', borderLeft:'2px solid var(--gold)', border:'1px solid rgba(212,168,75,0.3)', borderLeft:'2px solid var(--gold)'}}>
        <div>
          <label className="block font-code text-xs uppercase tracking-widest mb-2" style={{color:'var(--muted)'}}>{lbl.editName}</label>
          <input
            style={inputStyle(nameFocused)}
            value={editName}
            onChange={e => setEditName(e.target.value)}
            onFocus={() => setNameFocused(true)}
            onBlur={() => setNameFocused(false)}
          />
        </div>
        <div>
          <label className="block font-code text-xs uppercase tracking-widest mb-2" style={{color:'var(--muted)'}}>{lbl.editDesc}</label>
          <textarea
            style={{...inputStyle(descFocused), resize:'none'}}
            value={editDesc}
            onChange={e => setEditDesc(e.target.value)}
            onFocus={() => setDescFocused(true)}
            onBlur={() => setDescFocused(false)}
            rows={3}
          />
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleSave}
            disabled={saving || !editName.trim()}
            className="flex-1 py-2.5 text-sm font-semibold transition-all font-code"
            style={{
              background: 'var(--gold)', color: 'var(--ink)',
              opacity: (saving || !editName.trim()) ? 0.5 : 1,
            }}
          >
            {saving ? lbl.saving : lbl.save}
          </button>
          <button
            onClick={() => setEditing(false)}
            className="px-5 py-2.5 text-sm font-code transition-colors"
            style={{border:'1px solid var(--line-strong)', color:'var(--muted)'}}
            onMouseEnter={e => e.currentTarget.style.color='var(--text)'}
            onMouseLeave={e => e.currentTarget.style.color='var(--muted)'}
          >
            {lbl.cancel}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div
      className="flex flex-col gap-4 p-5 transition-colors"
      style={{
        background:'var(--ink-soft)',
        border:'1px solid var(--line)',
        borderLeft:`2px solid ${done ? '#5a9e6f' : 'var(--accent)'}`,
      }}
    >
      {/* Top row: title + actions */}
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="font-display font-bold text-lg leading-tight" style={{color: done ? '#5a9e6f' : 'var(--text)'}}>
            {course.name}
          </div>
          <div className="flex items-center gap-2 mt-1">
            <span className="font-code text-xs" style={{color:'var(--muted)'}}>
              {lbl.clues(course.clue_count ?? 0)}
            </span>
            {total > 0 && (
              <>
                <span style={{color:'var(--line-strong)'}}>·</span>
                <span className="font-code text-xs tabular-nums" style={{color: done ? '#5a9e6f' : 'var(--gold)'}}>
                  {done ? '✓' : `${pct}%`}
                </span>
              </>
            )}
          </div>
          {course.description && (
            <p className="text-sm mt-2 line-clamp-2" style={{color:'var(--muted)'}}>{course.description}</p>
          )}
        </div>

        {/* Action icons */}
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={() => setEditing(true)}
            className="p-2 transition-colors"
            style={{color:'var(--muted)'}}
            onMouseEnter={e => e.currentTarget.style.color='var(--text)'}
            onMouseLeave={e => e.currentTarget.style.color='var(--muted)'}
            title={lbl.edit}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          {confirmDelete ? (
            <div className="flex items-center gap-1.5 ml-1">
              <span className="font-code text-xs" style={{color:'var(--muted)'}}>{lbl.confirmDelete}</span>
              <button
                onClick={handleDelete}
                className="px-2.5 py-1 font-code text-xs transition-colors"
                style={{background:'rgba(224,90,90,0.15)', color:'#e05a5a', border:'1px solid rgba(224,90,90,0.3)'}}
              >
                {lbl.yes}
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="px-2.5 py-1 font-code text-xs transition-colors"
                style={{color:'var(--muted)', border:'1px solid var(--line-strong)'}}
              >
                {lbl.no}
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirmDelete(true)}
              className="p-2 transition-colors"
              style={{color:'var(--muted)'}}
              onMouseEnter={e => e.currentTarget.style.color='#e05a5a'}
              onMouseLeave={e => e.currentTarget.style.color='var(--muted)'}
              title={lbl.delete}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Progress line */}
      {total > 0 && (
        <div className="relative h-px w-full" style={{background:'var(--line-strong)'}}>
          <div style={{
            position:'absolute', inset:0, width:`${pct}%`,
            background: done ? '#5a9e6f' : 'var(--accent)',
            transition:'width 0.5s cubic-bezier(0.16,1,0.3,1)',
          }} />
        </div>
      )}

      {/* Play button */}
      <Link
        to={`/practice/course/${course.id}`}
        className="flex items-center justify-center gap-2 py-2.5 text-sm font-semibold transition-all font-code"
        style={{
          background: done ? 'rgba(90,158,111,0.12)' : 'rgba(212,168,75,0.08)',
          color: done ? '#5a9e6f' : 'var(--gold)',
          border: `1px solid ${done ? 'rgba(90,158,111,0.3)' : 'rgba(212,168,75,0.2)'}`,
        }}
        onMouseEnter={e => {
          e.currentTarget.style.background = done ? 'rgba(90,158,111,0.2)' : 'rgba(212,168,75,0.15)'
        }}
        onMouseLeave={e => {
          e.currentTarget.style.background = done ? 'rgba(90,158,111,0.12)' : 'rgba(212,168,75,0.08)'
        }}
      >
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
          <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z"/>
        </svg>
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
    <div className="flex items-center justify-center min-h-screen cart-bg" style={{background:'var(--ink)'}}>
      <div className="w-8 h-8 border-t border-r rounded-full animate-spin" style={{borderColor:'var(--gold)'}} />
    </div>
  )

  return (
    <div className="min-h-screen cart-bg" style={{background:'var(--ink)'}}>
      <Header onLogout={onLogout} />

      {/* Page header */}
      <div className="relative" style={{borderBottom:'1px solid var(--line)'}}>
        <div className="max-w-4xl mx-auto px-5 sm:px-10 py-10 anim-0">
          <div className="flex items-center gap-3 mb-2">
            <div className="h-px w-6" style={{background:'var(--gold)'}} />
            <span className="font-code text-xs uppercase tracking-widest" style={{color:'var(--gold)'}}>★ {lbl.subtitle}</span>
          </div>
          <div className="flex items-end justify-between gap-4">
            <h1 className="font-display text-4xl sm:text-5xl font-black" style={{color:'var(--text)'}}>
              {lbl.title}
            </h1>
            <Link
              to="/create-course"
              className="flex items-center gap-2 px-4 py-2.5 text-sm font-semibold border transition-all font-code shrink-0"
              style={{borderColor:'var(--line-strong)', color:'var(--muted)', background:'var(--ink-soft)'}}
              onMouseEnter={e => { e.currentTarget.style.borderColor='var(--gold)'; e.currentTarget.style.color='var(--text)' }}
              onMouseLeave={e => { e.currentTarget.style.borderColor='var(--line-strong)'; e.currentTarget.style.color='var(--muted)' }}
            >
              + {lbl.createBtn}
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-5 sm:px-10 py-10">
        {courses.length === 0 ? (
          <div className="flex flex-col items-center gap-6 py-24 text-center">
            <div className="font-code text-xs uppercase tracking-widest" style={{color:'var(--muted)'}}>
              — {lbl.empty} —
            </div>
            <Link
              to="/create-course"
              className="px-6 py-3 text-sm font-semibold font-code transition-all"
              style={{background:'var(--gold)', color:'var(--ink)'}}
            >
              + {lbl.createBtn}
            </Link>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
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
