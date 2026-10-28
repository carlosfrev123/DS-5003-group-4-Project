"""
Data preparation for the DS 5003 group project:
Red meat availability, hospital capacity, and colorectal cancer incidence
in the United States, 1999-2020.

The functions in this module read ONLY from ``original_datasets/`` and write
derived files to ``outputs/cleaned/`` and ``outputs/interim/``.  Raw inputs are never
modified.
"""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "original_datasets"
CLEAN = ROOT / "outputs" / "cleaned"
INTERIM = ROOT / "outputs" / "interim"
CLEAN.mkdir(parents=True, exist_ok=True)
INTERIM.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Reference tables
# ---------------------------------------------------------------------------
# (state name, USPS abbreviation, FIPS, Census region)
STATES = [
    ("Alabama", "AL", "01", "South"),
    ("Alaska", "AK", "02", "West"),
    ("Arizona", "AZ", "04", "West"),
    ("Arkansas", "AR", "05", "South"),
    ("California", "CA", "06", "West"),
    ("Colorado", "CO", "08", "West"),
    ("Connecticut", "CT", "09", "Northeast"),
    ("Delaware", "DE", "10", "South"),
    ("District of Columbia", "DC", "11", "South"),
    ("Florida", "FL", "12", "South"),
    ("Georgia", "GA", "13", "South"),
    ("Hawaii", "HI", "15", "West"),
    ("Idaho", "ID", "16", "West"),
    ("Illinois", "IL", "17", "Midwest"),
    ("Indiana", "IN", "18", "Midwest"),
    ("Iowa", "IA", "19", "Midwest"),
    ("Kansas", "KS", "20", "Midwest"),
    ("Kentucky", "KY", "21", "South"),
    ("Louisiana", "LA", "22", "South"),
    ("Maine", "ME", "23", "Northeast"),
    ("Maryland", "MD", "24", "South"),
    ("Massachusetts", "MA", "25", "Northeast"),
    ("Michigan", "MI", "26", "Midwest"),
    ("Minnesota", "MN", "27", "Midwest"),
    ("Mississippi", "MS", "28", "South"),
    ("Missouri", "MO", "29", "Midwest"),
    ("Montana", "MT", "30", "West"),
    ("Nebraska", "NE", "31", "Midwest"),
    ("Nevada", "NV", "32", "West"),
    ("New Hampshire", "NH", "33", "Northeast"),
    ("New Jersey", "NJ", "34", "Northeast"),
    ("New Mexico", "NM", "35", "West"),
    ("New York", "NY", "36", "Northeast"),
    ("North Carolina", "NC", "37", "South"),
    ("North Dakota", "ND", "38", "Midwest"),
    ("Ohio", "OH", "39", "Midwest"),
    ("Oklahoma", "OK", "40", "South"),
    ("Oregon", "OR", "41", "West"),
    ("Pennsylvania", "PA", "42", "Northeast"),
    ("Rhode Island", "RI", "44", "Northeast"),
    ("South Carolina", "SC", "45", "South"),
    ("South Dakota", "SD", "46", "Midwest"),
    ("Tennessee", "TN", "47", "South"),
    ("Texas", "TX", "48", "South"),
    ("Utah", "UT", "49", "West"),
    ("Vermont", "VT", "50", "Northeast"),
    ("Virginia", "VA", "51", "South"),
    ("Washington", "WA", "53", "West"),
    ("West Virginia", "WV", "54", "South"),
    ("Wisconsin", "WI", "55", "Midwest"),
    ("Wyoming", "WY", "56", "West"),
]
STATE_DF = pd.DataFrame(STATES, columns=["state", "state_abbr", "state_fips", "region"])
NAME_TO_ABBR = dict(zip(STATE_DF.state, STATE_DF.state_abbr))
ABBR_TO_NAME = dict(zip(STATE_DF.state_abbr, STATE_DF.state))
FIPS_TO_NAME = dict(zip(STATE_DF.state_fips, STATE_DF.state))


# ---------------------------------------------------------------------------
# CDC WONDER (United States Cancer Statistics, D205)
# ---------------------------------------------------------------------------
def _xml_cells(row: str) -> list[tuple[str, str | None]]:
    """Return (attributes, inner-xml) for each top-level <c> cell in a <r>."""
    return re.findall(r"<c ([^>]*?)(?:/>|>(.*?)</c>)", row, re.S)


def _attr(attrs: str, key: str) -> str | None:
    m = re.search(key + r'="([^"]*)"', attrs)
    return m.group(1) if m else None


def _num(value: str | None) -> float | None:
    if value in (None, "", ".", "Suppressed", "Unreliable"):
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def _wonder_rows(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"<data-table[^>]*>(.*?)</data-table>", text, re.S)
    if not match:
        raise ValueError(f"No <data-table> found in {path}")
    return re.findall(r"<r>.*?</r>", match.group(1), re.S)


def parse_crc_state_year(path: Path | None = None) -> pd.DataFrame:
    """State-year colorectal cancer counts, populations and rates (all ages)."""
    path = path or RAW / "CDC_cancer" / "wonder_state_year_1999_2020.xml"
    records = []
    for row in _wonder_rows(path):
        cells = _xml_cells(row)
        if len(cells) < 6:
            continue
        year = _attr(cells[0][0], "l")
        state = _attr(cells[1][0], "l")
        if not year or not state:
            # sub-total / total row
            continue
        ci = se = None
        if cells[4][1]:
            nested = re.findall(r'<l v="([^"]*)"', cells[4][1])
            ci = nested[0] if nested else None
            se = _num(nested[1]) if len(nested) > 1 else None
        records.append(
            {
                "year": int(year),
                "state": state,
                "state_fips": _attr(cells[1][0], "cd"),
                "crc_cases": _num(_attr(cells[2][0], "v")),
                "population": _num(_attr(cells[3][0], "v")),
                "crc_age_adj_rate": _num(_attr(cells[4][0], "v")),
                "crc_ci_low": _num(re.search(r"\(([\d.]+)", ci).group(1)) if ci else None,
                "crc_ci_high": _num(re.search(r"-\s*([\d.]+)", ci).group(1)) if ci else None,
                "crc_rate_se": se,
                "crc_crude_rate": _num(_attr(cells[5][0], "v")),
            }
        )
    df = pd.DataFrame(records)
    df = df[df.state.isin(NAME_TO_ABBR)].copy()
    df["state_abbr"] = df.state.map(NAME_TO_ABBR)
    return df.sort_values(["state", "year"]).reset_index(drop=True)


def parse_crc_national() -> pd.DataFrame:
    """National colorectal cancer totals by year (from the same WONDER export)."""
    path = RAW / "CDC_cancer" / "wonder_state_year_1999_2020.xml"
    records = []
    for row in _wonder_rows(path):
        if 'c="1"' not in row:
            continue
        year = re.search(r'<c l="(\d{4})"/>', row)
        dts = re.findall(r'dt="([^"]+)"', row)
        if not year or len(dts) < 4:
            continue
        records.append(
            {
                "year": int(year.group(1)),
                "crc_cases": _num(dts[0]),
                "population": _num(dts[1]),
                "crc_age_adj_rate": _num(dts[2]),
                "crc_crude_rate": _num(dts[3]),
            }
        )
    return pd.DataFrame(records).sort_values("year").reset_index(drop=True)


def parse_crc_state_early(path: Path | None = None) -> pd.DataFrame:
    """State-year colorectal cancer counts for adults aged 20-49 (early-onset)."""
    path = path or RAW / "CDC_cancer" / "wonder_state_early_1999_2020.xml"
    records = []
    for row in _wonder_rows(path):
        cells = _xml_cells(row)
        if len(cells) < 5:
            continue
        year = _attr(cells[0][0], "l")
        state = _attr(cells[1][0], "l")
        if not year or not state:
            continue
        records.append(
            {
                "year": int(year),
                "state": state,
                "crc_early_cases": _num(_attr(cells[2][0], "v")),
                "crc_early_population": _num(_attr(cells[3][0], "v")),
                "crc_early_rate": _num(_attr(cells[4][0], "v")),
            }
        )
    df = pd.DataFrame(records)
    df = df[df.state.isin(NAME_TO_ABBR)].copy()
    df["state_abbr"] = df.state.map(NAME_TO_ABBR)
    return df.sort_values(["state", "year"]).reset_index(drop=True)


def parse_crc_national_age(path: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """National CRC counts by year and 5-year age group, plus aggregated bands."""
    path = path or RAW / "CDC_cancer" / "wonder_national_age_1999_2020.xml"
    records = []
    for row in _wonder_rows(path):
        cells = _xml_cells(row)
        if len(cells) < 5:
            continue
        year = _attr(cells[0][0], "l")
        age = _attr(cells[1][0], "l")
        if not year or not age:
            continue
        if not re.match(r"^[\d<>]", age):
            continue
        age = age.replace("&lt;", "<").strip()
        records.append(
            {
                "year": int(year),
                "age_group": age,
                "crc_cases": _num(_attr(cells[2][0], "v")),
                "population": _num(_attr(cells[3][0], "v")),
                "crc_crude_rate": _num(_attr(cells[4][0], "v")),
            }
        )
    age_df = pd.DataFrame(records)

    def band(age: str) -> str | None:
        if age in ["20-24 years", "25-29 years", "30-34 years", "35-39 years", "40-44 years", "45-49 years"]:
            return "20-49"
        if age in ["50-54 years", "55-59 years", "60-64 years"]:
            return "50-64"
        if age in ["65-69 years", "70-74 years", "75-79 years", "80-84 years", "85+ years"]:
            return "65+"
        return None

    age_df["age_band"] = age_df.age_group.map(band)
    band_df = (
        age_df.dropna(subset=["age_band"])
        .groupby(["year", "age_band"], as_index=False)[["crc_cases", "population"]]
        .sum()
    )
    band_df["crc_crude_rate"] = band_df.crc_cases / band_df.population * 100_000
    return age_df, band_df


# ---------------------------------------------------------------------------
# HCUP State Inpatient Databases: hospitals by state and year
# ---------------------------------------------------------------------------
class _HCUPTableParser(HTMLParser):
    """Collect the first table that follows each <a name="YYYY"> anchor."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.rows: list[list[str]] | None = None
        self.row: list[str] | None = None
        self.cell: list[str] | None = None
        self.pending_year: int | None = None
        self.capture = False
        self.capture_year: int | None = None
        self.tables: dict[int, list[list[str]]] = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            name = attrs.get("name", "")
            if re.fullmatch(r"\d{4}", name):
                year = int(name)
                self.pending_year = None if year in self.tables else year
            return
        if tag == "table":
            self.depth += 1
            if self.depth == 1:
                self.rows = []
                self.row = None
                self.cell = None
                self.capture = self.pending_year is not None
                if self.capture:
                    self.capture_year = self.pending_year
            return
        if self.depth != 1 or not self.capture:
            return
        if tag == "tr":
            # Some HCUP tables omit a closing </td> or </tr>; close any open
            # cell, then treat a new <tr> as the end of the previous row.
            if self.cell is not None and self.row is not None:
                self.row.append(" ".join("".join(self.cell).split()))
                self.cell = None
            if self.row is not None and self.rows is not None and self.row:
                self.rows.append(self.row)
            self.row = []
        elif tag in ("td", "th"):
            if self.row is None:
                self.row = []
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == "table":
            if self.depth == 1:
                if self.capture and self.rows is not None and self.capture_year is not None:
                    self.tables[self.capture_year] = self.rows
                    self.pending_year = None
                self.rows = None
                self.capture = False
            self.depth = max(0, self.depth - 1)
            return
        if self.depth != 1 or not self.capture:
            return
        if tag == "tr":
            if self.cell is not None and self.row is not None:
                self.row.append(" ".join("".join(self.cell).split()))
                self.cell = None
            if self.row is not None and self.rows is not None and self.row:
                self.rows.append(self.row)
            self.row = None
        elif tag in ("td", "th"):
            if self.cell is not None and self.row is not None:
                self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None


def parse_hcup_html(path: Path | None = None) -> pd.DataFrame:
    path = path or RAW / "HCUP_SID" / "raw" / "siddist_hospital.html"
    parser = _HCUPTableParser()
    parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
    records = []
    for year, rows in parser.tables.items():
        if year < 1997 or year > 2010:
            continue
        for cells in rows:
            if len(cells) < 4 or not re.fullmatch(r"[A-Z]{2}", cells[0]):
                continue

            def to_int(x: str) -> int | None:
                x = x.replace(",", "").strip()
                return int(x) if re.fullmatch(r"\d+", x) else None

            community = to_int(cells[1])
            noncommunity = to_int(cells[2])
            records.append(
                {
                    "year": year,
                    "state_abbr": cells[0],
                    "hospitals_community_sid": community,
                    "hospitals_noncommunity_sid": noncommunity,
                    "hospitals_sid": (community + noncommunity)
                    if community is not None and noncommunity is not None
                    else None,
                    "hospitals_not_in_sid": to_int(cells[3]),
                    "source": "HCUP HTML table",
                }
            )
    return pd.DataFrame(records)


def parse_hcup_pdfs(text_dir: Path | None = None) -> pd.DataFrame:
    text_dir = text_dir or INTERIM / "hcup_text"
    records = []
    for year in range(2011, 2021):
        path = text_dir / f"{year}.txt"
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            # State, total SID discharges, community discharges, other discharges,
            # total hospitals in the SID (DSHOSPID).  Later columns are ignored.
            m = re.match(
                r"^\s+([A-Z]{2})\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)", line
            )
            if not m:
                continue
            g = m.groups()
            records.append(
                {
                    "year": year,
                    "state_abbr": g[0],
                    "hospitals_sid": int(g[4].replace(",", "")),
                    "hospitals_community_sid": np.nan,
                    "hospitals_noncommunity_sid": np.nan,
                    "hospitals_not_in_sid": np.nan,
                    "source": "HCUP PDF report",
                }
            )
    return pd.DataFrame(records)


def build_hcup() -> pd.DataFrame:
    html = parse_hcup_html()
    pdf = parse_hcup_pdfs()
    df = pd.concat([html, pdf], ignore_index=True)
    df = df[df.year.between(1999, 2020)].copy()
    df = df[df.state_abbr.isin(ABBR_TO_NAME)].copy()
    df["state"] = df.state_abbr.map(ABBR_TO_NAME)
    # Drop exact duplicates (some reports repeat a table across pages)
    df = df.sort_values(["year", "state_abbr"]).drop_duplicates(
        ["year", "state_abbr"], keep="first"
    )
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# BRFSS state covariates
# ---------------------------------------------------------------------------
def load_brfss() -> pd.DataFrame:
    frames = []
    for name in ["brfss_dttw-5yxu.json", "brfss_y4ft-s73h.json"]:
        path = RAW / "CDC_BRFSS" / name
        frames.append(pd.DataFrame(json.loads(path.read_text())))
    df = pd.concat(frames, ignore_index=True)
    df["year"] = pd.to_numeric(df.year, errors="coerce")
    df["value"] = pd.to_numeric(df.data_value, errors="coerce")
    df["state_abbr"] = df["locationabbr"]
    df["response"] = df["response"].astype(str)
    df = df[df.year.between(1999, 2020)]
    df = df[df.state_abbr.isin(ABBR_TO_NAME)]
    return df


def build_brfss_panel() -> pd.DataFrame:
    df = load_brfss()

    def pick(question_ids: list[str], response_test, label: str) -> pd.DataFrame:
        sub = df[
            df.questionid.isin(question_ids) & df.response.str.contains(response_test, case=False, na=False)
        ].copy()
        # Prefer the first (most modern) question id, then average duplicates.
        sub["priority"] = sub.questionid.map({q: i for i, q in enumerate(question_ids)})
        sub = sub.sort_values(["state_abbr", "year", "priority"])
        sub = sub.drop_duplicates(["state_abbr", "year"], keep="first")
        return sub[["state_abbr", "year", "value"]].rename(columns={"value": label})

    smoking = pick(["_RFSMOK3", "_RFSMOK2"], r"^Yes$", "smoking_pct")
    obesity = pick(
        ["_BMI5CAT", "_BMI4CAT", "_BMI2CAT"], r"^Obese", "obesity_pct"
    )
    uninsured = pick(["HLTHPLN1", "HLTHPLAN"], r"^No$", "uninsured_pct")
    out = smoking.merge(obesity, on=["state_abbr", "year"], how="outer").merge(
        uninsured, on=["state_abbr", "year"], how="outer"
    )
    return out.sort_values(["state_abbr", "year"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# USDA ERS meat availability
# ---------------------------------------------------------------------------
def build_meat() -> pd.DataFrame:
    path = RAW / "USDA_meat" / "mtpcc.csv"
    df = pd.read_csv(path)
    df = df[df.Commodity == "Red meat and poultry (carcass weight): Per capita availability"]
    wide = df.pivot_table(index="Year", columns="Attribute", values="Value", aggfunc="first")
    out = pd.DataFrame(
        {
            "year": wide.index.astype(int),
            "red_meat_lb_pc": wide.get("Red meat-Total-Pounds"),
            "poultry_lb_pc": wide.get("Poultry-Total-Pounds"),
            "total_meat_lb_pc": wide.get("Total-Pounds"),
        }
    )
    # USDA publishes the 2021 value; the analysis stops at 2020.
    return out[out.year.between(1909, 2021)].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Analysis panel
# ---------------------------------------------------------------------------
def build_panel() -> pd.DataFrame:
    crc = parse_crc_state_year()
    early = parse_crc_state_early()
    hcup = build_hcup()
    brfss = build_brfss_panel()
    meat = build_meat()

    panel = crc.merge(
        hcup[["year", "state_abbr", "hospitals_sid", "source"]],
        on=["year", "state_abbr"],
        how="left",
    ).merge(brfss, on=["state_abbr", "year"], how="left")
    panel = panel.merge(
        early[["year", "state_abbr", "crc_early_cases", "crc_early_population", "crc_early_rate"]],
        on=["year", "state_abbr"],
        how="left",
    )
    panel = panel.merge(STATE_DF[["state_abbr", "region"]], on="state_abbr", how="left")

    panel = panel.merge(meat, on="year", how="left")
    for lag in [5, 10, 15, 20]:
        lagged = meat[["year", "red_meat_lb_pc", "poultry_lb_pc"]].copy()
        lagged["year"] = lagged.year + lag
        lagged = lagged.rename(
            columns={
                "red_meat_lb_pc": f"red_meat_lag{lag}",
                "poultry_lb_pc": f"poultry_lag{lag}",
            }
        )
        panel = panel.merge(lagged, on="year", how="left")

    panel["hospitals_per100k"] = panel.hospitals_sid / panel.population * 100_000
    panel["log_population"] = np.log(panel.population)

    # State baseline burden: first observed age-adjusted rate (usually 1999).
    baseline = (
        panel.sort_values("year")
        .groupby("state_abbr")
        .crc_age_adj_rate.first()
        .rename("crc_rate_baseline")
    )
    panel = panel.merge(baseline, on="state_abbr", how="left")
    panel["crc_rate_change"] = panel.crc_age_adj_rate - panel.crc_rate_baseline

    early_baseline = (
        panel.sort_values("year")
        .groupby("state_abbr")
        .crc_early_rate.first()
        .rename("crc_early_rate_baseline")
    )
    panel = panel.merge(early_baseline, on="state_abbr", how="left")
    panel["crc_early_change"] = panel.crc_early_rate - panel.crc_early_rate_baseline

    # Change in hospital density relative to the state's first observed year.
    first_hosp = (
        panel.dropna(subset=["hospitals_per100k"])
        .sort_values("year")
        .groupby("state_abbr")
        .hospitals_per100k.first()
        .rename("hospitals_per100k_baseline")
    )
    panel = panel.merge(first_hosp, on="state_abbr", how="left")
    panel["hospitals_per100k_change"] = panel.hospitals_per100k - panel.hospitals_per100k_baseline

    return panel.sort_values(["state_abbr", "year"]).reset_index(drop=True)


def main() -> None:
    crc_state = parse_crc_state_year()
    crc_early = parse_crc_state_early()
    crc_nat = parse_crc_national()
    age5, ageband = parse_crc_national_age()
    hcup = build_hcup()
    brfss = build_brfss_panel()
    meat = build_meat()
    panel = build_panel()

    crc_state.to_csv(CLEAN / "crc_state_year_1999_2020.csv", index=False)
    crc_early.to_csv(CLEAN / "crc_state_early_1999_2020.csv", index=False)
    crc_nat.to_csv(CLEAN / "crc_national_1999_2020.csv", index=False)
    age5.to_csv(CLEAN / "crc_national_age5_1999_2020.csv", index=False)
    ageband.to_csv(CLEAN / "crc_national_ageband_1999_2020.csv", index=False)
    hcup.to_csv(CLEAN / "hcup_sid_hospitals_1999_2020.csv", index=False)
    brfss.to_csv(CLEAN / "brfss_state_covariates_1999_2020.csv", index=False)
    meat.to_csv(CLEAN / "usda_meat_per_capita_1909_2021.csv", index=False)
    panel.to_csv(CLEAN / "analysis_panel_1999_2020.csv", index=False)

    ranking = (
        panel.sort_values("year")
        .groupby("state_abbr")
        .agg(
            state=("state", "first"),
            region=("region", "first"),
            first_year=("year", "first"),
            last_year=("year", "last"),
            early_rate_first=("crc_early_rate", "first"),
            early_rate_last=("crc_early_rate", "last"),
        )
        .dropna(subset=["early_rate_first", "early_rate_last"])
    )
    ranking["early_change"] = ranking.early_rate_last - ranking.early_rate_first
    ranking["early_change_pct"] = ranking.early_rate_last / ranking.early_rate_first - 1
    ranking.sort_values("early_change", ascending=False).to_csv(
        CLEAN / "state_early_change_ranking.csv"
    )

    print(f"CRC state-year rows: {len(crc_state):,}")
    print(f"CRC national years: {len(crc_nat):,}")
    print(f"HCUP state-year rows: {len(hcup):,} ({hcup.state_abbr.nunique()} states)")
    print(f"BRFSS rows: {len(brfss):,}")
    print(f"Panel rows: {len(panel):,}")
    print(panel[["crc_age_adj_rate", "hospitals_per100k", "smoking_pct", "obesity_pct", "uninsured_pct", "red_meat_lb_pc"]].describe().round(2))


if __name__ == "__main__":
    main()
