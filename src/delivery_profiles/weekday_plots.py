from __future__ import annotations

from pathlib import Path
import ast
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
WEEKDAY_ORDER = [0, 1, 2, 3, 4]


def ensure_weekday(df: pd.DataFrame, date_col: str = "Loading_Date") -> pd.DataFrame:
    out = df.copy()
    if "Weekday" in out.columns:
        return out
    if date_col not in out.columns:
        raise KeyError(f"Need either 'Weekday' or '{date_col}' column for weekday plots.")
    out[date_col] = pd.to_datetime(out[date_col])
    out["Weekday"] = out[date_col].dt.dayofweek
    return out


def _safe_parse_list(x):
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except Exception:
            return None
    return None


def plot_demand_percentage(df_demand: pd.DataFrame, run_name: str, clustered: str = "Non-Clustered"):
    df = df_demand.copy()

    # robust parse
    if "Pattern_clear" in df.columns:
        df["Pattern_clear"] = df["Pattern_clear"].apply(_safe_parse_list)
        df = df[df["Pattern_clear"].notna()].copy()

        for i, day in enumerate(DAYS):
            df[day] = df["Pattern_clear"].apply(lambda x: x[i])

    # compute demand per day
    demand_per_day = {}
    for i, day in enumerate(DAYS):
        demand_per_day[day] = float(df.loc[df[day] == 1, "Demand"].sum()) if day in df.columns else 0.0

    total = sum(demand_per_day.values()) or 1.0
    perc = pd.Series({k: (v / total) * 100 for k, v in demand_per_day.items()})

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(perc.index, perc.values, width=0.5)
    ax.set_xlabel("Days of the Week")
    ax.set_ylabel("Percentage Demand (%)")
    ax.set_title(f"Percentage Demand per Day ({run_name} - {clustered})")
    ax.set_yticks([0, 5, 10, 15, 20, 25])
    ax.set_yticklabels([f"{t}%" for t in [0, 5, 10, 15, 20, 25]])
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    for x, y in zip(perc.index, perc.values):
        ax.text(x, y + 0.4, f"{y:.1f}%", ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    return fig


def plot_weight_profile_comparison(
    data_profile: pd.DataFrame,
    data_notprofile: pd.DataFrame,
    run_name: str,
    database_label: str,
    clustered: str = "Non-Clustered",
):
    prof = ensure_weekday(data_profile)
    base = ensure_weekday(data_notprofile)

    prof["Weight"] = pd.to_numeric(prof["Weight"], errors="coerce").fillna(0.0)
    base["Weight"] = pd.to_numeric(base["Weight"], errors="coerce").fillna(0.0)

    w_prof = (prof.groupby("Weekday")["Weight"].sum()).reindex(WEEKDAY_ORDER).fillna(0.0)
    w_base = (base.groupby("Weekday")["Weight"].sum()).reindex(WEEKDAY_ORDER).fillna(0.0)

    p_prof = (w_prof / (w_prof.sum() or 1.0)) * 100
    p_base = (w_base / (w_base.sum() or 1.0)) * 100

    x = np.arange(len(DAYS))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - width/2, p_base.values, width, label="Without Profiles", align="center")
    ax.bar(x + width/2, p_prof.values, width, label="With Profiles", align="center")

    for i in range(len(DAYS)):
        ax.text(x[i] - width/2, p_base.values[i] + 0.4, f"{p_base.values[i]:.1f}%", ha="center", fontsize=9)
        ax.text(x[i] + width/2, p_prof.values[i] + 0.4, f"{p_prof.values[i]:.1f}%", ha="center", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(DAYS)
    ax.set_xlabel("Days of the Week")
    ax.set_ylabel("Percentage Weight (%)")
    ax.set_title(f"Percentage Weight with and without Profiles per Day ({database_label} - {run_name} - {clustered})")
    ax.set_yticks([0, 5, 10, 15, 20, 25, 30])
    ax.set_yticklabels([f"{t}%" for t in [0, 5, 10, 15, 20, 25, 30]])
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend()
    fig.tight_layout()
    return fig


def write_weekday_plots_pdf(
    *,
    df_demand: pd.DataFrame,
    df_profile: pd.DataFrame,
    df_notprofile: pd.DataFrame,
    df_result: pd.DataFrame,
    df_full: pd.DataFrame,
    out_pdf: str | Path,
    run_name: str,
    clustered: str = "Non-Clustered",
):
    out_pdf = Path(out_pdf)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    # Ensure weekday everywhere
    df_full = ensure_weekday(df_full)
    df_result = ensure_weekday(df_result)
    df_profile = ensure_weekday(df_profile)
    df_notprofile = ensure_weekday(df_notprofile)

    with PdfPages(out_pdf, keep_empty=False) as pp:
        fig1 = plot_demand_percentage(df_demand, run_name, clustered)
        fig2 = plot_weight_profile_comparison(df_profile, df_notprofile, run_name, "Only Profiles", clustered)
        fig3 = plot_weight_profile_comparison(df_result, df_full, run_name, "Full Data", clustered)

        pp.savefig(fig1, bbox_inches="tight")
        pp.savefig(fig2, bbox_inches="tight")
        pp.savefig(fig3, bbox_inches="tight")

        plt.close(fig1)
        plt.close(fig2)
        plt.close(fig3)


WEEKDAY_FULL_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def plot_freight_cost_comparison(
    df_original: pd.DataFrame,
    df_profiled: pd.DataFrame,
    df_clustered: pd.DataFrame | None = None,
    *,
    freight_cost_col: str = "Freight_Cost",
) -> plt.Figure:
    """
    Bar chart showing freight cost % per weekday for up to three scenarios:
      Without Profiles / With Profiles / Clustered Profiles (optional).

    Fixes vs legacy freight_cost_comparison_plot():
      - df_original is a DataFrame, not a file path
      - All series reindexed to Mon-Fri so a missing weekday never crashes
      - Bar labels positioned relative to the percentage value, not the absolute cost
      - No seaborn dependency
      - Returns the figure; caller decides whether to save or show
    """
    def _pct_by_weekday(df: pd.DataFrame) -> pd.Series:
        df = ensure_weekday(df.copy())
        df[freight_cost_col] = pd.to_numeric(df[freight_cost_col], errors="coerce")
        totals = (
            df.groupby("Weekday")[freight_cost_col]
            .sum()
            .reindex(WEEKDAY_ORDER)
            .fillna(0.0)
        )
        grand = totals.sum() or 1.0
        return (totals / grand) * 100.0

    pct_orig = _pct_by_weekday(df_original)
    pct_prof = _pct_by_weekday(df_profiled)
    pct_clus = _pct_by_weekday(df_clustered) if df_clustered is not None else None

    has_clustered = pct_clus is not None
    n_series = 3 if has_clustered else 2
    bar_w = 0.25 if has_clustered else 0.35
    x = np.arange(len(WEEKDAY_ORDER))
    offsets = np.linspace(-(n_series - 1) / 2.0 * bar_w, (n_series - 1) / 2.0 * bar_w, n_series)

    # Colours match legacy intent without seaborn
    col_clus = "#4C72B0"   # blue  — Clustered Profiles
    col_prof = "#55A868"   # green — Profiles Only
    col_orig = "#C44E52"   # red   — Without Profiles

    fig, ax = plt.subplots(figsize=(10, 6))

    series = []
    if has_clustered:
        series = [
            (pct_clus.values, offsets[0], "Clustered Profiles", col_clus),
            (pct_prof.values, offsets[1], "Profiles Only",      col_prof),
            (pct_orig.values, offsets[2], "Without Profiles",   col_orig),
        ]
    else:
        series = [
            (pct_prof.values, offsets[0], "Profiles Only",    col_prof),
            (pct_orig.values, offsets[1], "Without Profiles", col_orig),
        ]

    for vals, offset, label, color in series:
        ax.bar(x + offset, vals, bar_w, label=label, color=color)
        for xi, v in zip(x, vals):
            ax.text(xi + offset, v + 0.3, f"{v:.2f}%", ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(WEEKDAY_FULL_NAMES)
    ax.set_xlabel("Weekday")
    ax.set_ylabel("Freight Cost (%)")
    ax.set_title("Freight Cost Distribution by Weekday")
    ax.legend()
    fig.tight_layout()
    return fig


def write_freight_cost_comparison_pdf(
    *,
    df_original: pd.DataFrame,
    df_profiled: pd.DataFrame,
    df_clustered: pd.DataFrame | None = None,
    out_pdf: str | Path,
    freight_cost_col: str = "Freight_Cost",
) -> None:
    out_pdf = Path(out_pdf)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    fig = plot_freight_cost_comparison(
        df_original,
        df_profiled,
        df_clustered=df_clustered,
        freight_cost_col=freight_cost_col,
    )
    with PdfPages(out_pdf, keep_empty=False) as pp:
        pp.savefig(fig, bbox_inches="tight")
    plt.close(fig)
