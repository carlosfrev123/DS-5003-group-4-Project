#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/report/Meat_Hospitals_Colorectal_Cancer_Report.pdf"

if [[ ! -f "$ROOT/report/report.html" ]]; then
  echo "report/report.html not found; the PDF report is optional." >&2
  echo "Figures and model outputs do not require this step." >&2
  exit 1
fi

# Find Chrome/Chromium unless CHROME_BIN is already set.
find_chrome() {
  if [[ -n "${CHROME_BIN:-}" ]]; then
    printf '%s\n' "$CHROME_BIN"
    return 0
  fi

  local candidates=(
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    "/Applications/Chromium.app/Contents/MacOS/Chromium"
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
    "/c/Program Files/Google/Chrome/Application/chrome.exe"
    "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"
  )

  local candidate
  for candidate in "${candidates[@]}"; do
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  for candidate in google-chrome google-chrome-stable chromium chromium-browser microsoft-edge; do
    if command -v "$candidate" >/dev/null 2>&1; then
      command -v "$candidate"
      return 0
    fi
  done

  return 1
}

if ! CHROME_BIN="$(find_chrome)"; then
  echo "Chrome/Chromium not found." >&2
  echo "Set CHROME_BIN to the executable and retry, for example:" >&2
  echo '  CHROME_BIN="/path/to/chrome" bash src/render_report.sh' >&2
  exit 1
fi

for f in fig1_national_trends fig2_age_specific fig3_states_hospitals fig4_model; do
  if [[ ! -f "$ROOT/figures/$f.png" ]]; then
    echo "Missing figures/$f.png. Run: python3 src/make_figures.py" >&2
    exit 1
  fi
done

mkdir -p "$ROOT/report/assets"
cp "$ROOT"/figures/fig1_national_trends.png "$ROOT"/figures/fig2_age_specific.png \
   "$ROOT"/figures/fig3_states_hospitals.png "$ROOT"/figures/fig4_model.png \
   "$ROOT/report/assets/"

PROFILE="$(mktemp -d "${TMPDIR:-/tmp}/ds5003-chrome.XXXXXX")"
trap 'rm -rf "$PROFILE"' EXIT

"$CHROME_BIN" \
  --headless=new \
  --disable-gpu \
  --no-sandbox \
  --user-data-dir="$PROFILE" \
  --no-pdf-header-footer \
  --print-to-pdf="$OUT" \
  "file://$ROOT/report/report.html" 2>/dev/null

echo "Wrote $OUT"

# Page count (requires Ghostscript).
if command -v gs >/dev/null 2>&1; then
  gs -q -dNODISPLAY -dNOSAFER -c "($OUT) (r) file runpdfbegin pdfpagecount = quit"
fi
