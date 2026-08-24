// Sekunden lesbar machen — eine Quelle für alle Ansichten, damit dieselbe
// Dauer nicht an zwei Stellen unterschiedlich aussieht.
//   45  -> "45s"      120 -> "2 min"      340 -> "5:40 min"
export function formatTime(totalSeconds) {
  const s = Math.round(totalSeconds);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return rem > 0 ? `${m}:${String(rem).padStart(2, '0')} min` : `${m} min`;
}

// Kurzform ohne Einheitenwort - fuer enge Zellen, in denen das Label die
// Einheit schon nennt. 45 -> "45s", 65 -> "1:05", 340 -> "5:40"
export function formatTimeShort(totalSeconds) {
  const s = Math.round(totalSeconds);
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}
