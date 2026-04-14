import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api'
import { useLang } from '../LanguageContext'

// ── helpers ──────────────────────────────────────────────────────────────────

function flagUrl(val) {
  if (!val) return null
  if (val.codePointAt(0) >= 0x1F1E0) {
    const iso = [...val].map(c => String.fromCharCode(c.codePointAt(0) - 0x1F1E6 + 65)).join('').toLowerCase()
    return 'https://flagcdn.com/w320/' + iso + '.png'
  }
  return 'https://flagcdn.com/w320/' + val.toLowerCase() + '.png'
}

function generateMcOptions(card, courseNames, continentNames, isCapital, lang) {
  const correct = isCapital ? card.capital : (lang === 'de' && card.country_name_de ? card.country_name_de : card.country_name)
  // Deduplicate pool and exclude correct answer
  let pool = [...new Set([...courseNames, ...continentNames])].filter(n => n !== correct)
  const shuffled = [...pool].sort(() => Math.random() - 0.5)
  const options = [...shuffled.slice(0, 3), correct].sort(() => Math.random() - 0.5)
  return options
}

function freshMcOptions(card, courseNames, continentNames, isCapital, lang) {
  return generateMcOptions(card, courseNames, continentNames, isCapital, lang)
}

// For regions course: pick 3 wrong region cards + 1 correct, all as {id, name, map_image}
function generateRegionOptions(card, allCards) {
  const correctRegionId = card.region_id
  const pool = allCards.filter(c => c.region_id && c.region_id !== correctRegionId)
  const seen = new Set()
  const unique = pool.filter(c => { if (seen.has(c.region_id)) return false; seen.add(c.region_id); return true })
  const shuffled = [...unique].sort(() => Math.random() - 0.5).slice(0, 3)
  const correct = { id: card.region_id, name: card.region_name, map_image: card.region_map_image }
  return [...shuffled.map(c => ({ id: c.region_id, name: c.region_name, map_image: c.region_map_image })), correct].sort(() => Math.random() - 0.5)
}

function advanceCard(card, rating, courseType) {
  if (rating === 'wrong') return { ...card, stage: 1, streak: 0 }
  const newStreak = card.streak + 1
  if (courseType === 'regions') {
    if (newStreak >= 5) return { ...card, stage: 'learned', streak: 0 }
    return { ...card, streak: newStreak }
  }
  const thresholds = { 1: 2, 2: 3 }
  if (newStreak >= thresholds[card.stage]) {
    const nextStage = card.stage === 2 ? 'learned' : card.stage + 1
    return { ...card, stage: nextStage, streak: 0 }
  }
  return { ...card, streak: newStreak }
}

function pickNextIndex(cards, recentQueue) {
  const nonLearned = cards
    .map((c, i) => ({ c, i }))
    .filter(({ c }) => c.stage !== 'learned')
  if (nonLearned.length === 0) return null
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

// ── sub-components ────────────────────────────────────────────────────────────

function StageIndicator({ stage, t }) {
  const labels = { 1: t.stage1, 2: t.stage2 }
  return (
    <div className="flex items-center gap-2 text-xs text-gray-500">
      {[1, 2].map(s => (
        <div key={s} className="flex items-center gap-1">
          <div className={`w-2 h-2 rounded-full ${
            s < stage ? 'bg-green-500' : s === stage ? 'bg-blue-400' : 'bg-gray-700'
          }`} />
          <span className={s === stage ? 'text-blue-400' : ''}>{labels[s]}</span>
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

function normalizeSearch(str) {
  return str.trim().toLowerCase()
    .replace(/ä/g, 'a').replace(/ö/g, 'o').replace(/ü/g, 'u').replace(/ß/g, 'ss')
    .replace(/é|è|ê/g, 'e').replace(/á|à|â/g, 'a').replace(/ó|ò|ô/g, 'o')
    .replace(/ú|ù|û/g, 'u').replace(/í|ì|î/g, 'i').replace(/ñ/g, 'n')
}

function TextInput({ allSuggestions, altSuggestions, value, onChange, onSubmit, placeholder }) {
  const [open, setOpen] = useState(false)
  const inputRef = useRef(null)

  useEffect(() => {
    // Focus without scrolling — critical for iOS keyboard layout fix
    if (inputRef.current) {
      inputRef.current.focus({ preventScroll: true })
    }
  }, [])
  const q = normalizeSearch(value)
  const filtered = q.length > 0 && allSuggestions.length > 0
    ? allSuggestions.filter(n => {
        const match = normalizeSearch(n).includes(q)
        const alt = altSuggestions && altSuggestions[n]
        const altMatch = alt && normalizeSearch(alt).includes(q)
        return match || altMatch
      })
    : []

  function select(name) {
    onChange(name)
    setOpen(false)
  }

  return (
    <div className="relative w-full">
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={e => { onChange(e.target.value); setOpen(true) }}
        onKeyDown={e => {
          if (e.key === 'Enter' && value.trim()) { setOpen(false); onSubmit(value) }
          if (e.key === 'Escape') setOpen(false)
        }}
        placeholder={placeholder}
        autoComplete="off"
        className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:border-blue-500"
      />
      {open && filtered.length > 0 && (
        <ul className="absolute z-10 w-full bottom-full mb-1 bg-gray-800 border border-gray-700 rounded-xl overflow-hidden shadow-lg max-h-48 overflow-y-auto">
          {filtered.map(name => (
            <li key={name} onMouseDown={() => select(name)} className="px-4 py-4 hover:bg-gray-700 active:bg-gray-600 cursor-pointer text-base border-b border-gray-700 last:border-0">
              {name}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// ── Card visuals by type ─────────────────────────────────────────────────────

function cardDisplayName(card, lang) {
  return lang === 'de' && card.country_name_de ? card.country_name_de : card.country_name
}

function CardVisual({ card, courseType, revealed, t, lang }) {
  if (courseType === 'flags') {
    const url = flagUrl(card.flag_emoji)
    return (
      <div className="w-full flex items-center justify-center mb-6" style={{ height: '11rem' }}>
        {url ? (
          <img src={url} alt="Flag" className="max-h-full max-w-full rounded-xl shadow-2xl object-contain" />
        ) : (
          <div className="text-8xl">{card.flag_emoji}</div>
        )}
      </div>
    )
  }

  if (courseType === 'domains') {
    return (
      <div className="w-full flex flex-col items-center justify-center py-10 mb-6">
        <div className="font-mono text-6xl sm:text-7xl font-black text-blue-400 tracking-tight">
          {card.domain}
        </div>
      </div>
    )
  }

  if (courseType === 'capitals') {
    const url = flagUrl(card.flag_emoji)
    return (
      <div className="w-full flex flex-col items-center justify-center py-6 mb-6 gap-4">
        {url && <img src={url} alt={card.country_name} className="h-20 rounded-lg shadow-lg" />}
        <div className="text-3xl font-bold text-white">{cardDisplayName(card, lang)}</div>
      </div>
    )
  }

  // Default: clue image or question
  if (revealed) {
    return (
      <div className="w-full mb-4">
        {card.question ? (
          <div className="w-full rounded-xl bg-gray-800 border border-gray-700 flex items-center justify-center px-6 py-10 mb-3">
            <p className="text-xl font-semibold text-white text-center">{card.question}</p>
          </div>
        ) : card.image ? (
          <img src={card.image} alt="Clue" className="w-full rounded-xl object-contain max-h-72" />
        ) : (
          <div className="w-full h-40 rounded-xl bg-gray-800 border border-gray-700 flex items-center justify-center mb-3">
            <span className="text-gray-600 text-sm">{t.noImage}</span>
          </div>
        )}
        <div className="mt-3 bg-gray-800 rounded-xl p-3 border border-gray-700">
          <div className="font-bold text-sm mb-1">{cardDisplayName(card, lang)}</div>
          {card.description && (
            <p className="text-gray-400 text-xs leading-relaxed">{card.description}</p>
          )}
        </div>
      </div>
    )
  }
  return (
    <div className="w-full mb-4">
      {card.question ? (
        <div className="w-full rounded-xl bg-gray-800 border border-gray-700 flex items-center justify-center px-6 py-12">
          <p className="text-2xl font-semibold text-white text-center">{card.question}</p>
        </div>
      ) : card.image ? (
        <img src={card.image} alt="Clue" className="w-full rounded-xl object-contain max-h-56" />
      ) : (
        <div className="w-full h-48 rounded-xl bg-gray-800 border border-gray-700 flex items-center justify-center">
          <span className="text-gray-600 text-sm">{t.noImage}</span>
        </div>
      )}
    </div>
  )
}

// ── main component ────────────────────────────────────────────────────────────

export default function CoursePracticeView() {
  const { courseId } = useParams()
  const { t, lang } = useLang()

  const [courseType, setCourseType] = useState('clues')
  const [cards, setCards] = useState([])
  const [allCountryNames, setAllCountryNames] = useState([])
  const [allCountryNamesAlt, setAllCountryNamesAlt] = useState({})
  const [courseCountryNames, setCourseCountryNames] = useState([])
  const [continentCountryNames, setContinentCountryNames] = useState([])
  const [continentCapitalNames, setContinentCapitalNames] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [recentQueue, setRecentQueue] = useState([])
  const [phase, setPhase] = useState('answering')
  const [inputValue, setInputValue] = useState('')
  const [selectedOption, setSelectedOption] = useState(null)
  const [currentMcOptions, setCurrentMcOptions] = useState([])
  const [currentRegionOptions, setCurrentRegionOptions] = useState([])
  const [isCorrect, setIsCorrect] = useState(null)
  const [stats, setStats] = useState({ learned: 0, total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [allDone, setAllDone] = useState(false)
  const [mode, setMode] = useState(null)
  const [learnedIds, setLearnedIds] = useState(new Set())
  const [progressMap, setProgressMap] = useState({})
  const [rawData, setRawData] = useState(null)

  const isCapitalGuess = courseType === 'capitals'

  useEffect(() => {
    Promise.all([
      api.getCourseAllClues(courseId).then(r => r.json()),
      api.getCourseProgress(courseId).then(r => r.json()).catch(() => ({})),
      api.getProgress().then(r => r.json()).catch(() => []),
    ]).then(([data, courseProgress, clueProgress]) => {
      if (!data.clues || data.clues.length === 0) {
        setError(t.noCards)
        setLoading(false)
        return
      }
      const ct = data.course_type || 'clues'
      setCourseType(ct)

      // courseProgress is now a map: { country_id: { stage, streak, learned } }
      const progressMap = (typeof courseProgress === 'object' && !Array.isArray(courseProgress)) ? courseProgress : {}

      let knownIds
      if (ct === 'clues') {
        knownIds = new Set(
          (Array.isArray(clueProgress) ? clueProgress : (clueProgress.results ?? clueProgress))
            .filter(p => p.known)
            .map(p => p.clue)
        )
      } else {
        knownIds = new Set(Object.entries(progressMap).filter(([, v]) => v.learned).map(([k]) => Number(k)))
      }

      setLearnedIds(knownIds)
      setProgressMap(progressMap)
      setRawData(data)
      const useDe = lang === 'de'
      setCourseCountryNames(useDe ? (data.course_country_names_de || data.course_country_names) : data.course_country_names)
      setContinentCountryNames(useDe ? (data.continent_country_names_de || data.continent_country_names) : data.continent_country_names)
      setContinentCapitalNames(data.continent_capital_names || [])
      const courseNames = useDe ? (data.course_country_names_de || data.course_country_names) : data.course_country_names
      const continentNames = useDe ? (data.continent_country_names_de || data.continent_country_names) : data.continent_country_names
      const combined = [...new Set([...courseNames, ...continentNames])].sort()
      setAllCountryNames(combined)
      // Build a map: primary name → alt name (for cross-language search)
      const courseNamesEn = data.course_country_names || []
      const courseNamesDe = data.course_country_names_de || []
      const continentNamesEn = data.continent_country_names || []
      const continentNamesDe = data.continent_country_names_de || []
      const altMap = {}
      courseNamesEn.forEach((en, i) => { if (courseNamesDe[i]) { altMap[useDe ? courseNamesDe[i] : en] = useDe ? en : courseNamesDe[i] } })
      continentNamesEn.forEach((en, i) => { if (continentNamesDe[i]) { altMap[useDe ? continentNamesDe[i] : en] = useDe ? en : continentNamesDe[i] } })
      setAllCountryNamesAlt(altMap)

      const hasAnyProgress = ct === 'clues'
        ? data.clues.some(c => knownIds.has(c.id))
        : Object.keys(progressMap).length > 0
      if (hasAnyProgress) {
        setMode('choose')
      } else {
        startFresh(data, progressMap, false, ct)
      }
      setLoading(false)
    }).catch(() => { setError(t.loadError); setLoading(false) })
  }, [courseId])

  function startFresh(data, progressMap, resume, ctype) {
    const clues = data ?? rawData
    const pm = progressMap ?? {}
    const ct = ctype ?? courseType
    const initialized = clues.clues.map(clue => {
      if (ct === 'clues') {
        const learned = resume && learnedIds.has(clue.id)
        return { ...clue, stage: learned ? 'learned' : 1, streak: 0 }
      }
      const saved = resume && pm[clue.country_id]
      if (saved) {
        return { ...clue, stage: saved.learned ? 'learned' : saved.stage, streak: saved.streak }
      }
      return { ...clue, stage: 1, streak: 0 }
    })
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
    const isCapital = ct === 'capitals'
    const useDe = lang === 'de'
    const mcPool = isCapital ? (clues.continent_capital_names || []) : (useDe ? (clues.continent_country_names_de || clues.continent_country_names) : clues.continent_country_names)
    const mcCourse = isCapital ? clues.clues.map(c => c.capital) : (useDe ? clues.clues.map(c => c.country_name_de || c.country_name) : clues.course_country_names)
    setCurrentMcOptions(freshMcOptions(shuffled[firstIndex], mcCourse, mcPool, isCapital, lang))
    if (ct === 'regions') setCurrentRegionOptions(generateRegionOptions(shuffled[firstIndex], shuffled))
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
    const isCapital = courseType === 'capitals'
    const useDe = lang === 'de'
    const mcPool = isCapital ? continentCapitalNames : continentCountryNames
    const mcCourse = isCapital ? updatedCards.map(c => c.capital) : (useDe ? updatedCards.map(c => c.country_name_de || c.country_name) : courseCountryNames)
    setCurrentMcOptions(freshMcOptions(updatedCards[next], mcCourse, mcPool, isCapital, lang))
    if (courseType === 'regions') setCurrentRegionOptions(generateRegionOptions(updatedCards[next], updatedCards))
  }

  function handleRating(rating) {
    const updated = advanceCard(card, rating, courseType)
    const newCards = cards.map((c, i) => i === currentIndex ? updated : c)
    setCards(newCards)
    const justLearned = updated.stage === 'learned'
    if (justLearned) setStats(s => ({ ...s, learned: s.learned + 1 }))
    if (courseType === 'clues') {
      if (justLearned) api.saveProgress(card.id, true)
    } else {
      api.saveCourseCardProgress(courseId, card.country_id, updated.stage, updated.streak, justLearned)
    }
    goNext(newCards, recentQueue)
  }

  function handleMcSubmit(option) {
    setSelectedOption(option)
    const correct = isCapitalGuess ? card.capital : cardDisplayName(card, lang)
    setIsCorrect(normalize(option) === normalize(correct))
    setPhase('feedback')
  }

  function handleRegionSubmit(regionId) {
    setSelectedOption(regionId)
    setIsCorrect(regionId === card.region_id)
    setPhase('feedback')
  }

  function handleTextSubmit(val) {
    const v = val ?? inputValue
    const correctDe = isCapitalGuess ? card.capital : (card.country_name_de || card.country_name)
    const correctEn = isCapitalGuess ? card.capital : card.country_name
    const vNorm = normalize(v)
    setIsCorrect(vNorm === normalize(correctDe) || vNorm === normalize(correctEn))
    setPhase('feedback')
  }

  function handleContinue() {
    handleRating(isCorrect ? 'correct' : 'wrong')
  }

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950 text-blue-400 text-lg">
      {t.loading}
    </div>
  )

  if (error) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-950 text-gray-400">
      {error}
    </div>
  )

  if (mode === 'choose') {
    const learnedCount = courseType === 'clues'
      ? rawData.clues.filter(c => learnedIds.has(c.id)).length
      : Object.values(progressMap).filter(v => v.learned).length
    const total = rawData.clues.length
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
        <div className="w-full max-w-sm bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col gap-4">
          <div className="text-center mb-2">
            <div className="text-3xl mb-3">📚</div>
            <h2 className="text-xl font-bold text-white mb-1">{t.resumeTitle}</h2>
            <p className="text-gray-400 text-sm">{t.resumeDesc(learnedCount, total)}</p>
          </div>
          <button onClick={() => startFresh(rawData, progressMap, true, courseType)} className="w-full py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-semibold text-white transition-colors">
            {t.resumeButton}
          </button>
          <button onClick={() => startFresh(rawData, progressMap, false, courseType)} className="w-full py-3 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-xl font-semibold text-gray-300 transition-colors">
            {t.restartButton}
          </button>
        </div>
      </div>
    )
  }

  if (allDone) return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-950 text-white gap-6">
      <div className="text-6xl">🎉</div>
      <h1 className="text-3xl font-bold">{t.allDoneTitle}</h1>
      <p className="text-gray-400">{t.allDoneDesc(stats.total)}</p>
      <button onClick={() => history.back()} className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-semibold">
        {t.allDoneBack}
      </button>
    </div>
  )

  const card = cards[currentIndex]
  if (!card) return null
  const needed = courseType === 'regions' ? 5 : ({ 1: 2, 2: 3 }[card.stage] ?? 0)

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      <div className="border-b border-gray-800 px-6 py-3 grid grid-cols-[2.25rem_1fr_2.25rem] items-center">
        <button onClick={() => history.back()} className="inline-flex items-center justify-center w-9 h-9 text-gray-400 hover:text-white border border-gray-700 hover:border-gray-500 rounded-lg transition-all">
          <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg>
        </button>
        <div className="text-sm text-gray-400 text-center">
          <span className="whitespace-nowrap">✅ {stats.learned} / {stats.total} {t.learned}</span>
        </div>
      </div>

      <div className="flex-1 flex flex-col items-center px-4 py-6 max-w-3xl mx-auto w-full">

        <div className="w-full flex items-center justify-between mb-5">
          <StageIndicator stage={card.stage} t={t} />
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 whitespace-nowrap">{t.streak}</span>
            <StreakDots streak={card.streak} needed={needed} />
          </div>
        </div>

        <CardVisual
          card={card}
          courseType={courseType}
          revealed={phase === 'feedback'}
          t={t}
          lang={lang}
        />

        {/* STAGE 1: Regions — map image buttons */}
        {card.stage === 1 && phase === 'answering' && courseType === 'regions' && (
          <div className="w-full grid grid-cols-2 gap-3">
            {currentRegionOptions.map(region => (
              <button
                key={region.id}
                onClick={() => handleRegionSubmit(region.id)}
                className="w-full bg-white hover:opacity-90 border-2 border-gray-700 hover:border-blue-500 rounded-xl overflow-hidden transition-all flex items-center justify-center"
                style={{ height: '9rem' }}
              >
                <img src={region.map_image} alt={region.name} className="w-full h-full object-contain p-2" />
              </button>
            ))}
          </div>
        )}

        {card.stage === 1 && phase === 'feedback' && courseType === 'regions' && (
          <div className="w-full">
            <div className="grid grid-cols-2 gap-3 mb-4">
              {currentRegionOptions.map(region => {
                const isSelected = region.id === selectedOption
                const isCorrectOption = region.id === card.region_id
                let cls = 'w-full border-2 rounded-xl overflow-hidden flex items-center justify-center transition-all bg-white '
                if (isCorrectOption) cls += 'border-green-500'
                else if (isSelected && !isCorrectOption) cls += 'border-red-500 opacity-50'
                else cls += 'border-gray-300 opacity-30'
                return (
                  <div key={region.id} className={cls} style={{ height: '9rem' }}>
                    <img src={region.map_image} alt={region.name} className="w-full h-full object-contain p-2" />
                  </div>
                )
              })}
            </div>
            <button onClick={handleContinue} className="w-full py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-semibold transition-colors">
              {t.next}
            </button>
          </div>
        )}

        {/* STAGE 1: Multiple Choice (non-regions) */}
        {card.stage === 1 && phase === 'answering' && courseType !== 'regions' && (
          <div className="w-full grid grid-cols-2 gap-3 items-stretch">
            {currentMcOptions.map(option => (
              <button
                key={option}
                onClick={() => handleMcSubmit(option)}
                className="w-full h-full py-4 px-3 bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-blue-500 rounded-xl font-semibold text-center transition-all"
              >
                {option}
              </button>
            ))}
          </div>
        )}

        {card.stage === 1 && phase === 'feedback' && courseType !== 'regions' && (
          <div className="w-full">
            <div className="grid grid-cols-2 gap-3 mb-4 items-stretch">
              {currentMcOptions.map(option => {
                const isSelected = option === selectedOption
                const correctAnswer = isCapitalGuess ? card.capital : cardDisplayName(card, lang)
                const isCorrectOption = normalize(option) === normalize(correctAnswer)
                let cls = 'w-full h-full py-4 px-3 border rounded-xl font-semibold text-center '
                if (isCorrectOption) cls += 'bg-green-900 border-green-600 text-green-300'
                else if (isSelected && !isCorrectOption) cls += 'bg-red-900 border-red-600 text-red-300'
                else cls += 'bg-gray-800 border-gray-700 text-gray-500'
                return <div key={option} className={cls}>{option}</div>
              })}
            </div>
            <button onClick={handleContinue} className="w-full py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-semibold transition-colors">
              {t.next}
            </button>
          </div>
        )}

        {/* STAGE 2: Text Input */}
        {card.stage === 2 && phase === 'answering' && courseType !== 'regions' && (
          <div className="w-full">
            <p className="text-gray-400 text-sm mb-3 text-center">
              {isCapitalGuess ? (t.typeCapital || 'Type the capital city') : t.typeCountry}
            </p>
            <TextInput
              allSuggestions={isCapitalGuess ? [] : allCountryNames}
              altSuggestions={isCapitalGuess ? [] : allCountryNamesAlt}
              value={inputValue}
              onChange={setInputValue}
              onSubmit={handleTextSubmit}
              placeholder={isCapitalGuess ? (t.typeCapitalPlaceholder || 'Capital city...') : t.typeCountryPlaceholder}
            />
            <button
              onClick={() => handleTextSubmit()}
              disabled={!inputValue.trim()}
              className="w-full mt-3 py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 rounded-xl font-semibold transition-colors"
            >
              {t.confirm}
            </button>
          </div>
        )}

        {/* STAGE 2: feedback */}
        {card.stage === 2 && phase === 'feedback' && courseType !== 'regions' && (
          <div className="w-full">
            <div className={`text-center rounded-xl py-3 px-4 mb-4 font-semibold ${isCorrect ? 'bg-green-900 border border-green-700 text-green-300' : 'bg-red-900 border border-red-700 text-red-300'}`}>
              {isCorrect
                ? t.correct(isCapitalGuess ? card.capital : card.country_name)
                : t.wrong(isCapitalGuess ? card.capital : card.country_name)}
            </div>
            <button onClick={handleContinue} className="w-full py-3 bg-blue-600 hover:bg-blue-500 rounded-xl font-semibold transition-colors">
              {t.next}
            </button>
          </div>
        )}

      </div>
    </div>
  )
}
