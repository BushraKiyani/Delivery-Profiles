# src/delivery_profiles/clustered_pattern_assignment.py

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from ortools.linear_solver import pywraplp
from sklearn.cluster import KMeans
from math import radians


# Same pattern library used in pattern_assignment.py (Mon..Fri)
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


@dataclass(frozen=True)
class ClusteredPatternAssignmentConfig:
    days: int = 5
    time_limit_ms: int = 180_000  # 180 seconds

    # filtering thresholds
    var_weight_max: float = 100.0
    var_frequency_max: float = 100.0
    min_frequency: float = 1.0

    # rounding
    round_border: float = 0.5

    # clustering
    num_clusters: int = 4
    random_state: int = 0
    n_init: int = 10

    enforce_min_demand_1: bool = False


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def round_custom(value_x: float, border: float) -> int:
    value_floor = math.floor(value_x)
    return math.ceil(value_x) if value_x - value_floor >= border else math.floor(value_x)


def filter_recipients(
    df_var: pd.DataFrame,
    cfg: ClusteredPatternAssignmentConfig,
) -> pd.DataFrame:
    needed = [
        "Recipient_ID",
        "avg_Weight",
        "AVG_Frequency",
        "Variability_Weight",
        "Variability_Frequency",
    ]
    missing = [c for c in needed if c not in df_var.columns]
    if missing:
        raise ValueError(f"Variability dataframe missing required columns: {missing}")

    out = df_var.copy()
    out["Recipient_ID"] = out["Recipient_ID"].astype(int)
    out["avg_Weight"] = pd.to_numeric(out["avg_Weight"], errors="coerce")
    out["AVG_Frequency"] = pd.to_numeric(out["AVG_Frequency"], errors="coerce")
    out["Variability_Weight"] = pd.to_numeric(out["Variability_Weight"], errors="coerce")
    out["Variability_Frequency"] = pd.to_numeric(out["Variability_Frequency"], errors="coerce")

    out = out.loc[
        (out["Variability_Weight"] <= cfg.var_weight_max)
        & (out["Variability_Frequency"] <= cfg.var_frequency_max)
        & (out["AVG_Frequency"] >= cfg.min_frequency)
    ].copy()

    return out


def build_parameters(df_filtered: pd.DataFrame, cfg: ClusteredPatternAssignmentConfig) -> pd.DataFrame:
    out = df_filtered.copy()

    out["Frequency"] = out["AVG_Frequency"].apply(lambda x: round_custom(float(x), cfg.round_border))
    out["Frequency"] = out["Frequency"].clip(lower=1, upper=5)

    def _demand(row) -> int:
        f = float(row["AVG_Frequency"])
        w = float(row["avg_Weight"])
        if f <= 0 or np.isnan(f) or np.isnan(w):
            return 0
        d = int(round(w / f))
        if cfg.enforce_min_demand_1 and w > 0 and d == 0:
            return 1
        return max(d, 0)

    out["Demand"] = out.apply(_demand, axis=1)

    # cluster must exist later
    return out[["Recipient_ID", "Frequency", "Demand"]].reset_index(drop=True)


def add_clusters(
    df_params: pd.DataFrame,
    coordinate_list: List[Dict],
    cfg: ClusteredPatternAssignmentConfig,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    coordinate_list expected like:
      [{"Empfänger_id": 123, "latitude": 51.2, "longitude": 7.1}, ...]
    """
    coords = pd.DataFrame(coordinate_list).copy()
    needed = ["Empfänger_id", "latitude", "longitude"]
    missing = [c for c in needed if c not in coords.columns]
    if missing:
        raise ValueError(f"coordinate_list missing required keys/columns: {missing}")

    coords["Empfänger_id"] = coords["Empfänger_id"].astype(int)
    coords["latitude"] = coords["latitude"].astype(float)
    coords["longitude"] = coords["longitude"].astype(float)

    # only those recipients present in df_params
    sel = coords.loc[coords["Empfänger_id"].isin(df_params["Recipient_ID"])].copy()
    if sel.empty:
        raise ValueError("No overlapping Recipient_IDs between params and coordinate_list.")

    # radians transform (as in your code)
    sel["Latitude_Radians"] = sel["latitude"].apply(radians)
    sel["Longitude_Radians"] = sel["longitude"].apply(radians)
    X = sel[["Latitude_Radians", "Longitude_Radians"]].to_numpy()

    kmeans = KMeans(
        n_clusters=cfg.num_clusters,
        random_state=cfg.random_state,
        n_init=cfg.n_init,
    )
    sel["Cluster"] = kmeans.fit_predict(X).astype(int)

    mapping = dict(zip(sel["Empfänger_id"], sel["Cluster"]))
    out = df_params.copy()
    out["Cluster"] = out["Recipient_ID"].map(mapping).astype(int)

    return out, sel


# -----------------------------------------------------------------------------
# Optimization (cluster constraints done efficiently)
# -----------------------------------------------------------------------------

def solve_clustered_pattern_assignment(df_params: pd.DataFrame, cfg: ClusteredPatternAssignmentConfig) -> pd.DataFrame:
    """
    Minimize max daily demand s.
    Additional constraint:
      for each (cluster, frequency) group, everyone must pick the same pattern m.
    """
    if df_params.empty:
        return pd.DataFrame(columns=["Recipient_ID", "Frequency", "Demand", "Cluster", "Pattern", "Pattern_clear"])

    required = ["Recipient_ID", "Frequency", "Demand", "Cluster"]
    missing = [c for c in required if c not in df_params.columns]
    if missing:
        raise ValueError(f"df_params missing required columns: {missing}")

    # local solver
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if solver is None:
        raise RuntimeError("Could not create SCIP solver. Ensure OR-Tools is installed correctly.")

    infinity = solver.infinity()
    s = solver.IntVar(0, infinity, "s")

    C = df_params["Recipient_ID"].astype(int).tolist()
    f = df_params["Frequency"].astype(int).tolist()
    q = df_params["Demand"].astype(int).tolist()
    cl = df_params["Cluster"].astype(int).tolist()
    days = cfg.days

    # x[j,m] ∈ {0,1}
    x: Dict[Tuple[int, int], pywraplp.Variable] = {}
    for j in range(len(C)):
        freq = int(f[j])
        if freq not in PAT:
            raise ValueError(f"Frequency {freq} not supported. Allowed: {sorted(PAT.keys())}")
        for m in range(len(PAT[freq])):
            x[(j, m)] = solver.IntVar(0, 1, f"x_{j}_{m}")

    # daily constraints
    for t in range(days):
        solver.Add(
            solver.Sum(
                x[(j, m)] * PAT[int(f[j])][m][t] * int(q[j])
                for j in range(len(C))
                for m in range(len(PAT[int(f[j])]))
            )
            <= s
        )

    # each recipient picks exactly one pattern
    for j in range(len(C)):
        solver.Add(solver.Sum(x[(j, m)] for m in range(len(PAT[int(f[j])]))) == 1)

    # cluster+frequency groups must share same pattern
    # Efficient approach:
    # For each group g and each pattern m in that frequency:
    #   x[j,m] == y[g,m] for all j in group
    # and sum_m y[g,m] == 1
    groups: Dict[Tuple[int, int], List[int]] = {}
    for j in range(len(C)):
        key = (int(cl[j]), int(f[j]))
        groups.setdefault(key, []).append(j)

    y: Dict[Tuple[Tuple[int, int], int], pywraplp.Variable] = {}
    for (cluster_id, freq) in groups.keys():
        for m in range(len(PAT[freq])):
            y[((cluster_id, freq), m)] = solver.IntVar(0, 1, f"y_c{cluster_id}_f{freq}_m{m}")

        solver.Add(solver.Sum(y[((cluster_id, freq), m)] for m in range(len(PAT[freq]))) == 1)

        for j in groups[(cluster_id, freq)]:
            for m in range(len(PAT[freq])):
                solver.Add(x[(j, m)] == y[((cluster_id, freq), m)])

    # objective
    solver.Minimize(s)
    solver.SetTimeLimit(cfg.time_limit_ms)

    status = solver.Solve()
    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        raise RuntimeError("Clustered pattern assignment model did not find a feasible solution.")

    # Extract solution
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
                        "Cluster": int(cl[j]),
                        "Pattern": int(m),
                        "Pattern_clear": PAT[freq][m],
                    }
                )
                break

    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# Public API (replaces your clustered_pattern_assignment function)
# -----------------------------------------------------------------------------

def assign_clustered_patterns(
    df_variability: pd.DataFrame,
    coordinate_list: List[Dict[str, Any]],
    cfg: ClusteredPatternAssignmentConfig = ClusteredPatternAssignmentConfig(),
    *,
    save_path: Optional[str | Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    One-call:
      filter -> params -> add clusters -> solve -> optional save

    Returns:
      (results_df, clustered_coords_df)
    """
    filtered = filter_recipients(df_variability, cfg)
    params = build_parameters(filtered, cfg)
    params_clustered, coords_clustered = add_clusters(params, coordinate_list, cfg)
    results = solve_clustered_pattern_assignment(params_clustered, cfg)

    if save_path:
        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        results.to_csv(p, encoding="latin-1", sep=";", index=False)

    return results, coords_clustered
