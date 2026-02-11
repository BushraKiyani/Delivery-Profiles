from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class VariabilityConfig:
    # input columns
    date_col: str = "Loading_Date"
    week_col: str = "Calendar_Week"
    recipient_col: str = "Recipient_ID"
    weight_col: str = "Weight"
    cost_col: str = "Freight_Cost"

    # output behavior
    fill_missing_with_zero: bool = True  # matches your old fillna(0)
    ddof: int = 1  # pandas std default (sample std)


def add_calendar_week(df: pd.DataFrame, cfg: VariabilityConfig = VariabilityConfig()) -> pd.DataFrame:
    """
    Adds Calendar_Week if missing, derived from date_col.
    """
    out = df.copy()
    if cfg.week_col in out.columns:
        return out

    if cfg.date_col not in out.columns:
        raise ValueError(f"Missing '{cfg.date_col}'. Provide it or precompute '{cfg.week_col}'.")

    out[cfg.date_col] = pd.to_datetime(out[cfg.date_col], errors="coerce")
    out[cfg.week_col] = out[cfg.date_col].dt.isocalendar().week.astype(int)
    return out


def compute_weekly_weight_and_frequency(
    df: pd.DataFrame,
    cfg: VariabilityConfig = VariabilityConfig(),
    *,
    save_frequency_path: Optional[str | Path] = None,
    save_weight_path: Optional[str | Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Equivalent to your evaluation_after_KW1(...)

    Returns:
      df_frequency: index=Calendar_Week, columns=Recipient_ID, values=#shipments
      df_weight:    index=Calendar_Week, columns=Recipient_ID, values=sum(weight)
    """
    out = add_calendar_week(df, cfg)

    out[cfg.weight_col] = pd.to_numeric(out[cfg.weight_col], errors="coerce")

    df_weight = out.groupby([cfg.week_col, cfg.recipient_col])[cfg.weight_col].sum().unstack()
    df_frequency = out.groupby([cfg.week_col, cfg.recipient_col])[cfg.weight_col].count().unstack()

    if cfg.fill_missing_with_zero:
        df_weight = df_weight.fillna(0)
        df_frequency = df_frequency.fillna(0)

    df_weight = df_weight.astype(float)
    df_frequency = df_frequency.astype(float)

    # Optional saving (keep file I/O in scripts, but supported)
    if save_frequency_path:
        p = Path(save_frequency_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        df_frequency.to_csv(p, encoding="latin_1", sep=";")

    if save_weight_path:
        p = Path(save_weight_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        df_weight.to_csv(p, encoding="latin_1", sep=";")

    return df_frequency, df_weight


def compute_variability_summary(
    df_frequency: pd.DataFrame,
    df_weight: pd.DataFrame,
    df_shipments: pd.DataFrame,
    cfg: VariabilityConfig = VariabilityConfig(),
    *,
    save_path: Optional[str | Path] = None,
    save_path_eu: Optional[str | Path] = None,
) -> pd.DataFrame:
    """
    Equivalent to your variability_evaluation(...)

    Returns one row per recipient with:
      avg/std weight & frequency
      variability ratios
      total Freight_Cost, shipments count, total Weight
    """
    df = df_shipments.copy()
    df[cfg.cost_col] = pd.to_numeric(df.get(cfg.cost_col, np.nan), errors="coerce")
    df[cfg.weight_col] = pd.to_numeric(df.get(cfg.weight_col, np.nan), errors="coerce")
    df[cfg.recipient_col] = df[cfg.recipient_col].astype(int)

    # ensure columns align
    recipients = sorted(set(df[cfg.recipient_col].unique()).union(set(map(int, df_weight.columns))))

    summary = pd.DataFrame(index=recipients)
    summary.index.name = cfg.recipient_col

    # Weekly stats
    summary["avg_Weight"] = df_weight.mean(axis=0)
    summary["AVG_Frequency"] = df_frequency.mean(axis=0)
    summary["std_Weight"] = df_weight.std(axis=0, ddof=cfg.ddof)
    summary["STD_Frequency"] = df_frequency.std(axis=0, ddof=cfg.ddof)

    # Variability ratios with safe division (avoid inf)
    summary["Variability_Weight"] = np.where(
        summary["avg_Weight"] > 0,
        summary["std_Weight"] / summary["avg_Weight"],
        np.nan,
    )
    summary["Variability_Frequency"] = np.where(
        summary["AVG_Frequency"] > 0,
        summary["STD_Frequency"] / summary["AVG_Frequency"],
        np.nan,
    )

    # Shipment-level totals
    grp = df.groupby(cfg.recipient_col)
    summary["Freight_Cost"] = grp[cfg.cost_col].sum(min_count=1)
    summary["Shipments"] = grp[cfg.cost_col].count()
    summary["Weight"] = grp[cfg.weight_col].sum(min_count=1)

    summary = summary.reset_index()

    # Optional write
    if save_path:
        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(p, encoding="latin_1", sep=";", index=False)

    if save_path_eu:
        p = Path(save_path_eu)
        p.parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(p, encoding="latin_1", sep=";", index=False, decimal=",")

    return summary


# Convenience function if you want one call (common in main.py)
def run_variability_analysis(
    df_shipments: pd.DataFrame,
    cfg: VariabilityConfig = VariabilityConfig(),
    *,
    save_frequency_path: Optional[str | Path] = None,
    save_weight_path: Optional[str | Path] = None,
    save_variability_path: Optional[str | Path] = None,
    save_variability_path_eu: Optional[str | Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    One-call helper.

    Returns:
      df_frequency, df_weight, df_variability
    """
    df_frequency, df_weight = compute_weekly_weight_and_frequency(
        df_shipments,
        cfg,
        save_frequency_path=save_frequency_path,
        save_weight_path=save_weight_path,
    )
    df_var = compute_variability_summary(
        df_frequency,
        df_weight,
        df_shipments,
        cfg,
        save_path=save_variability_path,
        save_path_eu=save_variability_path_eu,
    )
    return df_frequency, df_weight, df_var
