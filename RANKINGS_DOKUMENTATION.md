# 📊 Rankings Section - Dokumentation

## Wo du die Rankings bearbeitest

Alle Rankings-Daten befinden sich in: **`/media/docker/alex-django/static/js/main.js`** (Zeile 1-34)

---

## 🎬 Struktur eines Rankings-Eintrags

```javascript
{
    rank: 1,                    // Position (1-5)
    title: 'Filmname',          // Name des Films/Serie/Anime
    year: 2023,                 // Veröffentlichungsjahr
    rating: '9.2',              // IMDb Rating (0.0-10.0)
    length: '120min',           // Länge (Filme in Minuten, Serien: "X Staffeln")
    description: 'Beschreibung...', // Kurze Beschreibung (optional)
    platform: 'Netflix',        // Plattform (Netflix, Amazon Prime, Disney+, etc.)
    imdb: 'https://www.imdb.com/title/ttXXXXXX/', // IMDb Link
    poster: 'POSTER_URL'        // Poster-Bild URL
}
```

---

## 🖼️ Poster-Bilder einfügen

### Lokale Bilder im Projekt-Ordner
1. Bilder speichern in: `/static/css/images/movie/`
2. In der Datei dann eintragen:
```javascript
poster: '/static/css/images/movie/mein-poster.jpg'
```

**Empfohlene Bildgröße**: 336×500px (2:3 Seitenverhältnis)

### Beispiel:
```javascript
poster: '/static/css/images/movie/the-sixth-sense.jpg'
poster: '/static/css/images/movie/interstellar.jpg'
```

---

## 🔗 IMDb Links korrekt eintragen

Die IMDb-ID findest du so:
1. Gehe zu https://www.imdb.com
2. Suche nach dem Film/Serie/Anime
3. Klicke auf den Eintrag
4. Die URL sieht so aus: `https://www.imdb.com/title/tt0167404/`
5. Die **tt0167404** ist deine IMDb-ID

**Format für deine Datei:**
```javascript
imdb: 'https://www.imdb.com/title/tt0167404/'
```

---

## 📝 Beispiele zum Kopieren

### Film
```javascript
{
    rank: 1,
    title: 'The Sixth Sense',
    year: 1999,
    rating: '9.2',
    length: '107min',
    description: 'Ein Psycho-Thriller mit einem der unvergesslichsten Twists der Filmgeschichte.',
    platform: 'Amazon Prime',
    imdb: 'https://www.imdb.com/title/tt0167404/',
    poster: 'https://m.media-amazon.com/images/...'
}
```

### Serie
```javascript
{
    rank: 1,
    title: 'Prison Break',
    year: 2005,
    rating: '9.0',
    length: '5 Staffeln',
    description: 'Spannungsgeladen von Anfang bis Ende...',
    platform: 'Disney+',
    imdb: 'https://www.imdb.com/title/tt0455275/',
    poster: '...'
}
```

### Anime
```javascript
{
    rank: 1,
    title: 'Attack on Titan',
    year: 2013,
    rating: '9.1',
    length: '4 Staffeln',
    description: 'Komplexe Welt...',
    platform: 'Crunchyroll',
    imdb: 'https://www.imdb.com/title/tt2560140/',
    poster: '...'
}
```

---

## 🎯 Meta-Information Ordnung

Die Reihenfolge ist jetzt:
1. **⭐ Rating** (mit Stern-Symbol)
2. **Plattform** (Netflix, Amazon Prime, etc.)
3. **Länge** (Minuten oder Staffeln)
4. **Jahr** (Veröffentlichungsjahr)

Beispiel angezeigt: `⭐ 9.2 | Netflix | 107min | 1999`

---

## 📂 Wichtige Dateien

| Datei | Beschreibung |
|-------|-------------|
| `/static/js/main.js` | Alle Rankings-Daten (Zeile 1-34) |
| `/templates/index.html` | Rankings-HTML (Zeile 120-142) |
| `/static/css/styles.css` | Rankings-Styling (Zeile 1930-2090) |

---

## ❓ Häufige Fragen

**Q: Wie viele Rankings kann ich haben?**
A: Pro Kategorie maximal 5 (rank: 1-5). Du kannst aber mehr hinzufügen und dann die Nummer anpassen.

**Q: Kann ich die Reihenfolge ändern?**
A: Ja! Ändere einfach die `rank` Nummer.

**Q: Wo sehe ich die Änderungen live?**
A: Nach dem Speichern: Browser aktualisieren (Strg+F5 oder Cmd+Shift+R für Hard Refresh)

**Q: Poster wird nicht angezeigt?**
A: Überprüfe die URL oder lade das Bild als Datei hoch und nutze den lokalen Pfad.

**Q: Wie ändere ich die Anzahl der Kategorien?**
A: Dafür brauchst du JavaScript-Änderungen. Meld dich, wenn du das brauchst!

---

## 🚀 Schnell-Guide zum Ändern

1. Öffne `/media/docker/alex-django/static/js/main.js`
2. Suche nach `const RANKINGS = {`
3. Bearbeite die Daten (title, rating, year, etc.)
4. **Speichern**
5. Browser neuladen (Strg+F5)
6. Fertig! ✨

---

Bei Fragen oder Problemen meld dich!
