/* app.js — Încarcă și afișează evenimentele din events.json */

let allEvents = [];

/* ─── Filtrare evenimente recurente ─────────────────────── */
/**
 * Pentru titluri care apar de mai multe ori (recurente),
 * păstrează doar ocurența din săptămâna curentă.
 * Dacă nu există niciuna în săptămâna curentă, ia cea mai apropiată viitoare.
 */
function deduplicateRecurring(events) {
  const now      = new Date();
  const sow      = new Date(now); // start of week (luni)
  sow.setHours(0, 0, 0, 0);
  sow.setDate(now.getDate() - ((now.getDay() || 7) - 1));
  const eow = new Date(sow);
  eow.setDate(sow.getDate() + 7); // end of week (duminică 23:59:59)

  // Grupăm după titlu normalized
  const groups = {};
  events.forEach(ev => {
    const key = (ev.titlu || ev.link).toLowerCase().trim();
    if (!groups[key]) groups[key] = [];
    groups[key].push(ev);
  });

  const result = [];
  Object.values(groups).forEach(group => {
    if (group.length === 1) {
      result.push(group[0]);
      return;
    }
    // Eveniment recurent — selectăm ocurența potrivită
    const enriched = group.map(ev => ({
      ev,
      date: ev.data_parsed ? new Date(ev.data_parsed) : null,
    }));

    // 1. Prefer ocurența din săptămâna curentă
    const thisWeek = enriched.filter(({ date }) => date && date >= sow && date < eow);
    if (thisWeek.length > 0) {
      result.push(thisWeek[0].ev);
      return;
    }

    // 2. Altfel, cea mai apropiată viitoare
    const upcoming = enriched
      .filter(({ date }) => date && date >= now)
      .sort((a, b) => a.date - b.date);
    if (upcoming.length > 0) {
      result.push(upcoming[0].ev);
      return;
    }

    // 3. Fallback: primul din grup
    result.push(group[0]);
  });

  return result;
}

/* ─── Bootstrap ──────────────────────────────────────────── */
async function init() {
  try {
    const res = await fetch('events.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    allEvents = deduplicateRecurring(data.events || []);

    // Timestamp actualizare
    if (data.actualizat_la) {
      document.getElementById('last-updated').textContent =
        new Date(data.actualizat_la).toLocaleString('ro-RO', {
          day: '2-digit', month: 'long', year: 'numeric',
          hour: '2-digit', minute: '2-digit',
        });
    }

    // Populează filtrul de surse
    const surse = [...new Set(allEvents.map(e => e.sursa).filter(Boolean))].sort();
    const selSursa = document.getElementById('filter-sursa');
    surse.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s;
      opt.textContent = s;
      selSursa.appendChild(opt);
    });

    render();
  } catch (err) {
    document.getElementById('events-grid').innerHTML =
      `<div class="loading">⚠️ Nu s-au putut încărca evenimentele: ${err.message}</div>`;
  }
}

/* ─── Filtrare ───────────────────────────────────────────── */
function getFiltered() {
  const search    = document.getElementById('search').value.toLowerCase().trim();
  const sursa     = document.getElementById('filter-sursa').value;
  const filterDt  = document.getElementById('filter-data').value;

  const now           = new Date();
  const sow           = new Date(now); sow.setHours(0,0,0,0); sow.setDate(now.getDate() - ((now.getDay()||7) - 1));
  const eow           = new Date(sow); eow.setDate(sow.getDate() + 7);
  const som           = new Date(now.getFullYear(), now.getMonth(), 1);
  const eom           = new Date(now.getFullYear(), now.getMonth() + 1, 1);

  return allEvents.filter(ev => {
    if (search && !(ev.titlu||'').toLowerCase().includes(search) &&
                  !(ev.locatie||'').toLowerCase().includes(search)) return false;
    if (sursa && ev.sursa !== sursa) return false;
    if (filterDt !== 'all') {
      // data_raw este text liber (ex. "Sâm, 10 aug"); folosim colectat_la ca aproximație
      const d = new Date(ev.colectat_la);
      if (filterDt === 'upcoming' && d < now) return false;
      if (filterDt === 'week'     && (d < sow || d >= eow)) return false;
      if (filterDt === 'month'    && (d < som || d >= eom)) return false;
    }
    return true;
  });
}

/* ─── Render ─────────────────────────────────────────────── */
function render() {
  const filtered  = getFiltered();
  const grid      = document.getElementById('events-grid');
  const noEvents  = document.getElementById('no-events');

  document.getElementById('count').textContent =
    `${filtered.length} eveniment${filtered.length !== 1 ? 'e' : ''}`;

  if (filtered.length === 0) {
    grid.innerHTML = '';
    noEvents.classList.remove('hidden');
    return;
  }
  noEvents.classList.add('hidden');
  grid.innerHTML = filtered.map(cardHTML).join('');
}

function cardHTML(ev) {
  const cover = ev.imagine
    ? `<div class="card-cover"><img src="${esc(ev.imagine)}" alt="${esc(ev.titlu)}"
           onerror="this.parentElement.innerHTML='🎉'"></div>`
    : `<div class="card-cover">🎉</div>`;

  return `
<div class="card">
  ${cover}
  <div class="card-body">
    <div class="card-title">${esc(ev.titlu || 'Eveniment')}</div>
    ${ev.data_raw ? `<div class="card-date">📅 ${esc(ev.data_raw)}</div>` : ''}
    ${ev.locatie  ? `<div class="card-location">📍 ${esc(ev.locatie)}</div>` : ''}
    <div class="card-footer">
      <span class="badge-sursa" title="${esc(ev.sursa)}">${esc(ev.sursa || '')}</span>
      <a class="card-link" href="${esc(ev.link)}" target="_blank" rel="noopener noreferrer">
        Vezi eveniment →
      </a>
    </div>
  </div>
</div>`;
}

function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

/* ─── Listeners ──────────────────────────────────────────── */
document.getElementById('search').addEventListener('input', render);
document.getElementById('filter-sursa').addEventListener('change', render);
document.getElementById('filter-data').addEventListener('change', render);

init();
