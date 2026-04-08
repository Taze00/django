import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api'

// ── helpers ──────────────────────────────────────────────────────────────────

function generateMcOptions(card, courseCountryNames, continentCountryNames) {
  const correct = card.country_name
  let pool = courseCountryNames.filter(n => n !== correct)
  if (pool.length < 3) {
    const extra = continentCountryNames.filter(n => n !== correct && !pool.includes(n))
    pool = [...pool, ...extra]
  }
  const shuffled = [...pool].sort(() => Math.random() - 0.5)
  const options = [...shuffled.slice(0, 3), correct].sort(() => Math.random() - 0.5)
  return options
}

// Regenerate fresh MC options each time a card is shown (fix #3: random order + different distractors)
function freshMcOptions(card, courseCountryNames, continentCountryNames) {
  return generateMcOptions(card, courseCountryNames, continentCountryNames)
}

function advanceCard(card, rating) {
  if (rating === 'wrong') return { ...card, stage: 1, streak: 0 }
  // correct
  const newStreak = card.streak + 1
  const thresholds = { 1: 2, 2: 3 }
  if (newStreak >= thresholds[card.stage]) {
    const nextStage = card.stage === 2 ? 'learned' : card.stage + 1
    return { ...card, stage: nextStage, streak: 0 }
  }
  return { ...card, streak: newStreak }
}

// Pick a random non-learned card that is not in the cooldown set.
// cooldown = set of indices recently shown; min gap = min(3, total-1).
function pickNextIndex(cards, recentQueue) {
  const nonLearned = cards
    .map((c, i) => ({ c, i }))
    .filter(({ c }) => c.stage !== 'learned')
  if (nonLearned.length === 0) return null

  // Prefer cards not in the recent queue
  const cooldownSize = Math.min(3, nonLearned.length - 1)
  const cooldownSet = new Set(recentQueue.slice(-cooldownSize))
  const preferred = nonLearned.filter(({ i }) => !cooldownSet.has(i))
  const pool = preferred.length > 0 ? preferred : nonLearned
  const pick = pool[Math.floor(Math.random() * pool.length)]
  return pick.i
}

function normalize(str) {
  return str.trim().toLowerCase()
}

const STAGE_LABELS = { 1: 'Multiple Choice', 2: 'Eintippen' }

// ── sub-components ────────────────────────────────────────────────────────────

function StageIndicator({ stage }) {
  return (
    <div className="flex items-center gap-2 text-xs text-gray-500">
      {[1, 2].map(s => (
        <div key={s} className="flex items-center gap-1">
          <div className={`w-2 h-2 rounded-full ${
            s < stage ? 'bg-green-500' : s === stage ? 'bg-blue-400' : 'bg-gray-700'
          }`} />
          <span className={s === stage ? 'text-blue-400' : ''}>{STAGE_LABELS[s]}</span>
          {s < 2 && <span className="text-gray-700">→</span>}
        </div>
      ))}
    </div>
  )
}

function StreakDots({ streak, needed }) {
  return (
    <div className="flex gap-1">
      {Array.from({ length: needed }).map((_, i) => (
        <div key={i} className={`w-2.5 h-2.5 rounded-full border ${
          i < streak ? 'bg-blue-400 border-blue-400' : 'border-gray-600'
        }`} />
      ))}
    </div>
  )
}

// Fix #4: autocomplete dropdown for country input
function CountryInput({ allCountries, value, onChange, onSubmit }) {
  const [open, setOpen] = useState(false)
  const filtered = value.trim().length > 0
    ? allCountries.filter(n => n.toLowerCase().startsWith(value.trim().toLowerCase()))
    : []

  function select(name) {
    onChange(name)
    setOpen(false)
    setTimeout(() => onSubmit(name), 0)
  }

  return (
    <div className="relative w-full">
      <input
        type="text"
        value={value}
        onChange={e => { onChange(e.target.value); setOpen(true) }}
        onKeyDown={e => {
          if (e.key === 'Enter' && value.trim()) {
            setOpen(false)
            onSubmit(value)
          }
          if (e.key === 'Escape') setOpen(false)
        }}
        placeholder="Land eintippen..."
        autoFocus
        autoComplete="off"
        className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:border-blue-500"
      />
      {open && filtered.length > 0 && (
        <ul className="absolute z-10 w-full mt-1 bg-gray-800 border border-gray-700 rounded-xl overflow-hidden shadow-lg max-h-52 overflow-y-auto">
          {filtered.map(name => (
            <li
              key={name}
              onMouseDown={() => select(name)}
              className="px-4 py-2.5 hover:bg-gray-700 cursor-pointer text-sm"
            >
              {name}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// ── main component ────────────────────────────────────────────────────────────


export default function CoursePracticeView() {
  const { courseId } = useParams()

  const [cards, setCards] = useState([])
  const [allCountryNames, setAllCountryNames] = useState([])
  const [courseCountryNames, setCourseCountryNames] = useState([])
  const [continentCountryNames, setContinentCountryNames] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [recentQueue, setRecentQueue] = useState([])
  const [phase, setPhase] = useState('answering')
  const [inputValue, setInputValue] = useState('')
  const [selectedOption, setSelectedOption] = useState(null)
  const [currentMcOptions, setCurrentMcOptions] = useState([])
  const [isCorrect, setIsCorrect] = useState(null)
  const [stats, setStats] = useState({ learned: 0, total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [allDone, setAllDone] = useState(false)
  // 'choose' = show resume/restart dialog, 'playing' = in progress
  const [mode, setMode] = useState(null)
  const [learnedIds, setLearnedIds] = useState(new Set())
  const [rawData, setRawData] = useState(null)

  useEffect(() => {
    Promise.all([
      api.getCourseAllClues(courseId).then(r => r.json()),
      api.getProgress().then(r => r.json()),
    ]).then(([data, progress]) => {
      if (!data.clues || data.clues.length === 0) {
        setError('Keine Karten in diesem Kurs.')
        setLoading(false)
        return
      }
      const knownIds = new Set(
        (progress.results ?? progress)
          .filter(p => p.known)
          .map(p => p.clue)
      )
      setLearnedIds(knownIds)
      setRawData(data)
      setCourseCountryNames(data.course_country_names)
      setContinentCountryNames(data.continent_country_names)
      const combined = [...new Set([...data.course_country_names, ...data.continent_country_names])].sort()
      setAllCountryNames(combined)

      const alreadyLearnedCount = data.clues.filter(c => knownIds.has(c.id)).length
      if (alreadyLearnedCount > 0) {
        setMode('choose')
      } else {
        startFresh(data, knownIds, false)
      }
      setLoading(false)
    }).catch(() => { setError('Fehler beim Laden.'); setLoading(false) })
  }, [courseId])

  function startFresh(data, knownIds, resume) {
    const clues = data ?? rawData
    const kIds = knownIds ?? learnedIds
    const initialized = clues.clues.map(clue => ({
      ...clue,
      stage: (resume && kIds.has(clue.id)) ? 'learned' : 1,
      streak: 0,
    }))
    const shuffled = [...initialized].sort(() => Math.random() - 0.5)
    const learnedCount = shuffled.filter(c => c.stage === 'learned').length
    setCards(shuffled)
    setStats({ learned: learnedCount, total: shuffled.length })

    const firstIndex = shuffled.findIndex(c => c.stage !== 'learned')
    if (firstIndex === -1) {
      setAllDone(true)
      setMode('playing')
      return
    }
    setCurrentIndex(firstIndex)
    setRecentQueue([firstIndex])
    setCurrentMcOptions(freshMcOptions(shuffled[firstIndex], clues.course_country_names, clues.continent_country_names))
    setPhase('answering')
    setInputValue('')
    setSelectedOption(null)
    setIsCorrect(null)
    setAllDone(false)
    setMode('playing')
  }

  function goNext(updatedCards, currentQueue) {
    const remaining = updatedCards.filter(c => c.stage !== 'learned')
    if (remaining.length === 0) { setAllDone(true); return }
    const next = pickNextIndex(updatedCards, currentQueue)
    if (next === null) { setAllDone(true); return }
    const newQueue = [...currentQueue, next].slice(-10)
    setRecentQueue(newQueue)
    setCurrentIndex(next)
    setPhase('answering')
    setInputValue('')
    setSelectedOption(null)
    setIsCorrect(null)
    setCurrentMcOptions(freshMcOptions(updatedCards[next], courseCountryNames, continentCountryNames))
  }

  function handleRating(rating) {
    const updated = advanceCard(card, rating)
    const newCards = cards.map((c, i) => i === currentIndex ? updated : c)
    setCards(newCards)

    if (updated.stage === 'learned') {
      setStats(s => ({ ...s, learned: s.learned + 1 }))
      api.saveProgress(card.id, true)
    }
    goNext(newCards, recentQueue)
  }

  function handleMcSubmit(option) {
    setSelectedOption(option)
    setIsCorrect(normalize(option) === normalize(card.country_name))
    setPhase('feedback')
  }

  function handleTextSubmit(val) {
    const v = val ?? inputValue
    setIsCorrect(normalize(v) === normalize(card.country_name))
    setPhase('feedback')
  }

  function handleContinue() {
    handleRating(isCorrect ? 'correct' : 'wrong')
  }

  // ── loading / error ───────────────────────────────────────────────────────────

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950 text-blue-400 text-lg">
      Laden...
    </div>
  )

  if (error) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950 text-gray-400">
      {error}
    </div>
  )

  // ── resume/restart dialog ─────────────────────────────────────────────────────

  if (mode === 'choose') {
    const learnedCount = rawData.clues.filter(c => learnedIds.has(c.id)).length
    const total = rawData.clues.length
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
        <div className="w-full max-w-sm bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col gap-4">
          <div className="text-center mb-2">
            <div className="text-3xl mb-3">📚</div>
            <h2 className="text-xl font-bold text-white mb-1">Kurs fortsetzen?</h2>
            <p className="text-gray-400 text-sm">
              Du hast bereits <span className="text-green-400 font-semibold">{learnedCount} von {total}</span> Karten gelernt.
            </p>
          </div>
          <button
            onClick={() => startFresh(rawData, learnedIds, true)}
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-semibold text-white transition-colors"
          >
            ▶ Fortsetzen
          </button>
          <button
            onClick={() => startFresh(rawData, learnedIds, false)}
            className="w-full py-3 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-xl font-semibold text-gray-300 transition-colors"
          >
            🔄 Neu starten
          </button>
        </div>
      </div>
    )
  }

  // ── all done ──────────────────────────────────────────────────────────────────

  if (allDone) return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-950 text-white gap-6">
      <div className="text-6xl">🎉</div>
      <h1 className="text-3xl font-bold">Alle Karten gelernt!</h1>
      <p className="text-gray-400">{stats.total} Karten gemeistert</p>
      <button
        onClick={() => history.back()}
        className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-semibold"
      >
        Zurück
      </button>
    </div>
  )

  const card = cards[currentIndex]
  if (!card) return null
  const needed = { 1: 2, 2: 3 }[card.stage] ?? 0

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      {/* Header */}
      <div className="border-b border-gray-800 px-4 py-3 flex items-center justify-between">
        <button onClick={() => history.back()} className="text-blue-400 hover:text-blue-300 text-sm">
          ← Zurück
        </button>
        <div className="text-sm text-gray-400">
          ✅ {stats.learned} / {stats.total} gelernt
        </div>
      </div>

      <div className="flex-1 flex flex-col items-center px-4 py-6 max-w-3xl mx-auto w-full">

        {/* Stage indicator + streak */}
        <div className="w-full flex items-center justify-between mb-5">
          <StageIndicator stage={card.stage} />
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Streak:</span>
            <StreakDots streak={card.streak} needed={needed} />
          </div>
        </div>

        {/* Feedback: stacked on mobile, side-by-side on md+ */}
        {phase === 'feedback' ? (
          <div className="w-full flex flex-col md:flex-row gap-5 mb-5 md:h-72">
            <div className="w-full md:flex-1 md:min-w-0 rounded-xl overflow-hidden">
              {card.image ? (
                <img src={card.image} alt="Clue" className="w-full md:h-full object-cover" />
              ) : (
                <div className="w-full h-56 md:h-full bg-gray-800 border border-gray-700 flex items-center justify-center">
                  <span className="text-gray-600 text-sm">Kein Bild</span>
                </div>
              )}
            </div>
            <div className="w-full md:w-80 md:shrink-0 bg-gray-800 rounded-xl p-4 border border-gray-700 flex flex-col overflow-y-auto md:max-h-none" style={{maxHeight: '16rem'}}>
              <div className="font-bold text-xl mb-2">{card.country_name}</div>
              {card.description && (
                <p className="text-gray-400 text-sm leading-relaxed">{card.description}</p>
              )}
            </div>
          </div>
        ) : (
          card.image ? (
            <div className="w-full rounded-xl overflow-hidden mb-6">
              <img src={card.image} alt="Clue" className="w-full max-h-80 object-cover" />
            </div>
          ) : (
            <div className="w-full h-48 rounded-xl bg-gray-800 border border-gray-700 flex items-center justify-center mb-6">
              <span className="text-gray-600 text-sm">Kein Bild</span>
            </div>
          )
        )}

        {/* ── STAGE 1: Multiple Choice ── */}
        {card.stage === 1 && phase === 'answering' && (
          <div className="w-full grid grid-cols-2 gap-3">
            {currentMcOptions.map(option => (
              <button
                key={option}
                onClick={() => handleMcSubmit(option)}
                className="py-4 px-3 bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-blue-500 rounded-xl font-semibold text-center transition-all"
              >
                {option}
              </button>
            ))}
          </div>
        )}

        {card.stage === 1 && phase === 'feedback' && (
          <div className="w-full">
            <div className="grid grid-cols-2 gap-3 mb-4">
              {currentMcOptions.map(option => {
                const isSelected = option === selectedOption
                const isCorrectOption = normalize(option) === normalize(card.country_name)
                let cls = 'py-4 px-3 border rounded-xl font-semibold text-center '
                if (isCorrectOption) cls += 'bg-green-900 border-green-600 text-green-300'
                else if (isSelected && !isCorrectOption) cls += 'bg-red-900 border-red-600 text-red-300'
                else cls += 'bg-gray-800 border-gray-700 text-gray-500'
                return <div key={option} className={cls}>{option}</div>
              })}
            </div>
            <button
              onClick={handleContinue}
              className="w-full py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-semibold transition-colors"
            >
              Weiter →
            </button>
          </div>
        )}

        {/* ── STAGE 2: Eintippen ── */}
        {card.stage === 2 && phase === 'answering' && (
          <div className="w-full">
            <p className="text-gray-400 text-sm mb-3 text-center">Land eintippen:</p>
            <CountryInput
              allCountries={allCountryNames}
              value={inputValue}
              onChange={setInputValue}
              onSubmit={handleTextSubmit}
            />
            <button
              onClick={() => handleTextSubmit()}
              disabled={!inputValue.trim()}
              className="w-full mt-3 py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 rounded-xl font-semibold transition-colors"
            >
              Bestätigen
            </button>
          </div>
        )}

        {card.stage === 2 && phase === 'feedback' && (
          <div className="w-full">
            <div className={`text-center rounded-xl py-3 px-4 mb-4 font-semibold ${isCorrect ? 'bg-green-900 border border-green-700 text-green-300' : 'bg-red-900 border border-red-700 text-red-300'}`}>
              {isCorrect ? `✓ ${card.country_name}` : `✗ Richtig war: ${card.country_name}`}
            </div>
            <button
              onClick={handleContinue}
              className="w-full py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-semibold transition-colors"
            >
              Weiter →
            </button>
          </div>
        )}

      </div>
    </div>
  )
}
