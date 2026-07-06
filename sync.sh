#!/usr/bin/env bash
# sync.sh — Rulează scraperul și împinge events.json la GitHub.
# Ruleaza din directorul proiectului: cd /path/to/facebook-events && bash sync.sh

set -e
cd "$(dirname "$0")"

echo "=== $(date '+%Y-%m-%d %H:%M:%S') — Pornire colectare ==="

# 1. Extrage evenimentele
python3 extract_events.py

# 2. Daca events.json s-a schimbat, commit + push
if git diff --quiet events.json; then
  echo "=== Nicio schimbare in events.json — push omis. ==="
else
  git add events.json
  git commit -m "Auto: actualizare evenimente $(date '+%Y-%m-%d %H:%M')"
  git push
  echo "=== Push OK — Netlify va redeploya automat. ==="
fi
