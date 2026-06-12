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
    df_clustered: "pd.DataFrame | None" = None,
    *,
    df_dbscan: "pd.DataFrame | None" = None,
    freight_cost_col: str = "Freight_Cost",
    title: str = "Freight Cost Distribution by Weekday",
) -> plt.Figure:
    """
    Bar chart: freight cost % per weekday for 2-4 scenarios.
    When df_dbscan is supplied, df_clustered is labelled
    'KMeans Clustered' instead of 'Clustered Profiles'.
    """
    def _pct(df: pd.DataFrame) -> pd.Series:
        df = ensure_weekday(df.copy())
        df[freight_cost_col] = pd.to_numeric(df[freight_cost_col], errors="coerce")
        totals = df.groupby("Weekday")[freight_cost_col].sum().reindex(WEEKDAY_ORDER).fillna(0.0)
        return (totals / (totals.sum() or 1.0)) * 100.0

    pct_orig   = _pct(df_original)
    pct_prof   = _pct(df_profiled)
    pct_clus   = _pct(df_clustered)        if df_clustered      is not None else None
    pct_dbscan = _pct(df_dbscan) if df_dbscan is not None else None

    col_dbscan = "#9467BD"   # purple — DBSCAN Clustered
    col_clus   = "#4C72B0"   # blue   — KMeans / Clustered Profiles
    col_prof   = "#55A868"   # green  — Profiles Only
    col_orig   = "#C44E52"   # red    — Without Profiles

    # ordered left→right: DBSCAN → KMeans → Profiles Only → Without Profiles
    all_data = []
    if pct_dbscan is not None:
        all_data.append((pct_dbscan, "DBSCAN Clustered",   col_dbscan))
    if pct_clus is not None:
        lbl = "KMeans Clustered" if pct_dbscan is not None else "Clustered Profiles"
        all_data.append((pct_clus, lbl, col_clus))
    all_data.append((pct_prof, "Profiles Only",    col_prof))
    all_data.append((pct_orig, "Without Profiles", col_orig))

    n     = len(all_data)
    bar_w = {2: 0.35, 3: 0.25, 4: 0.18}.get(n, 0.18)
    x     = np.arange(len(WEEKDAY_ORDER))
    offs  = np.linspace(-(n - 1) / 2.0 * bar_w, (n - 1) / 2.0 * bar_w, n)

    fig, ax = plt.subplots(figsize=(12 if n == 4 else 10, 6))
    lbl_fs  = 7 if n == 4 else 8

    for (pct_s, lbl, color), offset in zip(all_data, offs):
        ax.bar(x + offset, pct_s.values, bar_w, label=lbl, color=color)
        for xi, v in zip(x, pct_s.values):
            ax.text(xi + offset, v + 0.3, f"{v:.1f}%", ha="center", va="bottom", fontsize=lbl_fs)

    ax.set_xticks(x)
    ax.set_xticklabels(WEEKDAY_FULL_NAMES)
    ax.set_xlabel("Weekday")
    ax.set_ylabel("Freight Cost (%)")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    return fig


def write_freight_cost_comparison_pdf(
    *,
    df_original: pd.DataFrame,
    df_profiled: pd.DataFrame,
    df_clustered: "pd.DataFrame | None" = None,
    df_dbscan: "pd.DataFrame | None" = None,
    out_pdf: "str | Path",
    freight_cost_col: str = "Freight_Cost",
    profiled_ids: "set[int] | None" = None,
) -> None:
    """
    Page 1: fleet-wide freight cost distribution across all three scenarios.
    Page 2 (only when profiled_ids is supplied): same chart filtered to profiled
            recipients only, so the optimiser's effect is not diluted by the
            unchanged majority.
    """
    out_pdf = Path(out_pdf)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    fig_fleet = plot_freight_cost_comparison(
        df_original,
        df_profiled,
        df_clustered=df_clustered,
        df_dbscan=df_dbscan,
        freight_cost_col=freight_cost_col,
        title="Freight Cost Distribution by Weekday — Full Fleet",
    )

    with PdfPages(out_pdf, keep_empty=False) as pp:
        pp.savefig(fig_fleet, bbox_inches="tight")
        plt.close(fig_fleet)

        if profiled_ids:
            def _filter(df: pd.DataFrame) -> pd.DataFrame:
                if "Recipient_ID" not in df.columns:
                    return df.copy()
                numeric = pd.to_numeric(df["Recipient_ID"], errors="coerce").fillna(-1).astype(int)
                return df[numeric.isin(profiled_ids)].copy()

            fig_subset = plot_freight_cost_comparison(
                _filter(df_original),
                _filter(df_profiled),
                df_clustered=_filter(df_clustered) if df_clustered is not None else None,
                df_dbscan=_filter(df_dbscan) if df_dbscan is not None else None,
                freight_cost_col=freight_cost_col,
                title=f"Freight Cost Distribution by Weekday — Profiled Recipients Only (n={len(profiled_ids)})",
            )
            pp.savefig(fig_subset, bbox_inches="tight")
            plt.close(fig_subset)


def plot_weight_distribution_comparison(
    df_original: pd.DataFrame,
    df_profiled: pd.DataFrame,
    df_clustered: "pd.DataFrame | None" = None,
    *,
    df_dbscan: "pd.DataFrame | None" = None,
    weight_col: str = "Weight",
    title: str = "Weight Distribution by Weekday",
) -> plt.Figure:
    """
    Bar chart: weight % per weekday for 2-4 scenarios.
    When df_dbscan is supplied, df_clustered is labelled
    'KMeans Clustered' instead of 'Clustered Profiles'.
    """
    def _pct(df: pd.DataFrame) -> pd.Series:
        df = ensure_weekday(df.copy())
        df[weight_col] = pd.to_numeric(df[weight_col], errors="coerce")
        totals = df.groupby("Weekday")[weight_col].sum().reindex(WEEKDAY_ORDER).fillna(0.0)
        return (totals / (totals.sum() or 1.0)) * 100.0

    pct_orig   = _pct(df_original)
    pct_prof   = _pct(df_profiled)
    pct_clus   = _pct(df_clustered)        if df_clustered      is not None else None
    pct_dbscan = _pct(df_dbscan) if df_dbscan is not None else None

    col_dbscan = "#9467BD"
    col_clus   = "#4C72B0"
    col_prof   = "#55A868"
    col_orig   = "#C44E52"

    all_data = []
    if pct_dbscan is not None:
        all_data.append((pct_dbscan, "DBSCAN Clustered",   col_dbscan))
    if pct_clus is not None:
        lbl = "KMeans Clustered" if pct_dbscan is not None else "Clustered Profiles"
        all_data.append((pct_clus, lbl, col_clus))
    all_data.append((pct_prof, "Profiles Only",    col_prof))
    all_data.append((pct_orig, "Without Profiles", col_orig))

    n     = len(all_data)
    bar_w = {2: 0.35, 3: 0.25, 4: 0.18}.get(n, 0.18)
    x     = np.arange(len(WEEKDAY_ORDER))
    offs  = np.linspace(-(n - 1) / 2.0 * bar_w, (n - 1) / 2.0 * bar_w, n)

    fig, ax = plt.subplots(figsize=(12 if n == 4 else 10, 6))
    lbl_fs  = 7 if n == 4 else 8

    for (pct_s, lbl, color), offset in zip(all_data, offs):
        ax.bar(x + offset, pct_s.values, bar_w, label=lbl, color=color)
        for xi, v in zip(x, pct_s.values):
            ax.text(xi + offset, v + 0.3, f"{v:.1f}%", ha="center", va="bottom", fontsize=lbl_fs)

    ax.set_xticks(x)
    ax.set_xticklabels(WEEKDAY_FULL_NAMES)
    ax.set_xlabel("Weekday")
    ax.set_ylabel("Weight (%)")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    return fig


def write_weight_distribution_pdf(
    *,
    df_original: pd.DataFrame,
    df_profiled: pd.DataFrame,
    df_clustered: "pd.DataFrame | None" = None,
    df_dbscan: "pd.DataFrame | None" = None,
    out_pdf: "str | Path",
    weight_col: str = "Weight",
    profiled_ids: "set[int] | None" = None,
) -> None:
    """
    Page 1: fleet-wide weight distribution across all three scenarios.
    Page 2 (only when profiled_ids is supplied): same chart filtered to
            profiled recipients only.
    """
    out_pdf = Path(out_pdf)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    fig_fleet = plot_weight_distribution_comparison(
        df_original,
        df_profiled,
        df_clustered=df_clustered,
        df_dbscan=df_dbscan,
        weight_col=weight_col,
        title="Weight Distribution by Weekday — Full Fleet",
    )

    with PdfPages(out_pdf, keep_empty=False) as pp:
        pp.savefig(fig_fleet, bbox_inches="tight")
        plt.close(fig_fleet)

        if profiled_ids:
            def _filter(df: pd.DataFrame) -> pd.DataFrame:
                if "Recipient_ID" not in df.columns:
                    return df.copy()
                numeric = pd.to_numeric(df["Recipient_ID"], errors="coerce").fillna(-1).astype(int)
                return df[numeric.isin(profiled_ids)].copy()

            fig_subset = plot_weight_distribution_comparison(
                _filter(df_original),
                _filter(df_profiled),
                df_clustered=_filter(df_clustered) if df_clustered is not None else None,
                df_dbscan=_filter(df_dbscan) if df_dbscan is not None else None,
                weight_col=weight_col,
                title=f"Weight Distribution by Weekday — Profiled Recipients Only (n={len(profiled_ids)})",
            )
            pp.savefig(fig_subset, bbox_inches="tight")
            plt.close(fig_subset)


# ============================================================================
# Pipeline savings summary (console + txt + PDF)
# ============================================================================

def _pct_by_col(df: pd.DataFrame, col: str) -> pd.Series:
    """Returns column % per weekday (Mon=0 … Fri=4), reindexed to all five days."""
    df = ensure_weekday(df.copy())
    df[col] = pd.to_numeric(df[col], errors="coerce")
    totals = df.groupby("Weekday")[col].sum().reindex(WEEKDAY_ORDER).fillna(0.0)
    grand = totals.sum() or 1.0
    return (totals / grand) * 100.0


def _splitting_stats(pattern_only: "pd.DataFrame | None") -> "tuple[int, int]":
    """(n_recipients_split, n_extra_truck_dispatches) from pattern_only rows."""
    if pattern_only is None or pattern_only.empty or "Truck_Number" not in pattern_only.columns:
        return 0, 0
    mask = pattern_only["Truck_Number"] > 1
    return int(pattern_only.loc[mask, "Recipient_ID"].nunique()), int(mask.sum())


def _build_summary_metrics(
    *,
    df_original: pd.DataFrame,
    df_best: pd.DataFrame,
    df_var: pd.DataFrame,
    profiled_ids: "set[int]",
    pattern_only_best: "pd.DataFrame | None",
    var_weight_max: float,
    var_frequency_max: float,
    min_frequency: float,
    max_truck_weight: float,
    best_label: str,
) -> dict:
    n_total = len(df_var)
    n_profiled = len(profiled_ids)
    pct_profiled = n_profiled / n_total * 100.0 if n_total > 0 else 0.0

    if "Freight_Cost" in df_var.columns:
        total_cost = float(df_var["Freight_Cost"].sum())
        rid_num = pd.to_numeric(df_var["Recipient_ID"], errors="coerce").fillna(-1).astype(int)
        covered_cost = float(df_var.loc[rid_num.isin(profiled_ids), "Freight_Cost"].sum())
    else:
        total_cost = covered_cost = 0.0
    pct_cost_coverage = covered_cost / total_cost * 100.0 if total_cost > 0 else 0.0

    w_before = _pct_by_col(df_original, "Weight")
    w_after  = _pct_by_col(df_best,     "Weight")
    c_before = _pct_by_col(df_original, "Freight_Cost")
    c_after  = _pct_by_col(df_best,     "Freight_Cost")

    n_split, n_extra = _splitting_stats(pattern_only_best)

    return {
        "n_total":            n_total,
        "n_profiled":         n_profiled,
        "pct_profiled":       pct_profiled,
        "total_cost":         total_cost,
        "covered_cost":       covered_cost,
        "pct_cost_coverage":  pct_cost_coverage,
        # weight
        "mon_w_before":       float(w_before.iloc[0]),
        "mon_w_after":        float(w_after.iloc[0]),
        "fri_w_before":       float(w_before.iloc[4]),
        "fri_w_after":        float(w_after.iloc[4]),
        "max_w_before":       float(w_before.max()),
        "max_w_after":        float(w_after.max()),
        "max_w_day_before":   WEEKDAY_FULL_NAMES[int(w_before.idxmax())],
        "max_w_day_after":    WEEKDAY_FULL_NAMES[int(w_after.idxmax())],
        "peak_reduction_pp":  float(w_before.max()) - float(w_after.max()),
        # freight cost
        "mon_c_before":       float(c_before.iloc[0]),
        "mon_c_after":        float(c_after.iloc[0]),
        "max_c_before":       float(c_before.max()),
        "max_c_after":        float(c_after.max()),
        "max_c_day_before":   WEEKDAY_FULL_NAMES[int(c_before.idxmax())],
        "max_c_day_after":    WEEKDAY_FULL_NAMES[int(c_after.idxmax())],
        # truck splitting
        "n_split_recipients": n_split,
        "n_extra_trucks":     n_extra,
        # thresholds
        "var_weight_max":     var_weight_max,
        "var_frequency_max":  var_frequency_max,
        "min_frequency":      min_frequency,
        "max_truck_weight":   max_truck_weight,
        "best_label":         best_label,
        # raw series carried forward for PDF bar charts
        "w_before": w_before,
        "w_after":  w_after,
    }


def _format_summary_text(m: dict) -> str:
    W = 65
    sep  = "=" * W
    dash = "  " + "-" * (W - 2)

    def row(label: str, value: str) -> str:
        return f"  {label:<30}: {value}"

    lines = [
        sep,
        "  DELIVERY PROFILE PIPELINE SUMMARY",
        sep,
        "",
        "  Recipients",
        dash,
        row("Total recipients",        str(m["n_total"])),
        row("Profiled recipients",      f"{m['n_profiled']}  ({m['pct_profiled']:.1f}%)"),
        row("Freight cost coverage",    f"EUR {m['covered_cost']:>10,.0f} / EUR {m['total_cost']:,.0f}  ({m['pct_cost_coverage']:.1f}%)"),
        "",
        f"  Workload Leveling — Weight  (best: {m['best_label']})",
        dash,
        row("Monday weight  — before",  f"{m['mon_w_before']:5.1f}%"),
        row("Monday weight  — after",   f"{m['mon_w_after']:5.1f}%"),
        row("Friday weight  — before",  f"{m['fri_w_before']:5.1f}%"),
        row("Friday weight  — after",   f"{m['fri_w_after']:5.1f}%"),
        row("Peak daily weight  before", f"{m['max_w_before']:5.1f}%  ({m['max_w_day_before']})"),
        row("Peak daily weight  after",  f"{m['max_w_after']:5.1f}%  ({m['max_w_day_after']})"),
        row("Peak reduction",           f"{m['peak_reduction_pp']:5.1f} pp"),
        "",
        "  Workload Leveling — Freight Cost",
        dash,
        row("Monday cost    — before",  f"{m['mon_c_before']:5.1f}%"),
        row("Monday cost    — after",   f"{m['mon_c_after']:5.1f}%"),
        row("Peak daily cost  before",  f"{m['max_c_before']:5.1f}%  ({m['max_c_day_before']})"),
        row("Peak daily cost  after",   f"{m['max_c_after']:5.1f}%  ({m['max_c_day_after']})"),
        "",
        "  Truck Splitting",
        dash,
        row("Recipients needing split", str(m["n_split_recipients"])),
        row("Total extra trucks",       str(m["n_extra_trucks"])),
        "",
        "  Thresholds Used",
        dash,
        row("var_weight_max",           str(m["var_weight_max"])),
        row("var_frequency_max",        str(m["var_frequency_max"])),
        row("min_frequency",            str(m["min_frequency"])),
        row("max_truck_weight",         f"{m['max_truck_weight']:,.0f} kg"),
        "",
        sep,
    ]
    return "\n".join(lines)


def _write_pipeline_summary_pdf(
    m: dict,
    df_original: pd.DataFrame,
    df_best: pd.DataFrame,
    out_pdf: Path,
) -> None:
    fig = plt.figure(figsize=(12, 12))
    gs = fig.add_gridspec(
        4, 2,
        height_ratios=[0.42, 1.0, 4.2, 3.5],
        hspace=0.50,
        wspace=0.30,
        top=0.97, bottom=0.04, left=0.04, right=0.96,
    )

    # ── Title + run-parameter subtitle ────────────────────────────────────────
    ax_title = fig.add_subplot(gs[0, :])
    ax_title.axis("off")
    subtitle = (
        f"var_weight ≤ {m['var_weight_max']},  "
        f"var_freq ≤ {m['var_frequency_max']},  "
        f"min_frequency ≥ {m['min_frequency']},  "
        f"{m['n_profiled']:,} / {m['n_total']:,} recipients profiled"
    )
    ax_title.text(
        0.5, 0.80, "Pipeline Summary Report",
        ha="center", va="center",
        fontsize=15, fontweight="bold", color="#2c3e50",
        transform=ax_title.transAxes,
    )
    ax_title.text(
        0.5, 0.18, subtitle,
        ha="center", va="center",
        fontsize=9, color="#666666",
        transform=ax_title.transAxes,
    )

    # ── Headline callout (large, colored box) ──────────────────────────────────
    ax_head = fig.add_subplot(gs[1, :])
    reduction = m["peak_reduction_pp"]
    sign  = "-" if reduction >= 0 else "+"
    bg    = "#d5e8d4" if reduction > 0 else "#ffe6cc"
    edge  = "#82b366" if reduction > 0 else "#d6b656"
    ax_head.set_facecolor(bg)
    for sp in ax_head.spines.values():
        sp.set_linewidth(2.5)
        sp.set_edgecolor(edge)
    ax_head.set_xticks([])
    ax_head.set_yticks([])
    ax_head.text(
        0.5, 0.63,
        f"{m['max_w_before']:.1f}%   →   {m['max_w_after']:.1f}%",
        ha="center", va="center",
        fontsize=28, fontweight="bold", color="#2c3e50",
        transform=ax_head.transAxes,
    )
    ax_head.text(
        0.5, 0.26,
        f"Peak day reduced by  {abs(reduction):.1f} percentage points",
        ha="center", va="center",
        fontsize=13, color="#4a4a4a",
        transform=ax_head.transAxes,
    )

    # ── Grouped metrics table ──────────────────────────────────────────────────
    ax_tbl = fig.add_subplot(gs[2, :])
    ax_tbl.axis("off")

    _SEC_BG    = "#EBF4FF"  # light blue-tinted section header
    _SEC_EDGE  = "#BEE3F8"
    _SEC_COLOR = "#2B6CB0"

    sections = [
        ("COVERAGE", [
            ["Recipients — total",    f"{m['n_total']:,}",
             "Recipients — profiled", f"{m['n_profiled']:,}  ({m['pct_profiled']:.1f}%)"],
            ["Freight cost coverage",  f"{m['pct_cost_coverage']:.1f}%   (EUR {m['covered_cost']:,.0f})",
             "", ""],
        ]),
        ("WORKLOAD LEVELING", [
            ["Monday weight — before",  f"{m['mon_w_before']:.1f}%",
             "Monday weight — after",   f"{m['mon_w_after']:.1f}%   ({m['best_label']})"],
            ["Friday weight — before",  f"{m['fri_w_before']:.1f}%",
             "Friday weight — after",   f"{m['fri_w_after']:.1f}%"],
            ["Peak weight — before",    f"{m['max_w_before']:.1f}%   ({m['max_w_day_before']})",
             "Peak weight — after",     f"{m['max_w_after']:.1f}%   ({m['max_w_day_after']})"],
            ["Peak cost — before",      f"{m['max_c_before']:.1f}%   ({m['max_c_day_before']})",
             "Peak cost — after",       f"{m['max_c_after']:.1f}%   ({m['max_c_day_after']})"],
        ]),
        ("TRUCK LOGISTICS", [
            ["Max truck weight",           f"{m['max_truck_weight']:,.0f} kg",
             "Recipients needing split",   str(m["n_split_recipients"])],
            ["Total extra trucks",         str(m["n_extra_trucks"]),
             "", ""],
        ]),
    ]

    cell_text  = []
    row_types  = []
    for sec_name, data_rows in sections:
        cell_text.append([f"  {sec_name}", "", "", ""])
        row_types.append("section")
        for row in data_rows:
            cell_text.append(row)
            row_types.append("data")

    tbl = ax_tbl.table(
        cellText=cell_text,
        colLabels=["Metric", "Value", "Metric", "Value"],
        cellLoc="left",
        loc="center",
        bbox=[0, 0, 1, 1],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)

    # Column header row
    for j in range(4):
        tbl[(0, j)].set_facecolor("#2c3e50")
        tbl[(0, j)].set_text_props(color="white", fontweight="bold")
        tbl[(0, j)].set_edgecolor("white")

    # Section headers and alternating data rows
    data_row_count = 0
    for i, rtype in enumerate(row_types, start=1):
        if rtype == "section":
            for j in range(4):
                tbl[(i, j)].set_facecolor(_SEC_BG)
                tbl[(i, j)].set_edgecolor(_SEC_EDGE)
                tbl[(i, j)].set_text_props(
                    color=_SEC_COLOR, fontweight="bold", fontsize=8.5,
                )
        else:
            bg_row = "#f7f7f7" if data_row_count % 2 == 0 else "white"
            data_row_count += 1
            for j in range(4):
                tbl[(i, j)].set_facecolor(bg_row)
                tbl[(i, j)].set_edgecolor("#e0e0e0")
                if j in (1, 3):
                    tbl[(i, j)].set_text_props(fontweight="bold")

    tbl.auto_set_column_width([0, 1, 2, 3])

    # ── Side-by-side bar charts ────────────────────────────────────────────────
    ax_b = fig.add_subplot(gs[3, 0])
    ax_a = fig.add_subplot(gs[3, 1])

    y_max = max(m["w_before"].max(), m["w_after"].max()) * 1.25
    y_max = max(y_max, 24.0)  # always show the 20% line with headroom
    x = np.arange(len(WEEKDAY_FULL_NAMES))

    for ax, pct, color, title in [
        (ax_b, m["w_before"], "#C44E52", "Weight — Without Profiles"),
        (ax_a, m["w_after"],  "#55A868", f"Weight — {m['best_label']}"),
    ]:
        ax.bar(x, pct.values, color=color, alpha=0.85, width=0.6)
        for xi, v in zip(x, pct.values):
            # Nudge label above the 20% reference line when the bar top is close
            label_y = 20.6 if 18.8 <= v <= 20.0 else v + 0.3
            ax.text(xi, label_y, f"{v:.1f}%", ha="center", va="bottom", fontsize=8)
        ax.axhline(y=20, color="#4A5568", linestyle="--", linewidth=1.2)
        ax.text(
            4.45, 20.5, "Equal distribution (20%)",
            ha="right", va="bottom", fontsize=7.5,
            color="#4A5568", style="italic",
        )
        ax.set_xticks(x)
        ax.set_xticklabels(WEEKDAY_FULL_NAMES, fontsize=8)
        ax.set_ylabel("Weight (%)", fontsize=9)
        ax.set_title(title, fontsize=10, fontweight="bold", pad=6)
        ax.set_ylim(0, y_max)
        ax.grid(axis="y", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    with PdfPages(out_pdf, keep_empty=False) as pp:
        pp.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def write_pipeline_summary(
    *,
    df_original: pd.DataFrame,
    df_profiled: pd.DataFrame,
    df_clustered: "pd.DataFrame | None",
    df_var: pd.DataFrame,
    profiled_ids: "set[int]",
    pattern_only_nc: pd.DataFrame,
    pattern_only_c: "pd.DataFrame | None",
    var_weight_max: float,
    var_frequency_max: float,
    min_frequency: float,
    max_truck_weight: float,
    plots_dir: "str | Path",
) -> None:
    """
    Compute savings metrics, print to console, write
    pipeline_summary.txt and pipeline_summary.pdf into plots_dir.
    """
    plots_dir = Path(plots_dir)
    plots_dir.mkdir(parents=True, exist_ok=True)

    if df_clustered is not None and not df_clustered.empty:
        df_best          = df_clustered
        pattern_only_best = pattern_only_c
        best_label       = "Clustered Profiles"
    else:
        df_best          = df_profiled
        pattern_only_best = pattern_only_nc
        best_label       = "Profiles Only"

    m = _build_summary_metrics(
        df_original=df_original,
        df_best=df_best,
        df_var=df_var,
        profiled_ids=profiled_ids,
        pattern_only_best=pattern_only_best,
        var_weight_max=var_weight_max,
        var_frequency_max=var_frequency_max,
        min_frequency=min_frequency,
        max_truck_weight=max_truck_weight,
        best_label=best_label,
    )

    text = _format_summary_text(m)
    print(text)

    txt_path = plots_dir / "pipeline_summary.txt"
    txt_path.write_text(text, encoding="utf-8")
    print(f"[Summary] Saved {txt_path}")

    pdf_path = plots_dir / "pipeline_summary.pdf"
    _write_pipeline_summary_pdf(m, df_original=df_original, df_best=df_best, out_pdf=pdf_path)
    print(f"[Summary] Saved {pdf_path}\n")
