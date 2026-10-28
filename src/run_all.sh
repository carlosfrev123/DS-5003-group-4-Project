#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 src/data_prep.py
python3 src/model.py
MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mpl}" python3 src/make_figures.py
bash src/render_report.sh
