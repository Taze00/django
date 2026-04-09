import { createContext, useContext, useState } from 'react'
import { translations } from './i18n'

const LanguageContext = createContext(null)

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(localStorage.getItem('lang') || 'de')

  function toggle() {
    const next = lang === 'de' ? 'en' : 'de'
    localStorage.setItem('lang', next)
    setLang(next)
  }

  const t = translations[lang]

  return (
    <LanguageContext.Provider value={{ lang, toggle, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLang() {
  return useContext(LanguageContext)
}

export function LangToggle() {
  const { lang, toggle } = useLang()
  return (
    <button
      onClick={toggle}
      className="flex items-center gap-1 text-xs text-gray-400 hover:text-white border border-gray-600 hover:border-gray-400 rounded-lg px-3 py-1.5 transition-all font-mono"
    >
      <span className={lang === 'de' ? 'text-white' : 'text-gray-500'}>DE</span>
      <span className="text-gray-600">|</span>
      <span className={lang === 'en' ? 'text-white' : 'text-gray-500'}>EN</span>
    </button>
  )
}
