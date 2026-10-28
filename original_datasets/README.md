# Original datasets (read-only)

These are the raw inputs used in the DS 5003 group project. **Nothing in this folder is edited by the analysis code.** Cleaned and derived files are written to `../outputs/cleaned/`, and intermediate text extracted from the HCUP PDFs is written to `../outputs/interim/`.

Download / access date for all web sources: **October 28, 2026**.

## Inventory

| Folder | File(s) | What it is | Source |
|---|---|---|---|
| `CDC_cancer/` | `wonder_state_year_1999_2020.xml`, `wonder_state_early_1999_2020.xml`, `wonder_national_age_1999_2020.xml` | CDC WONDER U.S. Cancer Statistics (D205) XML exports for colon and rectum (site codes 21041–21052): state-year all ages, state-year ages 20–49, and national 5-year age groups. The `req_*.xml` files are the exact API requests. | https://wonder.cdc.gov/cancer-v2022.html |
| `CDC_cancer/` | `United States and Puerto Rico Cancer Statistics, 1999-2022 Incidence.xls` | Original CDC WONDER tab-delimited export supplied with the project (aggregated 1999–2022 by state/race/age/sex; used only as a cross-check). | CDC WONDER |
| `USDA_meat/` | `mtpcc.csv` | USDA ERS per capita availability of red meat, poultry, and fish, carcass/retail/boneless weight, 1909–2021. This is the primary exposure file. | https://ers.usda.gov/data-products/food-availability-per-capita-data-system |
| `USDA_meat/` | `Meat-Statistics.xlsx` | USDA production, slaughter, and cold-storage tables supplied with the project. Not used in the final panel (production is not consumption). | USDA |
| `USDA_meat/` | `meatConsumption.csv`, `vegfresh.csv`, `vegprocessed.csv` | Food-availability extracts supplied with the project. `meatConsumption.csv` is a subset of the red-meat series; the vegetable files are not used in the final analysis. | USDA ERS |
| `HCUP_SID/raw/` | `siddist_hospital.html` | HCUP SID file-composition page, "Number of Hospitals by Year" (1997–2010 tables). | https://hcup-us.ahrq.gov/db/state/siddist/siddist_hospital.jsp |
| `HCUP_SID/raw/` | `2011.pdf` … `2020.pdf` | Annual HCUP reports "Comparison of Hospitals and Records in the [year] HCUP SID to the AHA Survey" (2011–2020). The total SID hospital count (`DSHOSPID`) is extracted from these. | https://hcup-us.ahrq.gov/db/state/siddist/siddist_hospital.jsp |
| `CDC_BRFSS/` | `brfss_dttw-5yxu.json`, `brfss_y4ft-s73h.json` | BRFSS state prevalence data for current smoking, obesity, and health insurance (1999–2020), pulled from the Socrata API. | https://data.cdc.gov/resource/dttw-5yxu , https://data.cdc.gov/resource/y4ft-s73h |
| root | `nihms-paper.pdf` | Zeng et al. (2019), NHANES trends in meat/poultry/fish intake, 1999–2016. Background and processed-meat context. | NIH manuscript / J Acad Nutr Diet |
| root | `TheLancet.com_20261028.zip` | Lancet Oncology package containing the IARC 2015 news article on red/processed meat carcinogenicity. | The Lancet Oncology |

## Checksums

`SHA256SUMS.txt` lists SHA-256 hashes for every raw file. To verify:

```bash
cd original_datasets
shasum -a 256 -c SHA256SUMS.txt
```

## Notes and caveats

- **HCUP SID is not a census of hospitals.** It counts hospitals that participate in the State Inpatient Databases. Coverage is unbalanced: 23 states appear in the 1999 HTML table (16 with usable counts after "Not Available" cells) and 35 in 2020. Fifteen states never appear in the 1999–2020 files.
- **USDA availability is national.** It measures disappearance per person (production + imports + stocks − exports − nonfood use), not individual intake, and it has no state dimension.
- **WONDER data are aggregate and de-identified.** Counts below 10 may be suppressed in some queries; the analysis queries used here returned complete state-year counts.
- **BRFSS is self-reported and changed weighting in 2011.** The analysis treats the series as state-level context, not a consistent clinical measurement.
- Prior group work supplied with the project (the `analysis_merged.csv` file and its dictionary) is kept in `../docs/prior_work/` for reference and is **not** used as a raw input.
