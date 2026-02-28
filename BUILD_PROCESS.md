# Build & Deploy Process

## Automatische Hash-Aktualisierung

Nach jedem Build werden die CSS und JS Hashes **automatisch** in `templates/fitness.html` aktualisiert.

### Wie es funktioniert:

1. **Build-Schritt**: `npm run build` erstellt neue Asset-Dateien mit Hashes
   ```
   dist/assets/index-<HASH>.js
   dist/assets/index-<HASH>.css
   ```

2. **Auto-Update-Schritt**: Nach dem Build läuft `update_template_hashes.py`
   - Liest die aktuellen Hashes aus `dist/assets/`
   - Aktualisiert die Links in `templates/fitness.html`
   - Gibt Status aus (updated oder already up-to-date)

### Normale Verwendung:

```bash
# Im fitness-frontend Verzeichnis:
npm run build

# Das build-Script ist so definiert:
# "build": "vite build && python3 ../update_template_hashes.py"
```

### Oder via Docker:

```bash
docker compose exec django-dev bash -c "cd /code/fitness-frontend && npm run build"
```

### Deploy:

```bash
# Im fitness-frontend Verzeichnis:
npm run deploy
```

Das `deploy`-Script:
1. Läuft `npm run build` (inkl. Auto-Update)
2. Löscht alte Assets aus `/static/fitness/`
3. Kopiert neue Assets hin
4. Bestätigung ausgeben

## Warum automatische Hashes?

Browser cachen aggressive. Wenn sich Code ändert, braucht man neue Dateinamen:
- `index-Q-vTsEmi.js` (alte Version)
- `index-NEW-HASH.js` (neue Version)

So sehen Browser: "Das ist eine neue Datei!" und cachen nicht die alte.

## Dateien:

- `update_template_hashes.py` — Python-Script für Auto-Update
- `fitness-frontend/package.json` — Build-Scripts
- `templates/fitness.html` — Template mit Hashes (wird auto-updated)
- `vite.config.js` — Vite Konfiguration mit PWA-Plugin

---

**Status:** ✅ Automatisiert seit Feb 28, 2026
