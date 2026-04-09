export const translations = {
  de: {
    // Navigation
    back: 'Zurück',
    logout: 'Abmelden',
    overview: 'Übersicht',

    // Login
    loginTitle: 'Bitte einloggen um fortzufahren',
    loginUsername: 'Benutzername',
    loginPassword: 'Passwort',
    loginButton: 'Einloggen',
    loginLoading: 'Einloggen...',
    loginError: 'Benutzername oder Passwort falsch.',
    loginErrorNetwork: 'Verbindungsfehler.',

    // Home
    learnTitle: 'Lernen',
    learnSubtitle: 'Starte einen Kurs und lerne Länder durch Multiple Choice und Eintippen.',
    selectCourse: 'Kurs auswählen →',
    noContinents: 'Noch keine Kontinente im System.',
    countries: 'Länder',

    // Courses
    noCourses: 'Noch keine Kurse vorhanden.',

    // Continent
    continentNotFound: 'Kontinent nicht gefunden.',
    clues: 'Hinweise',

    // Country
    countryNotFound: 'Land nicht gefunden.',
    noClues: 'Noch keine Hinweise für dieses Land vorhanden.',

    // Practice
    loading: 'Laden...',
    loadError: 'Fehler beim Laden.',
    noCards: 'Keine Karten in diesem Kurs.',
    stage1: 'Multiple Choice',
    stage2: 'Eintippen',
    streak: 'Streak:',
    noImage: 'Kein Bild',
    typeCountry: 'Land eintippen:',
    typeCountryPlaceholder: 'Land eintippen...',
    typeCapital: 'Hauptstadt eintippen:',
    typeCapitalPlaceholder: 'Hauptstadt eintippen...',
    confirm: 'Bestätigen',
    next: 'Weiter →',
    correct: (name) => `✓ ${name}`,
    wrong: (name) => `✗ Richtig war: ${name}`,
    learned: 'gelernt',

    // Resume dialog
    resumeTitle: 'Kurs fortsetzen?',
    resumeDesc: (learned, total) => `Du hast bereits ${learned} von ${total} Karten gelernt.`,
    resumeButton: '▶ Fortsetzen',
    restartButton: '🔄 Neu starten',

    // All done
    allDoneTitle: 'Alle Karten gelernt!',
    allDoneDesc: (total) => `${total} Karten gemeistert`,
    allDoneBack: 'Zurück',

    // Cards count
    cards: (n) => `🃏 ${n} Karten`,
  },
  en: {
    // Navigation
    back: 'Back',
    logout: 'Logout',
    overview: 'Overview',

    // Login
    loginTitle: 'Please log in to continue',
    loginUsername: 'Username',
    loginPassword: 'Password',
    loginButton: 'Login',
    loginLoading: 'Logging in...',
    loginError: 'Incorrect username or password.',
    loginErrorNetwork: 'Connection error.',

    // Home
    learnTitle: 'Learn',
    learnSubtitle: 'Start a course and learn countries through multiple choice and typing.',
    selectCourse: 'Select course →',
    noContinents: 'No continents in the system yet.',
    countries: 'Countries',

    // Courses
    noCourses: 'No courses available yet.',

    // Continent
    continentNotFound: 'Continent not found.',
    clues: 'Clues',

    // Country
    countryNotFound: 'Country not found.',
    noClues: 'No clues available for this country yet.',

    // Practice
    loading: 'Loading...',
    loadError: 'Error loading data.',
    noCards: 'No cards in this course.',
    stage1: 'Multiple Choice',
    stage2: 'Typing',
    streak: 'Streak:',
    noImage: 'No image',
    typeCountry: 'Type the country:',
    typeCountryPlaceholder: 'Type country...',
    typeCapital: 'Type the capital city:',
    typeCapitalPlaceholder: 'Capital city...',
    confirm: 'Confirm',
    next: 'Next →',
    correct: (name) => `✓ ${name}`,
    wrong: (name) => `✗ Correct was: ${name}`,
    learned: 'learned',

    // Resume dialog
    resumeTitle: 'Continue course?',
    resumeDesc: (learned, total) => `You have already learned ${learned} of ${total} cards.`,
    resumeButton: '▶ Continue',
    restartButton: '🔄 Restart',

    // All done
    allDoneTitle: 'All cards learned!',
    allDoneDesc: (total) => `Mastered ${total} cards`,
    allDoneBack: 'Back',

    // Cards count
    cards: (n) => `🃏 ${n} cards`,
  },
}

export const LANGUAGES = ['de', 'en']
export const LANGUAGE_LABELS = { de: 'DE', en: 'EN' }
