# DS 5003 Group 4 — Meat, Hospitals, and Colorectal Cancer

This repository reproduces the group's analysis of U.S. red meat availability, hospital capacity, and colorectal cancer (CRC) incidence from 1999 to 2020.

The project has two goals:

1. **Describe** how CRC incidence and meat availability changed over time, overall and by age.
2. **Predict** state-level early-onset CRC (ages 20–49) from meat availability, hospital supply, and behavioral risk factors, using a transparent machine-learning workflow.

All analysis code, cleaned data, and executed notebooks are included. The raw inputs are preserved in `original_datasets/` and are never modified by the code.

---

## 1. Repository layout

```text
DS-5003-group-4-Project/
├── README.md                     # this file
├── requirements.txt              # Python packages
├── notebooks/
│   ├── 01_data_cleaning.ipynb    # raw data → cleaned analysis panel
│   ├── 02_exploratory_analysis.ipynb
│   └── 03_modeling.ipynb
├── src/
│   ├── data_prep.py              # cleaning/parsing functions + CLI
│   ├── model.py                  # Ridge / Random Forest / HistGradientBoosting
│   ├── make_figures.py           # Figures 1–4
│   ├── run_all.sh                # scripts end-to-end (Bash)
│   └── render_report.sh          # optional HTML → PDF report
├── outputs/
│   ├── cleaned/                  # tidy CSVs used by notebooks and figures
│   └── interim/hcup_text/        # text extracted from the HCUP PDFs
├── original_datasets/            # untouched raw inputs + SHA256SUMS.txt
├── DATA/                         # original project files (not used by pipeline)
├── OTHER/                        # earlier exports (not used by pipeline)
├── SOURCES/                      # background papers (not used by pipeline)
└── Instructions.pdf
```

`figures/` is created automatically when you run `src/make_figures.py` or notebook 03/02. The optional `report/` folder (HTML + PDF) is not required to reproduce the figures or models.

---

## 2. Requirements

- **Python 3.10+** (tested with 3.11)
- Packages in `requirements.txt`:
  - `pandas`, `numpy`, `scikit-learn`, `matplotlib`
  - `jupyterlab`, `nbformat`, `nbconvert` for notebooks
- **Ghostscript** (`gs`) only if you need to re-extract text from the HCUP PDFs.
- **Google Chrome or Chromium** only if you want to rebuild the optional PDF report.

No internet connection is required for the analysis: all data are in the repository.

### Install

```bash
# from the repository root
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

On Windows, use `python` instead of `python3` if that is how Python is installed.

---

## 3. Quick start: run the scripts

Clone the repository and enter it:

```bash
git clone https://github.com/carlosfrev123/DS-5003-group-4-Project.git
cd DS-5003-group-4-Project
```

Then run the scripts from the repository root:

```bash
python3 src/data_prep.py      # rebuild outputs/cleaned/*.csv from original_datasets/
python3 src/model.py          # fit models, write metrics/predictions/importance
python3 src/make_figures.py   # write figures/fig1..fig4
```

Or run the whole pipeline:

```bash
bash src/run_all.sh
# if your interpreter is `python` rather than `python3`:
PYTHON=python bash src/run_all.sh
```

`run_all.sh` runs cleaning, modeling, and figures. It runs the PDF step only if `report/report.html` exists; otherwise it prints a skip message and exits successfully.

### What each script writes

| Script | Output |
|---|---|
| `src/data_prep.py` | `outputs/cleaned/*.csv`, `outputs/cleaned/data_dictionary.csv`, `outputs/cleaned/state_early_change_ranking.csv` |
| `src/model.py` | `outputs/cleaned/model_metrics.csv`, `model_test_predictions.csv`, `model_permutation_importance.csv`, `model_permutation_importance_full.csv` |
| `src/make_figures.py` | `figures/fig1_national_trends.png`, `fig2_age_specific.png`, `fig3_states_hospitals.png`, `fig4_model.png` |

`make_figures.py` depends on the model outputs, so run `model.py` before `make_figures.py` (unless those CSVs are already present).

---

## 4. Quick start: run the notebooks

```bash
jupyter lab
```

Open the notebooks in this order:

1. **`01_data_cleaning.ipynb`** — parses the raw CDC WONDER XML, USDA, HCUP, and BRFSS files, builds `outputs/cleaned/analysis_panel_1999_2020.csv`, and runs validation checks.
   - Requires `original_datasets/` and `outputs/interim/hcup_text/`.
   - You can skip this notebook if `outputs/cleaned/` is already present and you only want figures/models.
2. **`03_modeling.ipynb`** — fits Ridge, Random Forest, and Histogram Gradient Boosting; evaluates GroupKFold and temporal holdouts; writes model metrics and Figure 4.
3. **`02_exploratory_analysis.ipynb`** — produces Figures 1–3 (national trends, age bands, state changes, hospital supply).

The notebooks include a setup cell that finds the repository root automatically, so they work whether Jupyter starts in the repository root or in `notebooks/`. Run cells top-to-bottom.

If you re-run notebook 01, it overwrites the tracked files in `outputs/cleaned/` with the same deterministic outputs.

---

## 5. Optional: rebuild the PDF report

The report source is not required for the figures/models. If `report/report.html` and `report/assets/` are present:

```bash
bash src/render_report.sh
```

The script auto-detects Chrome on macOS, Linux, and Windows (Git Bash/WSL), or uses `CHROME_BIN`:

```bash
CHROME_BIN="/path/to/chrome" bash src/render_report.sh
```

It writes `report/Meat_Hospitals_Colorectal_Cancer_Report.pdf` and prints the page count. The report is designed for 6 pages.

---

## 6. Data and provenance

| Input | Location | Notes |
|---|---|---|
| CDC WONDER U.S. Cancer Statistics (D205) | `original_datasets/CDC_cancer/*.xml` | State-year CRC counts, populations, crude and age-adjusted rates, ages 20–49, national age bands |
| USDA ERS meat availability | `original_datasets/USDA_meat/mtpcc.csv` | National per capita red meat/poultry availability, carcass weight |
| HCUP SID hospital counts | `original_datasets/HCUP_SID/raw/` | HTML tables 1997–2010 + annual PDFs 2011–2020 |
| CDC BRFSS | `original_datasets/CDC_BRFSS/*.json` | State smoking, obesity, uninsurance |
| Census region | derived in `src/data_prep.py` | 50 states + DC |

See `original_datasets/README.md` for file-level provenance and `original_datasets/SHA256SUMS.txt` for checksums.

If you need to regenerate the HCUP PDF text:

```bash
mkdir -p outputs/interim/hcup_text
for y in 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020; do
  gs -q -sDEVICE=txtwrite -dTextFormat=3 \
     -o "outputs/interim/hcup_text/$y.txt" \
     "original_datasets/HCUP_SID/raw/$y.pdf"
done
```

---

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'src'` | Run the notebook/script from the repository root, or let the notebook setup cell find the root. The setup cell searches upward for `src/data_prep.py`. |
| `FileNotFoundError: outputs/cleaned/analysis_panel_1999_2020.csv` | Run `python3 src/data_prep.py` or notebook 01 first; or restore the tracked `outputs/cleaned/` files. |
| `FileNotFoundError: .../outputs/interim/hcup_text/2011.txt` | Re-extract the HCUP PDFs with the Ghostscript loop above, or restore `outputs/interim/`. |
| `FileNotFoundError: outputs/cleaned/model_permutation_importance_full.csv` | Run `python3 src/model.py` before `src/make_figures.py`. |
| `jupyter: command not found` | `pip install jupyterlab` inside the activated environment. |
| `MPLCONFIGDIR` or font-cache warnings | The scripts use the system temp directory automatically. If needed: `export MPLCONFIGDIR=$(python3 -c "import tempfile;print(tempfile.gettempdir())")/mpl`. |
| `Chrome not found` | The report step is optional. Set `CHROME_BIN` to your Chrome/Chromium executable, or skip it. |
| `bash: command not found` on Windows | Use Git Bash or WSL, or run the three Python commands manually. |
| `python3: command not found` on Windows | Use `python` (and `py -3`) instead. |
| PDF has missing figures | Run `src/make_figures.py` first; `report/assets/` must contain the four PNGs. |

---

## 8. Notes for AI agents

- **Work from the repository root.** All paths in `src/*.py` are derived from `Path(__file__).resolve().parents[1]`; do not hardcode absolute paths.
- **Do not modify `original_datasets/`.** It is the read-only raw-data archive. Write derived files to `outputs/` and figures to `figures/`.
- **Preferred execution order:** `src/data_prep.py` → `src/model.py` → `src/make_figures.py`.
- **If `outputs/cleaned/` already exists**, you can skip cleaning and run `src/model.py` then `src/make_figures.py`.
- **Determinism:** model random seeds are fixed (`random_state=42`). Figures should look identical up to Matplotlib version/font differences.
- **Success criteria:**
  - `outputs/cleaned/analysis_panel_1999_2020.csv` exists with 1,116 data rows.
  - `outputs/cleaned/model_metrics.csv` has 9 rows (3 models × 3 validation schemes).
  - `figures/` contains 4 PNG files.
  - `figures/fig1_national_trends.png` shows overall CRC falling and early-onset CRC rising.
- **No network calls** are made by the analysis scripts. All data are local.
- **Do not edit notebooks' saved outputs by hand.** Re-run the notebook or the corresponding script to regenerate them.
- **Report generation is optional.** If `report/` is absent, `run_all.sh` skips it and still succeeds.

---

## 9. Team

- **Course:** DS 5003, University of Virginia School of Data Science
- **Team:** Group 4
- **Members:** add names here
- **Term:** Fall 2026
