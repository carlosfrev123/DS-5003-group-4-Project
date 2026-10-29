#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"

"$PYTHON" src/data_prep.py
"$PYTHON" src/model.py
"$PYTHON" src/make_figures.py

if [[ -f "$ROOT/report/report.html" ]]; then
  bash "$ROOT/src/render_report.sh"
else
  echo "Skipping PDF report: report/report.html not found."
  echo "Figures and model outputs are complete."
fi
