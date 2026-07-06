# 🎉 Facebook Events Aggregator

Colectează automat evenimentele de pe paginile Facebook monitorizate și le publică pe un website static via GitHub + Netlify.

## Structura proiectului

```
facebook-events/
├── extract_events.py  # Scriptul de scraping (Playwright)
├── pages.json         # Lista paginilor monitorizate
├── events.json        # Baza de date cu evenimente (comitat, auto-generat)
├── sync.sh            # Scraping + git commit/push
├── index.html         # Website-ul public
├── style.css          # Stil
├── app.js             # Logica website (filtre, carduri)
├── netlify.toml       # Config Netlify
└── requirements.txt   # Dependente Python
```

## Setup (prima rulare)

### 1. Instalează dependențele
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Adaugă paginile monitorizate
Editează `pages.json`:
```json
{
  "Scoala Salsa Bucuresti": "https://www.facebook.com/scoalasalsa/events",
  "Club Latino Timisoara":  "https://www.facebook.com/clublatino/events"
}
```

### 3. Salvează sesiunea de login Facebook (o singură dată)
```bash
python extract_events.py --login
```
> Logează-te în browser, apasă Enter, sesiunea se salvează în `fb_session.json`.  
> ⚠️ `fb_session.json` este în `.gitignore` — nu se comite niciodată.

### 4. Inițializează repo-ul Git
```bash
git init
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
git add .
git commit -m "Init: facebook-events"
git push -u origin main
```

### 5. Conectează Netlify
- New site → Import from GitHub → selectează repo-ul
- Build command: (gol)
- Publish directory: `.`
- Deploy → site-ul e live!

## Rulare manuală
```bash
bash sync.sh
```

## Rulare automată (OpenClaw cron)
Configurat în OpenClaw să ruleze zilnic la 07:00.  
Verifică jobul cu: `cron list`

## Actualizare pagini monitorizate
Editează `pages.json` și adaugă/elimină pagini. Nicio altă modificare necesară.
