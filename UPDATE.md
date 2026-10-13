# Actualizare events.json (task programat: luni și joi)

Se rulează cu Claude în Chrome (sesiune Facebook logată). Scraperul Python (`extract_events.py`) nu mai e folosit.

## Reguli de conținut
- Doar **petreceri** (party, social, festival). **Nu** cursuri, workshopuri, clase, intensive.
- Nu include paginile scoase din `pages.json` (ex. Salsa On Sundays — evenimente anulate, neactualizate).
- Nu inventa date. Ce nu se poate citi se omite.

## Pași
1. Citește `pages.json`.
2. Pagini normale: deschide `https://www.facebook.com/<slug>/upcoming_hosted_events` (pentru `profile.php?id=X` folosește `...profile.php?id=X&sk=events`). Citește cardurile cu JS (`a[href*="/events/"]`, text din cel mai apropiat părinte care conține „Interesat/găzduit”). Chrome blochează output cu query string: nu returna URL-uri cu `?`.
3. Pagini cu `"mod": "postari"` (ex. SBK Latino Party, nu fac evenimente FB): deschide pagina, citește postările recente și caută anunțuri de petreceri viitoare (dată, oră, locație). Apasă „Vezi mai mult” ca să vezi textul întreg. `link` = URL-ul paginii, `id` = `<slug>-<AAAA-LL-ZZ>`.
4. Ignoră cursurile/workshopurile ca eveniment de sine stătător (un workshop inclus în biletul unei petreceri nu contează).
5. Data: `data_raw` în format Facebook (`Vi, 30 oct. la 23:00`; `Mâine`/`Azi` se convertesc în dată reală), `data_parsed` ISO.
6. Evenimentele care se repetă (aceeași petrecere în mai multe date) → câte o intrare per dată.
7. Șterge evenimentele trecute de mai mult de 7 zile; păstrează restul + pozele existente. Dacă o pagină nu poate fi citită, păstrează evenimentele ei vechi și raportează.
8. `actualizat_la` = acum (UTC). Commit „Auto: actualizare evenimente <data>” + `git push` (Netlify publică automat).
9. Raport scurt: ce e nou, ce a dispărut, ce pagini au dat eroare.

## Limitări cunoscute
- Pozele Facebook (`fbcdn`) sunt semnate și expiră; Chrome le blochează la citire, deci evenimentele noi nu au poză.
