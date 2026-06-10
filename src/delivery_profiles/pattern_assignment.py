from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from ortools.linear_solver import pywraplp


# -----------------------------------------------------------------------------
# Pattern library (Mon..Fri)
# -----------------------------------------------------------------------------

PAT: Dict[int, List[List[int]]] = {
    5: [[1, 1, 1, 1, 1]],
    4: [
        [0, 1, 1, 1, 1],
        [1, 0, 1, 1, 1],
        [1, 1, 0, 1, 1],
        [1, 1, 1, 0, 1],
        [1, 1, 1, 1, 0],
    ],
    3: [
        [0, 1, 0, 1, 1],
        [1, 0, 1, 0, 1],
        [1, 1, 0, 1, 0],
        [0, 1, 1, 0, 1],
        [1, 0, 1, 1, 0],
    ],
    2: [
        [1, 0, 1, 0, 0],
        [0, 1, 0, 1, 0],
        [0, 0, 1, 0, 1],
        [1, 0, 0, 1, 0],
        [0, 1, 0, 0, 1],
    ],
    1: [
        [1, 0, 0, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 1, 0],
        [0, 0, 0, 0, 1],
    ],
}


# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class PatternAssignmentConfig:
    days: int = 5
    time_limit_ms: int = 180_000  # 180 seconds

    # Filtering thresholds (same meaning as your original)
    var_weight_max: float = 100.0
    var_frequency_max: float = 100.0
    min_frequency: float = 1.0

    # How to round average frequency to an integer frequency (1..5)
    round_border: float = 0.5

    # Demand formula: round(avg_weight / avg_frequency)
    # set to True to ensure demand>=1 when frequency>0 and avg_weight>0
    enforce_min_demand_1: bool = False


# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------

def round_custom(value_x: float, border: float) -> int:
    """
    Round based on a specified border (your round_costum).
    """
    if value_x is None or (isinstance(value_x, float) and np.isnan(value_x)):
        return 0
    value_floor = math.floor(value_x)
    return math.ceil(value_x) if (value_x - value_floor) >= border else math.floor(value_x)


def filter_recipients(
    df_var: pd.DataFrame,
    cfg: PatternAssignmentConfig,
    *,
    var_weight_col: str = "Variability_Weight",
    var_freq_col: str = "Variability_Frequency",
    avg_freq_col: str = "AVG_Frequency",
) -> pd.DataFrame:
    """
    Equivalent to empfänger_filtern but without file I/O.
    """
    needed = ["Recipient_ID", var_weight_col, var_freq_col, avg_freq_col, "avg_Weight"]
    missing = [c for c in needed if c not in df_var.columns]
    if missing:
        raise ValueError(f"Variability dataframe missing required columns: {missing}")

    out = df_var.copy()
    out["Recipient_ID"] = out["Recipient_ID"].astype(int)

    out[var_weight_col] = pd.to_numeric(out[var_weight_col], errors="coerce")
    out[var_freq_col] = pd.to_numeric(out[var_freq_col], errors="coerce")
    out[avg_freq_col] = pd.to_numeric(out[avg_freq_col], errors="coerce")
    out["avg_Weight"] = pd.to_numeric(out["avg_Weight"], errors="coerce")

    out = out.loc[
        (out[var_weight_col] <= cfg.var_weight_max)
        & (out[var_freq_col] <= cfg.var_frequency_max)
        & (out[avg_freq_col] >= cfg.min_frequency)
    ].copy()

    return out


def build_parameters(
    df_filtered: pd.DataFrame,
    cfg: PatternAssignmentConfig,
    *,
    avg_freq_col: str = "AVG_Frequency",
    avg_weight_col: str = "avg_Weight",
    freight_cost_col: str = "Freight_Cost",
    shipments_col: str = "Shipments",
) -> pd.DataFrame:
    """
    Frequency = round_custom(AVG_Frequency, 0.5)
    Demand    = round(Freight_Cost / Shipments)  — avg freight cost per shipment.
                Falls back to round(avg_Weight / AVG_Frequency) when cost columns absent.
    """
    out = df_filtered.copy()

    out["Frequency"] = out[avg_freq_col].apply(lambda x: round_custom(float(x), cfg.round_border))
    out["Frequency"] = out["Frequency"].clip(lower=1, upper=5)

    use_cost = freight_cost_col in out.columns and shipments_col in out.columns

    def _demand(row) -> int:
        if use_cost:
            cost = float(row[freight_cost_col]) if not pd.isna(row[freight_cost_col]) else 0.0
            n = float(row[shipments_col]) if not pd.isna(row[shipments_col]) else 0.0
            if n > 0:
                d = int(round(cost / n))
                if cfg.enforce_min_demand_1 and cost > 0 and d == 0:
                    return 1
                return max(d, 0)
        # fallback: weight-based demand
        f = float(row[avg_freq_col])
        w = float(row[avg_weight_col])
        if f <= 0 or np.isnan(f) or np.isnan(w):
            return 0
        d = int(round(w / f))
        if cfg.enforce_min_demand_1 and w > 0 and d == 0:
            return 1
        return max(d, 0)

    out["Demand"] = out.apply(_demand, axis=1)

    return out[["Recipient_ID", "Frequency", "Demand"]].reset_index(drop=True)


# -----------------------------------------------------------------------------
# Optimization (your model, fixed)
# -----------------------------------------------------------------------------

def solve_pattern_assignment(
    df_params: pd.DataFrame,
    cfg: PatternAssignmentConfig,
) -> pd.DataFrame:
    """
    Minimize maximum daily shipped quantity s subject to:
      - each recipient selects exactly one pattern
      - daily sum of demands <= s

    Returns results df:
      Recipient_ID, Frequency, Demand, Pattern, Pattern_clear
    """
    if df_params.empty:
        return pd.DataFrame(columns=["Recipient_ID", "Frequency", "Demand", "Pattern", "Pattern_clear"])

    # Local solver (IMPORTANT: no global solver)
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if solver is None:
        raise RuntimeError("Could not create SCIP solver. Ensure OR-Tools is installed correctly.")

    infinity = solver.infinity()
    s = solver.IntVar(0, infinity, "s")

    C = df_params["Recipient_ID"].astype(int).tolist()
    f = df_params["Frequency"].astype(int).tolist()
    q = df_params["Demand"].astype(int).tolist()
    days = cfg.days

    # Decision variables: x[j,m] ∈ {0,1}
    x: Dict[Tuple[int, int], pywraplp.Variable] = {}
    for j in range(len(C)):
        freq = int(f[j])
        if freq not in PAT:
            raise ValueError(f"Frequency {freq} not supported. Allowed: {sorted(PAT.keys())}")
        for m in range(len(PAT[freq])):
            x[(j, m)] = solver.IntVar(0, 1, f"x_{j}_{m}")

    # Constraints: daily max <= s
    for t in range(days):
        solver.Add(
            solver.Sum(
                x[(j, m)] * PAT[int(f[j])][m][t] * int(q[j])
                for j in range(len(C))
                for m in range(len(PAT[int(f[j])]))
            )
            <= s
        )

    # Each recipient exactly one pattern
    for j in range(len(C)):
        solver.Add(
            solver.Sum(x[(j, m)] for m in range(len(PAT[int(f[j])]))) == 1
        )

    # Objective
    solver.Minimize(s)

    # Time limit
    solver.SetTimeLimit(cfg.time_limit_ms)

    status = solver.Solve()
    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        raise RuntimeError("Pattern assignment model did not find a feasible solution.")

    # Collect solution
    rows = []
    for j in range(len(C)):
        freq = int(f[j])
        for m in range(len(PAT[freq])):
            if x[(j, m)].solution_value() > 0.5:
                rows.append(
                    {
                        "Recipient_ID": int(C[j]),
                        "Frequency": int(freq),
                        "Demand": int(q[j]),
                        "Pattern": int(m),
                        "Pattern_clear": PAT[freq][m],
                    }
                )
                break

    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# Public API (replaces your pattern_assignment(...) function)
# -----------------------------------------------------------------------------

def assign_patterns(
    df_variability: pd.DataFrame,
    cfg: PatternAssignmentConfig = PatternAssignmentConfig(),
    *,
    save_path: Optional[str | Path] = None,
) -> pd.DataFrame:
    """
    One-call function:
      filter -> build params -> solve -> optional save
    """
    filtered = filter_recipients(df_variability, cfg)
    params = build_parameters(filtered, cfg)
    results = solve_pattern_assignment(params, cfg)

    if save_path:
        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        results.to_csv(p, encoding="latin-1", sep=";", index=False)

    return results
