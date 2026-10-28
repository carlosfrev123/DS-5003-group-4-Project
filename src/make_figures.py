"""Create the figures used in the report and notebooks."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "outputs" / "cleaned"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

# Consistent visual language
RED = "#B03A2E"
AMBER = "#D68910"
NAVY = "#1F4E79"
TEAL = "#117A65"
PURPLE = "#6C3483"
GREY = "#7F8C8D"
LIGHT_GREY = "#D5D8DC"
REGION_COLORS = {
    "Northeast": "#2E86C1",
    "Midwest": "#CA6F1E",
    "South": "#C0392B",
    "West": "#117A65",
}

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.titleweight": "bold",
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#4D5656",
        "axes.linewidth": 0.6,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.03,
    }
)


def load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    panel = pd.read_csv(CLEAN / "analysis_panel_1999_2020.csv")
    nat = pd.read_csv(CLEAN / "crc_national_1999_2020.csv")
    age = pd.read_csv(CLEAN / "crc_national_ageband_1999_2020.csv")
    meat = pd.read_csv(CLEAN / "usda_meat_per_capita_1909_2021.csv")
    return panel, nat, age, meat


def national_early(panel: pd.DataFrame) -> pd.Series:
    g = panel.groupby("year")[["crc_early_cases", "crc_early_population"]].sum()
    return (g.crc_early_cases / g.crc_early_population * 100_000).rename("crc_early_rate")


def year_axis(ax, ticks=(1999, 2005, 2010, 2015, 2020)) -> None:
    ax.set_xticks(list(ticks))
    ax.set_xticklabels([str(t) for t in ticks])


def fig1_national_trends(panel, nat, meat) -> Path:
    m = meat[meat.year.between(1999, 2020)]
    early = national_early(panel)

    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.55))

    ax = axes[0]
    ax.plot(m.year, m.red_meat_lb_pc, color=RED, lw=1.8, label="Red meat")
    ax.plot(m.year, m.poultry_lb_pc, color=AMBER, lw=1.8, label="Poultry")
    ax.set_ylabel("Pounds per person per year")
    ax.set_title("a. Per capita meat availability")
    ax.set_xlim(1999, 2020)
    year_axis(ax)
    ax.set_ylim(90, 175)
    ax.grid(axis="y", color=LIGHT_GREY, lw=0.5)
    ax.legend(loc="center left", frameon=False)
    ax.annotate(
        f"{m.red_meat_lb_pc.iloc[-1]:.0f} lb\n({m.red_meat_lb_pc.iloc[-1]/m.red_meat_lb_pc.iloc[0]-1:+.0%})",
        xy=(2020, m.red_meat_lb_pc.iloc[-1]),
        xytext=(2015.4, 160),
        fontsize=6.5,
        color=RED,
        arrowprops=dict(arrowstyle="-", color=RED, lw=0.6),
    )
    ax.annotate(
        f"{m.poultry_lb_pc.iloc[-1]:.0f} lb\n({m.poultry_lb_pc.iloc[-1]/m.poultry_lb_pc.iloc[0]-1:+.0%})",
        xy=(2020, m.poultry_lb_pc.iloc[-1]),
        xytext=(2014.2, 103),
        fontsize=6.5,
        color=AMBER,
        arrowprops=dict(arrowstyle="-", color=AMBER, lw=0.6),
    )

    ax = axes[1]
    idx_red = m.red_meat_lb_pc / m.red_meat_lb_pc.iloc[0] * 100
    idx_crc = nat.crc_age_adj_rate / nat.crc_age_adj_rate.iloc[0] * 100
    idx_early = early / early.iloc[0] * 100
    ax.axhline(100, color=GREY, lw=0.6, ls=":")
    ax.plot(m.year, idx_red, color=RED, lw=1.4, ls="--", label="Red meat availability")
    ax.plot(nat.year, idx_crc, color=NAVY, lw=1.9, label="CRC, all ages (age-adjusted)")
    ax.plot(early.index, idx_early, color=PURPLE, lw=1.9, label="CRC, ages 20-49")
    ax.set_ylabel("Index (1999 = 100)")
    ax.set_title("b. Colorectal cancer vs. red meat")
    ax.set_xlim(1999, 2020)
    year_axis(ax)
    ax.set_ylim(55, 145)
    ax.grid(axis="y", color=LIGHT_GREY, lw=0.5)
    ax.legend(loc="lower left", frameon=False, fontsize=6.2)
    ax.annotate(f"{idx_crc.iloc[-1]:.0f}", xy=(2020, idx_crc.iloc[-1]), xytext=(2020.6, idx_crc.iloc[-1]), fontsize=6.5, color=NAVY, va="center")
    ax.annotate(f"{idx_early.iloc[-1]:.0f}", xy=(2020, idx_early.iloc[-1]), xytext=(2020.6, idx_early.iloc[-1]), fontsize=6.5, color=PURPLE, va="center")
    ax.annotate(f"{idx_red.iloc[-1]:.0f}", xy=(2020, idx_red.iloc[-1]), xytext=(2020.6, idx_red.iloc[-1]), fontsize=6.5, color=RED, va="center")

    fig.tight_layout(w_pad=1.4)
    path = FIG / "fig1_national_trends.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig2_age_specific(age: pd.DataFrame) -> Path:
    pivot = age.pivot(index="year", columns="age_band", values="crc_crude_rate")
    fig, ax = plt.subplots(figsize=(4.6, 2.55))
    colors = {"20-49": PURPLE, "50-64": "#2E86C1", "65+": GREY}
    for band in ["20-49", "50-64", "65+"]:
        ax.plot(pivot.index, pivot[band], color=colors[band], lw=1.9, label=f"Ages {band}")
    ax.set_yscale("log")
    ax.set_yticks([5, 10, 20, 50, 100, 200, 400])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_ylabel("New cases per 100,000 (log scale)")
    ax.set_xlabel("Year")
    ax.set_xlim(1999, 2020)
    year_axis(ax, ticks=(1999, 2004, 2009, 2014, 2020))
    ax.grid(axis="y", color=LIGHT_GREY, lw=0.5)
    ax.legend(loc="lower left", frameon=False, ncol=3, columnspacing=0.8, handlelength=1.2)
    ax.axvspan(2019.5, 2020.5, color=LIGHT_GREY, alpha=0.45, lw=0)
    ax.text(2020, 8, "2020", ha="center", va="bottom", fontsize=6, color=GREY)
    # end labels with % change
    for band, yoff in [("20-49", 1.06), ("50-64", 1.06), ("65+", 1.06)]:
        chg = pivot[band].iloc[-1] / pivot[band].iloc[0] - 1
        ax.annotate(
            f"{chg:+.0%}",
            xy=(2020, pivot[band].iloc[-1] * yoff),
            fontsize=6.5,
            color=colors[band],
            ha="left",
            va="center",
        )
    fig.tight_layout()
    path = FIG / "fig2_age_specific.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig3_states_hospitals(panel: pd.DataFrame) -> Path:
    # State change in early-onset CRC, first vs last year
    s = (
        panel.sort_values("year")
        .groupby("state_abbr")
        .agg(
            first=("crc_early_rate", "first"),
            last=("crc_early_rate", "last"),
            region=("region", "first"),
        )
        .dropna()
    )
    s["change"] = s["last"] - s["first"]
    s = s.sort_values("change")

    # For readability show the largest increases and the declines; the full
    # 51-state ranking is in the cleaned data and the notebook.
    selected = pd.concat([s.head(8), s.tail(12)]).drop_duplicates().sort_values("change")

    fig, axes = plt.subplots(
        1, 2, figsize=(7.2, 3.2), gridspec_kw={"width_ratios": [1.55, 1.0]}
    )

    ax = axes[0]
    colors = [TEAL if v < 0 else RED for v in selected["change"]]
    ax.barh(selected.index, selected["change"], color=colors, height=0.72)
    ax.axvline(0, color="black", lw=0.6)
    ax.axvline(s["change"].mean(), color=GREY, lw=0.8, ls="--")
    ax.set_xlabel("Change in rate per 100,000 (ages 20-49)")
    ax.set_title("a. Early-onset CRC change, selected states")
    ax.tick_params(axis="y", labelsize=7.0, length=0)
    ax.tick_params(axis="x", labelsize=6.5)
    ax.grid(axis="x", color=LIGHT_GREY, lw=0.5)
    ax.set_xlim(min(selected["change"]) - 0.8, max(selected["change"]) + 1.6)
    ax.text(
        0.99,
        0.04,
        "48 of 51 states increased\n(full ranking in data file)",
        transform=ax.transAxes,
        fontsize=5.8,
        va="bottom",
        ha="right",
        color=GREY,
    )

    # Hospital density boxplots
    ax = axes[1]
    years = [1999, 2004, 2009, 2014, 2020]
    data = [
        panel.loc[panel.year == y, "hospitals_per100k"].dropna().values for y in years
    ]
    bp = ax.boxplot(
        data,
        positions=range(len(years)),
        widths=0.55,
        patch_artist=True,
        showfliers=True,
        flierprops=dict(marker="o", markersize=2, markerfacecolor=GREY, markeredgewidth=0),
        medianprops=dict(color="black", lw=1.1),
        whiskerprops=dict(color="#4D5656", lw=0.7),
        capprops=dict(color="#4D5656", lw=0.7),
    )
    for patch in bp["boxes"]:
        patch.set_facecolor("#AED6F1")
        patch.set_edgecolor("#2E86C1")
        patch.set_linewidth(0.7)
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels([f"{y}\n(n={len(d)})" for y, d in zip(years, data)], fontsize=6.5)
    ax.set_ylabel("Hospitals per 100,000 residents")
    ax.set_title("b. Hospital supply in SID states")
    ax.grid(axis="y", color=LIGHT_GREY, lw=0.5)
    ax.text(
        0.02,
        0.03,
        "Box = IQR; line = median; dots = outliers",
        transform=ax.transAxes,
        fontsize=5.8,
        va="bottom",
        color=GREY,
    )

    fig.tight_layout(w_pad=1.2)
    path = FIG / "fig3_states_hospitals.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig4_model(importance: pd.DataFrame, preds: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.7), gridspec_kw={"width_ratios": [1.15, 1.0]})

    ax = axes[0]
    imp = importance.head(9).iloc[::-1]
    labels = {
        "crc_early_rate_baseline": "State baseline rate (1999)",
        "year": "Year",
        "obesity_pct": "Adult obesity (%)",
        "log_population": "Population (log)",
        "smoking_pct": "Adult smoking (%)",
        "region": "Census region",
        "uninsured_pct": "Uninsured (%)",
        "poultry_lb_pc": "Poultry availability",
        "red_meat_lb_pc": "Red meat availability",
    }
    colors = [RED if f in ("red_meat_lb_pc", "poultry_lb_pc") else NAVY for f in imp.feature]
    ax.barh([labels.get(f, f) for f in imp.feature], imp.importance_mean, color=colors, height=0.7)
    ax.set_xlabel("Permutation importance (drop in R²)")
    ax.set_title("a. What drives the model?")
    ax.tick_params(axis="y", labelsize=6.6, length=0)
    ax.grid(axis="x", color=LIGHT_GREY, lw=0.5)

    ax = axes[1]
    sc = ax.scatter(
        preds.crc_early_rate,
        preds.prediction,
        c=preds.year,
        cmap="viridis",
        s=18,
        alpha=0.85,
        edgecolor="white",
        linewidth=0.3,
    )
    lo = min(preds.crc_early_rate.min(), preds.prediction.min()) - 0.5
    hi = max(preds.crc_early_rate.max(), preds.prediction.max()) + 0.5
    ax.plot([lo, hi], [lo, hi], color=GREY, lw=0.8, ls="--")
    ax.set_xlabel("Observed rate per 100,000 (ages 20-49)")
    ax.set_ylabel("Predicted rate per 100,000")
    ax.set_title("b. 2017-2020 holdout")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.grid(color=LIGHT_GREY, lw=0.5)
    r2 = 1 - ((preds.crc_early_rate - preds.prediction) ** 2).sum() / (
        (preds.crc_early_rate - preds.crc_early_rate.mean()) ** 2
    ).sum()
    mae = (preds.crc_early_rate - preds.prediction).abs().mean()
    ax.text(
        0.04,
        0.96,
        f"R² = {r2:.2f}\nMAE = {mae:.2f}",
        transform=ax.transAxes,
        va="top",
        fontsize=7,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=LIGHT_GREY, lw=0.5),
    )
    cbar = fig.colorbar(sc, ax=ax, ticks=[2017, 2018, 2019, 2020], pad=0.02, fraction=0.05)
    cbar.ax.tick_params(labelsize=6)
    cbar.outline.set_linewidth(0.4)

    fig.tight_layout(w_pad=1.2)
    path = FIG / "fig4_model.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def main() -> None:
    panel, nat, age, meat = load()
    importance = pd.read_csv(CLEAN / "model_permutation_importance_full.csv")
    preds = pd.read_csv(CLEAN / "model_test_predictions.csv")
    # Use full-data importance for the report figure (the holdout version is
    # nearly identical for the meat variables, but year is uninformative when
    # the model cannot extrapolate beyond the training window).
    import subprocess

    print(fig1_national_trends(panel, nat, meat))
    print(fig2_age_specific(age))
    print(fig3_states_hospitals(panel))
    print(fig4_model(importance, preds))


if __name__ == "__main__":
    main()
