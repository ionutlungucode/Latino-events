#!/usr/bin/env python3
"""
extract_events.py — Extrage evenimentele de pe paginile Facebook monitorizate.

Cerinte:
  pip install playwright
  playwright install chromium

Prima rulare (salveaza sesiunea de login o singura data):
  python extract_events.py --login

Rulari normale (programate prin cron / OpenClaw):
  python extract_events.py
"""

import json
import re
import sys
import time
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright

# ============================================================
# PAGINI — incarcate din pages.json (sau fallback inline)
# ============================================================
PAGES_FILE = Path("pages.json")

def load_pages() -> dict:
    if PAGES_FILE.exists():
        data = json.loads(PAGES_FILE.read_text(encoding="utf-8"))
        # Format suportat: {"Nume pagina": "url"} sau [{"name": "...", "url": "..."}]
        if isinstance(data, dict):
            return data
        elif isinstance(data, list):
            return {item["name"]: item["url"] for item in data}
    # Fallback inline — inlocuieste cu paginile tale reale
    return {
        "Exemplu Scoala Salsa": "https://www.facebook.com/exemplu.scoala.salsa/events",
        "Exemplu Club Latino": "https://www.facebook.com/exemplu.club.latino/events",
    }

# --- Setari generale -----------------------------------------
SESSION_FILE = Path("fb_session.json")   # sesiunea de login salvata
OUTPUT_FILE  = Path("events.json")       # baza de date cu evenimente
HEADLESS     = True                      # False = vezi browserul (debug)
PAUZA_MIN, PAUZA_MAX = 8, 20            # secunde intre pagini (anti-detectie)
# --------------------------------------------------------------


def login_interactiv():
    """Deschide browserul vizibil ca sa te loghezi manual o singura data."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx  = browser.new_context()
        page = ctx.new_page()
        page.goto("https://www.facebook.com/login")
        print("✔ Logheaza-te in fereastra deschisa, apoi apasa Enter aici...")
        input()
        ctx.storage_state(path=str(SESSION_FILE))
        browser.close()
    print(f"✔ Sesiune salvata in {SESSION_FILE}")


def incarca_evenimente_existente() -> dict:
    """Incarca events.json existent, indexat dupa link (pentru deduplicare)."""
    if OUTPUT_FILE.exists():
        data = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        return {ev["link"]: ev for ev in data.get("events", [])}
    return {}


LUNI_RO = {
    'ian': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mai': 5, 'iun': 6,
    'iul': 7, 'aug': 8, 'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12
}

def parse_data_fb(data_raw: str) -> str | None:
    """
    Parsează data în format Facebook românesc → ISO 8601.
    Exemple: 'J, 9 iul. la 21:00', 'L, 7 ian. la 20:00', 'Joi la 21:00'
    """
    if not data_raw:
        return None
    an = datetime.now().year
    # "9 iul. la 21:00" sau "9 iul la 21:00"
    m = re.search(r'(\d{1,2})\s+(\w+)\.?\s+la\s+(\d{1,2}):(\d{2})', data_raw)
    if m:
        zi, luna_str, ora, minut = m.groups()
        luna = LUNI_RO.get(luna_str.lower()[:4].rstrip('.'))
        if luna:
            try:
                dt = datetime(an, luna, int(zi), int(ora), int(minut))
                if dt < datetime.now() - timedelta(days=1):
                    dt = dt.replace(year=an + 1)
                return dt.isoformat()
            except ValueError:
                pass
    return None


def extrage_de_pe_pagina(page, nume_pagina: str, url: str) -> list[dict]:
    """Extrage evenimentele vizibile pe pagina /events a unei pagini FB."""
    evenimente = []
    page.goto(url, wait_until="networkidle", timeout=60_000)
    time.sleep(3)

    # Scroll ca sa se incarce mai multe evenimente
    for _ in range(3):
        page.mouse.wheel(0, 2500)
        time.sleep(2)

    # Linkurile de evenimente au mereu forma /events/<id>
    linkuri = page.eval_on_selector_all(
        'a[href*="/events/"]',
        """els => els.map(a => ({
            href: a.href,
            text: a.innerText.trim()
        }))"""
    )

    vazute = set()
    for item in linkuri:
        m = re.search(r"facebook\.com/events/(\d+)", item["href"])
        if not m or m.group(1) in vazute:
            continue
        vazute.add(m.group(1))

        # Textul cardului contine de obicei: data, titlu, locatie (pe linii)
        linii = [l for l in item["text"].split("\n") if l.strip()]
        evenimente.append({
            "id":          m.group(1),
            "link":        f"https://www.facebook.com/events/{m.group(1)}",
            "titlu":       linii[1] if len(linii) > 1 else (linii[0] if linii else "Necunoscut"),
            "data_raw":    linii[0] if linii else "",
            "data_parsed": parse_data_fb(linii[0] if linii else ""),
            "locatie":     linii[2] if len(linii) > 2 else "",
            "imagine":     "",   # placeholder — extins ulterior daca e necesar
            "sursa":       nume_pagina,
            "colectat_la": datetime.now(timezone.utc).isoformat(),
        })
    return evenimente


def main():
    if "--login" in sys.argv:
        login_interactiv()
        return

    if not SESSION_FILE.exists():
        print("✖ Nu exista sesiune salvata. Ruleaza intai: python extract_events.py --login")
        sys.exit(1)

    pages    = load_pages()
    existente = incarca_evenimente_existente()
    noi_total = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        ctx  = browser.new_context(storage_state=str(SESSION_FILE))
        page = ctx.new_page()

        for nume, url in pages.items():
            print(f"  ⏳ {nume} ...")
            try:
                gasite = extrage_de_pe_pagina(page, nume, url)
                noi = [ev for ev in gasite if ev["link"] not in existente]
                for ev in noi:
                    existente[ev["link"]] = ev
                noi_total += len(noi)
                print(f"     {len(gasite)} gasite, {len(noi)} noi")
            except Exception as e:
                print(f"  ✖ Eroare la {nume}: {e}")

            # Pauza aleatorie intre pagini — reduce riscul de detectie
            time.sleep(random.uniform(PAUZA_MIN, PAUZA_MAX))

        browser.close()

    rezultat = {
        "actualizat_la": datetime.now(timezone.utc).isoformat(),
        "events": sorted(existente.values(), key=lambda e: e["colectat_la"], reverse=True),
    }
    OUTPUT_FILE.write_text(
        json.dumps(rezultat, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n✔ Gata: {noi_total} evenimente noi, {len(existente)} in total → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
