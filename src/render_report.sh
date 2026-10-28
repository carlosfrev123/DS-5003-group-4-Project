#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHROME_BIN="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
OUT="$ROOT/report/Meat_Hospitals_Colorectal_Cancer_Report.pdf"
PROFILE="$(mktemp -d /tmp/ds5003-chrome.XXXXXX)"

if [[ ! -x "$CHROME_BIN" ]]; then
  echo "Chrome not found at: $CHROME_BIN" >&2
  echo "Set CHROME_BIN to the Chrome/Chromium executable." >&2
  exit 1
fi

# Keep report/assets in sync with the latest figures.
cp "$ROOT"/figures/fig1_national_trends.png "$ROOT"/figures/fig2_age_specific.png \
   "$ROOT"/figures/fig3_states_hospitals.png "$ROOT"/figures/fig4_model.png \
   "$ROOT/report/assets/"

"$CHROME_BIN" \
  --headless=new \
  --disable-gpu \
  --no-sandbox \
  --user-data-dir="$PROFILE" \
  --no-pdf-header-footer \
  --print-to-pdf="$OUT" \
  "file://$ROOT/report/report.html" 2>/dev/null

rm -rf "$PROFILE"
echo "Wrote $OUT"

# Page count (requires Ghostscript).
if command -v gs >/dev/null 2>&1; then
  gs -q -dNODISPLAY -dNOSAFER -c "($OUT) (r) file runpdfbegin pdfpagecount = quit"
fi
