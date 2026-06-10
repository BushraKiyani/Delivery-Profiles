from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from .preprocessing import preprocess_shipments, PreprocessConfig
from .geo import add_coordinates, GeoConfig
from .distance_matrix import create_distance_matrices, OSRMConfig
from .variability import run_variability_analysis, VariabilityConfig
from .pattern_assignment import assign_patterns, PatternAssignmentConfig
from .clustered_pattern_assignment import assign_clustered_patterns, ClusteredPatternAssignmentConfig
from .cost_model import CostModelConfig, add_freight_costs
from .profile_application import apply_profiles_to_shipments, ProfileApplicationConfig
from .routing_vrp import route
from .maps import create_cluster_map_html, MapConfig
from .weekday_plots import write_weekday_plots_pdf, write_freight_cost_comparison_pdf, write_weight_distribution_pdf, write_pipeline_summary


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _log_overweight_check(
    profiles: pd.DataFrame,
    df_var: pd.DataFrame,
    max_truck_weight: float,
    label: str = "",
) -> None:
    """
    Print a pre-run summary of profiled recipients whose average buffer weight
    per pattern day exceeds max_truck_weight.  These will be split into multiple
    trucks at apply time rather than skipped.
    """
    if profiles.empty or "avg_Weight" not in df_var.columns:
        return

    merged = profiles[["Recipient_ID", "Frequency"]].merge(
        df_var[["Recipient_ID", "avg_Weight"]], on="Recipient_ID", how="left"
    )
    merged["avg_kg_per_day"] = (
        pd.to_numeric(merged["avg_Weight"], errors="coerce")
        / merged["Frequency"].clip(lower=1)
    )
    heavy = merged[merged["avg_kg_per_day"] > max_truck_weight].copy()

    tag = f" ({label})" if label else ""
    if heavy.empty:
        print(f"[Overweight check{tag}]  All {len(profiles)} profiled recipients fit within"
              f" {max_truck_weight:,.0f} kg/pattern day — no splitting needed.\n")
        return

    # ceiling: trucks needed per day
    heavy["est_trucks"] = (heavy["avg_kg_per_day"] / max_truck_weight).apply(
        lambda x: int(-(-x // 1))
    )
    print(
        f"\n[Overweight check{tag}]  {len(heavy)}/{len(profiles)} profiled recipient(s)"
        f" will need multi-truck splitting (avg load > {max_truck_weight:,.0f} kg/pattern day):"
    )
    for _, row in heavy.sort_values("avg_kg_per_day", ascending=False).iterrows():
        print(
            f"  Recipient {int(row['Recipient_ID'])}: freq={int(row['Frequency'])},"
            f" avg {row['avg_kg_per_day']:,.0f} kg/day"
            f" → ~{int(row['est_trucks'])} truck(s)/day"
        )
    print()

def _write_tableau_export(
    *,
    df_original: pd.DataFrame,
    df_profiled: "pd.DataFrame | None",
    df_clustered: "pd.DataFrame | None",
    df_clustered_dbscan: "pd.DataFrame | None" = None,
    out_path: Path,
) -> None:
    """Concatenate all scenarios into one CSV with a Scenario column for Tableau."""
    parts = []
    for df, label in [
        (df_original,        "Without Profiles"),
        (df_profiled,        "Profiles Only"),
        (df_clustered,       "KMeans Clustered"),
        (df_clustered_dbscan,"DBSCAN Clustered"),
    ]:
        if df is None or df.empty:
            continue
        chunk = df.copy()
        chunk["Scenario"] = label
        parts.append(chunk)

    if not parts:
        return

    combined = pd.concat(parts, ignore_index=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(out_path, sep=";", encoding="latin-1", decimal=".", index=False)
    print(f"[Tableau export]  {len(combined):,} rows → {out_path}")


_WDAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri"]


def _write_recipient_summary_csv(
    *,
    df_original: pd.DataFrame,
    pattern_only_nc: pd.DataFrame,
    pattern_only_c: "pd.DataFrame | None",
    pattern_only_dbscan: "pd.DataFrame | None" = None,
    profiles_nc: pd.DataFrame,
    profiles_c: "pd.DataFrame | None",
    profiles_dbscan: "pd.DataFrame | None" = None,
    df_var: pd.DataFrame,
    out_path: Path,
) -> None:
    """Per-recipient before/after CSV: one row per (recipient × scenario)."""
    import ast

    def _ensure_weekday(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if "Weekday" not in df.columns and "Loading_Date" in df.columns:
            df["Weekday"] = pd.to_datetime(df["Loading_Date"], errors="coerce").dt.dayofweek
        return df

    def _parse_pattern(raw) -> list:
        if isinstance(raw, list):
            return raw
        if isinstance(raw, str):
            try:
                return ast.literal_eval(raw)
            except Exception:
                pass
        return []

    # ── normalise df_original once ───────────────────────────────────────
    orig = _ensure_weekday(df_original.copy())
    orig["_rid"] = pd.to_numeric(orig["Recipient_ID"], errors="coerce").fillna(-1).astype(int)
    if "Freight_Cost" not in orig.columns:
        orig["Freight_Cost"] = 0.0
    else:
        orig["Freight_Cost"] = pd.to_numeric(orig["Freight_Cost"], errors="coerce").fillna(0.0)
    if "Weight" not in orig.columns:
        orig["Weight"] = 0.0
    else:
        orig["Weight"] = pd.to_numeric(orig["Weight"], errors="coerce").fillna(0.0)

    # pre-compute "before" aggregates (scenario-independent)
    orig_cost_by_rid  = orig.groupby("_rid")["Freight_Cost"].sum()
    orig_wt_by_rid_day = (
        orig.groupby(["_rid", "Weekday"])["Weight"].sum()
        .unstack(fill_value=0.0)
    )
    orig_wdays_by_rid = orig.groupby("_rid")["Weekday"].apply(
        lambda s: ",".join(
            _WDAY_SHORT[d]
            for d in sorted(s.dropna().astype(int).unique())
            if 0 <= d <= 4
        )
    )

    # variability lookup (keyed by int recipient id)
    var_lut: dict = {}
    if not df_var.empty:
        _v = df_var.copy()
        _v["_rid"] = pd.to_numeric(_v["Recipient_ID"], errors="coerce").fillna(-1).astype(int)
        for _, r in _v.iterrows():
            var_lut[int(r["_rid"])] = r

    rows_out: list = []

    for scenario_label, profiles, pattern_only in [
        ("Profiles Only",      profiles_nc,      pattern_only_nc),
        ("KMeans Clustered",   profiles_c,        pattern_only_c),
        ("DBSCAN Clustered",   profiles_dbscan,   pattern_only_dbscan),
    ]:
        if profiles is None or profiles.empty:
            continue
        if pattern_only is None or pattern_only.empty:
            continue

        pat = _ensure_weekday(pattern_only.copy())
        pat["_rid"] = pd.to_numeric(pat["Recipient_ID"], errors="coerce").fillna(-1).astype(int)
        if "Freight_Cost" not in pat.columns:
            pat["Freight_Cost"] = 0.0
        else:
            pat["Freight_Cost"] = pd.to_numeric(pat["Freight_Cost"], errors="coerce").fillna(0.0)
        if "Weight" not in pat.columns:
            pat["Weight"] = 0.0
        else:
            pat["Weight"] = pd.to_numeric(pat["Weight"], errors="coerce").fillna(0.0)

        pat_cost_by_rid   = pat.groupby("_rid")["Freight_Cost"].sum()
        pat_wt_by_rid_day = (
            pat.groupby(["_rid", "Weekday"])["Weight"].sum()
            .unstack(fill_value=0.0)
        )
        pat_max_truck = (
            pat.groupby("_rid")["Truck_Number"].max()
            if "Truck_Number" in pat.columns
            else pd.Series(dtype=float)
        )

        # profile lookup (unique per recipient after pattern assignment)
        prof_lut: dict = {}
        for _, r in profiles.iterrows():
            prof_lut[int(pd.to_numeric(r["Recipient_ID"], errors="coerce"))] = r

        for rid in sorted(profiles["Recipient_ID"].dropna().astype(int).unique()):
            # ── before ───────────────────────────────────────────────────
            cost_before    = float(orig_cost_by_rid.get(rid, 0.0))
            orig_wday_str  = str(orig_wdays_by_rid.get(rid, ""))

            before_wt: dict = {}
            for d in range(5):
                val = 0.0
                if rid in orig_wt_by_rid_day.index and d in orig_wt_by_rid_day.columns:
                    val = float(orig_wt_by_rid_day.loc[rid, d])
                before_wt[f"{_WDAY_SHORT[d]}_weight_before"] = val

            # ── after ────────────────────────────────────────────────────
            cost_after       = float(pat_cost_by_rid.get(rid, 0.0))
            cost_change_eur  = cost_after - cost_before
            cost_change_pct  = round((cost_change_eur / cost_before * 100.0) if cost_before else 0.0, 2)

            after_wt: dict = {}
            for d in range(5):
                val = 0.0
                if rid in pat_wt_by_rid_day.index and d in pat_wt_by_rid_day.columns:
                    val = float(pat_wt_by_rid_day.loc[rid, d])
                after_wt[f"{_WDAY_SHORT[d]}_weight_after"] = val

            # ── truck splitting ──────────────────────────────────────────
            max_trucks  = int(pat_max_truck.get(rid, 1)) if not pat_max_truck.empty else 1
            truck_split = "yes" if max_trucks > 1 else "no"

            # ── profile data ─────────────────────────────────────────────
            p = prof_lut.get(rid, pd.Series())
            freq          = int(float(p.get("Frequency", 0))) if not p.empty else 0
            pattern_clear = p.get("Pattern_clear", "") if not p.empty else ""
            parsed        = _parse_pattern(pattern_clear)
            pattern_days  = ",".join(_WDAY_SHORT[i] for i, v in enumerate(parsed) if v == 1)

            # ── variability ──────────────────────────────────────────────
            v_row    = var_lut.get(rid, pd.Series())
            avg_wt   = float(v_row.get("avg_Weight",    float("nan"))) if not v_row.empty else float("nan")
            avg_freq = float(v_row.get("AVG_Frequency", float("nan"))) if not v_row.empty else float("nan")
            var_cost = float(v_row.get("Freight_Cost",  float("nan"))) if not v_row.empty else float("nan")

            rows_out.append({
                "Scenario":                  scenario_label,
                "Recipient_ID":              rid,
                "Original_weekdays":         orig_wday_str,
                "Assigned_pattern":          str(pattern_clear),
                "Pattern_days":              pattern_days,
                "Frequency":                 freq,
                "avg_Weight":                avg_wt,
                "AVG_Frequency":             avg_freq,
                "Variability_Freight_Cost":  var_cost,
                "Cost_before_EUR":           cost_before,
                "Cost_after_EUR":            cost_after,
                "Cost_change_EUR":           cost_change_eur,
                "Cost_change_pct":           cost_change_pct,
                "Truck_split":               truck_split,
                "Max_trucks":                max_trucks,
                **before_wt,
                **after_wt,
            })

    if not rows_out:
        print("[Recipient summary]  No profiled recipients found; skipping.")
        return

    df_out = pd.DataFrame(rows_out)
    base_cols = [
        "Scenario", "Recipient_ID", "Original_weekdays",
        "Assigned_pattern", "Pattern_days", "Frequency",
        "avg_Weight", "AVG_Frequency", "Variability_Freight_Cost",
        "Cost_before_EUR", "Cost_after_EUR", "Cost_change_EUR", "Cost_change_pct",
        "Truck_split", "Max_trucks",
    ]
    wday_cols = (
        [f"{d}_weight_before" for d in _WDAY_SHORT] +
        [f"{d}_weight_after"  for d in _WDAY_SHORT]
    )
    col_order = [c for c in (base_cols + wday_cols) if c in df_out.columns]
    df_out = df_out[col_order]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(out_path, sep=";", encoding="latin-1", decimal=".", index=False)
    print(f"[Recipient summary]  {len(df_out)} rows → {out_path}")


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _fmt_float(x: Any) -> str:
    """
    Stable float formatting:
    - always uses dot (.)
    - trims trailing zeros
    - keeps enough precision for folder/file names
    """
    try:
        return f"{float(x):.6f}".rstrip("0").rstrip(".")
    except Exception:
        return str(x)


def _run_id_from_variability(v: Dict[str, Any], fmt: str) -> str:
    return fmt.format(
        min_frequency=int(float(v.get("min_frequency", 1))),
        var_weight_max=_fmt_float(v.get("var_weight_max", 100)),
        var_frequency_max=_fmt_float(v.get("var_frequency_max", 100)),
    )


def _suffix_from_variability(v: Dict[str, Any], clustered: bool, method: str = "") -> str:
    base = (
        f"vw{_fmt_float(v.get('var_weight_max', 100))}"
        f"_vf{_fmt_float(v.get('var_frequency_max', 100))}"
        f"_mf{int(float(v.get('min_frequency', 1)))}"
    )
    if not clustered:
        return base
    prefix = f"clustered_{method}_" if method else "clustered_"
    return prefix + base


def _read_matrix_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, index_col=0)


# -----------------------------------------------------------------------------
# Pipeline
# -----------------------------------------------------------------------------

def run_pipeline_from_config(
    shipments: pd.DataFrame,
    *,
    tariff_matrix: Optional[pd.DataFrame],
    sender_lon: float,
    sender_lat: float,
    cfg: Dict[str, Any],
) -> Dict[str, Any]:
    """
    End-to-end pipeline using config/default.yaml structure.

    Behavior (matches your old main.py logic):
      - Preprocess -> Add coordinates -> Add distances (compute or load)
      - Add freight costs
      - Variability analysis
      - Non-clustered pattern assignment + apply profiles
      - If clustering.enabled: clustered pattern assignment + apply profiles
      - Optional: recalc freight costs after profile application (recommended)
      - Writes ALL outputs into a run-specific folder (no overwrites across runs)
    """
    # ----------------------------
    # Config blocks
    # ----------------------------
    paths_yaml = cfg.get("paths", {}) or {}
    data_paths = paths_yaml.get("data", {}) or {}
    cache_paths = paths_yaml.get("cache", {}) or {}

    base_out_dir = Path(str(data_paths.get("outputs", "outputs")))
    _ensure_dir(base_out_dir)

    # run-specific output directory based on variability thresholds
    rn = cfg.get("run_naming", {}) or {}
    v_yaml = cfg.get("variability", {}) or {}
    if bool(rn.get("enabled", True)):
        run_id = _run_id_from_variability(
            v_yaml,
            str(rn.get("format", "minF{min_frequency}_varW{var_weight_max}_varF{var_frequency_max}")),
        )
        out_dir = base_out_dir / "runs" / run_id
    else:
        out_dir = base_out_dir

    _ensure_dir(out_dir)
    plots_dir = out_dir / "plots"
    _ensure_dir(plots_dir)
    matrices_dir = out_dir / "matrices"
    _ensure_dir(matrices_dir)

    # cache directory (coordinates cache lives here)
    coord_cache_path = Path(str(cache_paths.get("coordinates", "cache/coordinates.json")))
    _ensure_dir(coord_cache_path.parent)

    # ----------------------------
    # 1) Preprocess
    # ----------------------------
    pre_yaml = cfg.get("preprocessing", {}) or {}
    pre_cfg = PreprocessConfig(
        write_preprocessed_csv=bool(pre_yaml.get("write_preprocessed_csv", False)),
        preprocessed_csv_path=str(out_dir / "preprocessed_shipments.csv"),
        address_correction_csv=None,
        id_split_csv=None,
    )
    df_pre = preprocess_shipments(shipments, pre_cfg)

    # ----------------------------
    # 2) Geocode / Add coordinates
    # ----------------------------
    geo_yaml = cfg.get("geocoding", {}) or {}
    geo_cfg = GeoConfig(
        base_url=str(geo_yaml.get("base_url") or GeoConfig().base_url),
        rate_limit_seconds=float(geo_yaml.get("rate_limit_seconds", 1.0)),
        timeout_seconds=int(geo_yaml.get("timeout_seconds", 20)),
    )

    df_coords, coord_list = add_coordinates(
        processed_data=df_pre,
        sender_lon=float(sender_lon),
        sender_lat=float(sender_lat),
        save_path=out_dir / "shipments_with_coords.csv",
        json_coordinate_list_path=coord_cache_path,
        cfg=geo_cfg,
        use_cache=bool(geo_yaml.get("use_cache", True)),
    )

    # ----------------------------
    # 3) Distances (compute OR load)
    # ----------------------------
    dist_yaml = cfg.get("distance_matrix", {}) or {}
    dist_mode = str(dist_yaml.get("mode", "compute")).lower()

    distances_RR = durations_RR = euclidean_RR = matrix_table = None
    durations_rr_path: Optional[Path] = None
    df_with_sender_distances: pd.DataFrame

    if dist_mode == "compute":
        osrm_yaml = (dist_yaml.get("osrm", {}) or {})
        osrm_cfg = OSRMConfig(
            base_url=str(osrm_yaml.get("base_url", OSRMConfig().base_url)),
            chunk_size=int(osrm_yaml.get("chunk_size", OSRMConfig().chunk_size)),
            rate_limit_seconds=float(osrm_yaml.get("rate_limit_seconds", OSRMConfig().rate_limit_seconds)),
            timeout_seconds=int(osrm_yaml.get("timeout_seconds", OSRMConfig().timeout_seconds)),
        )

        distances_RR, durations_RR, euclidean_RR, matrix_table, df_with_sender_distances = create_distance_matrices(
            df_shipments_with_coords=df_coords,
            coordinate_list=coord_list,
            sender_lon=float(sender_lon),
            sender_lat=float(sender_lat),
            cfg=osrm_cfg,
            save_distances_C=matrices_dir / "distances_rr.csv",
            save_durations_C=matrices_dir / "durations_rr.csv",
            save_euclidean_C=matrices_dir / "euclidean_rr.csv",
            save_matrix_table=matrices_dir / "matrix_table.csv",
            save_distances_S=matrices_dir / "distances_sender.csv",
            save_durations_S=matrices_dir / "durations_sender.csv",
            save_euclidean_S=matrices_dir / "euclidean_sender.csv",
            save_df_with_distances=out_dir / "shipments_with_distances.csv",
            symmetrize_osrm=bool(osrm_yaml.get("symmetrize", False)),
        )
        durations_rr_path = matrices_dir / "durations_rr.csv"

    elif dist_mode == "load":
        load_cfg = dist_yaml.get("load", {}) or {}

        p_ship = load_cfg.get("shipments_with_distances")
        if not p_ship:
            raise ValueError("distance_matrix.mode=load requires distance_matrix.load.shipments_with_distances")
        p_ship = Path(str(p_ship))
        if not p_ship.exists():
            raise FileNotFoundError(f"Missing precomputed shipments_with_distances file: {p_ship}")

        # This should be the same format as your pipeline writes: ; + latin1
        df_with_sender_distances = pd.read_csv(p_ship, sep=";", encoding="latin1")

        # Optional RR matrices
        p = load_cfg.get("distances_rr")
        if p:
            distances_RR = _read_matrix_csv(Path(str(p)))
        p = load_cfg.get("durations_rr")
        if p:
            durations_RR = _read_matrix_csv(Path(str(p)))
            durations_rr_path = Path(str(p))
        p = load_cfg.get("euclidean_rr")
        if p:
            euclidean_RR = _read_matrix_csv(Path(str(p)))
        p = load_cfg.get("matrix_table")
        if p:
            matrix_table = pd.read_csv(Path(str(p)))

        # Copy the loaded shipments_with_distances into this run folder (so it’s self-contained)
        df_with_sender_distances.to_csv(
            out_dir / "shipments_with_distances.csv", sep=";", encoding="latin1", decimal=".", index=False
        )

    else:
        raise ValueError("distance_matrix.mode must be 'compute' or 'load'")

    # ----------------------------
    # 4) Freight cost (baseline)
    # ----------------------------
    cost_yaml = cfg.get("cost_model", {}) or {}
    cost_cfg = CostModelConfig(
        tariff_type=str(cost_yaml.get("tariff_type", "matrix")),
        base_price=float(cost_yaml.get("base_price", 0.0)),
        price_per_ton=float(cost_yaml.get("price_per_ton", 0.0)),
    )

    if cost_cfg.tariff_type == "matrix" and tariff_matrix is None:
        raise ValueError("tariff_matrix is required when cost_model.tariff_type=matrix.")

    df_costed = add_freight_costs(
        df_with_sender_distances,
        df_tariff_wide=tariff_matrix,
        config=cost_cfg,
        out_col="Freight_Cost",
        weight_col_shipments="Weight",
        distance_col_shipments="Euc_Distance",
        weight_col_tariff="Weight_kg",
    )
    df_costed.to_csv(out_dir / "shipments_with_costs.csv", sep=";", encoding="latin1", decimal=".", index=False)

    # ----------------------------
    # 5) Variability analysis
    # ----------------------------
    var_cfg = VariabilityConfig()
    df_freq, df_w, df_var = run_variability_analysis(
        df_costed,
        var_cfg,
        save_frequency_path=out_dir / "weekly_frequency.csv",
        save_weight_path=out_dir / "weekly_weight.csv",
        save_variability_path=out_dir / "variability.csv",
        save_variability_path_eu=out_dir / "variability_eu.csv",
    )

    # ----------------------------
    # 6) Pattern assignment + apply profiles (NON-CLUSTERED always)
    # ----------------------------
    pat_yaml = cfg.get("pattern_assignment", {}) or {}
    time_limit_ms = int(float(pat_yaml.get("time_limit_seconds", 180)) * 1000)

    var_weight_max = float(v_yaml.get("var_weight_max", 100))
    var_frequency_max = float(v_yaml.get("var_frequency_max", 100))
    min_frequency = float(v_yaml.get("min_frequency", 1))

    pa_cfg = PatternAssignmentConfig(
        days=int(pat_yaml.get("days", 5)),
        time_limit_ms=time_limit_ms,
        var_weight_max=var_weight_max,
        var_frequency_max=var_frequency_max,
        min_frequency=min_frequency,
        round_border=float(pat_yaml.get("round_border", 0.5)),
    )

    # Coverage diagnostic: what share of freight cost will actually be optimised?
    if "Freight_Cost" in df_var.columns and "Variability_Weight" in df_var.columns:
        _total_cost = float(df_var["Freight_Cost"].sum())
        if _total_cost > 0:
            _mask = (
                (pd.to_numeric(df_var["Variability_Weight"], errors="coerce") <= var_weight_max)
                & (pd.to_numeric(df_var["Variability_Frequency"], errors="coerce") <= var_frequency_max)
                & (pd.to_numeric(df_var["AVG_Frequency"], errors="coerce") >= min_frequency)
            )
            _profiled_cost = float(df_var.loc[_mask, "Freight_Cost"].sum())
            _n_total = len(df_var)
            _n_prof = int(_mask.sum())
            print(
                f"\n[Profile coverage]  {_n_prof}/{_n_total} recipients qualify"
                f"  ({_profiled_cost:,.0f} / {_total_cost:,.0f} EUR"
                f"  = {_profiled_cost / _total_cost * 100:.1f}% of freight cost)"
                f"\n  thresholds: var_weight<={var_weight_max}, var_freq<={var_frequency_max},"
                f" min_frequency>={min_frequency}\n"
            )

    profiles_nc = assign_patterns(
        df_var,
        pa_cfg,
        save_path=out_dir / "profile_assignment.csv",
    )

    prof_app_yaml = cfg.get("profile_application", {}) or {}
    _app_cfg = ProfileApplicationConfig(
        max_truck_weight=float(prof_app_yaml.get("max_truck_weight", 25000.0)),
    )
    _log_overweight_check(profiles_nc, df_var, _app_cfg.max_truck_weight, label="non-clustered")

    pattern_only_nc, unchanged_nc, shipments_after_nc = apply_profiles_to_shipments(
        df_costed,
        profiles_nc,
        _app_cfg,
    )

    suffix_nc = _suffix_from_variability(v_yaml, clustered=False)

    pattern_only_nc.to_csv(
        out_dir / f"shipments_after_profiles_pattern_only_{suffix_nc}.csv",
        sep=";",
        encoding="latin1",
        index=False,
    )
    unchanged_nc.to_csv(
        out_dir / f"shipments_after_profiles_unchanged_{suffix_nc}.csv",
        sep=";",
        encoding="latin1",
        index=False,
    )
    shipments_after_nc.to_csv(
        out_dir / f"shipments_after_profiles_{suffix_nc}.csv",
        sep=";",
        encoding="latin1",
        index=False,
    )

    # Optional: recalc costs after applying profiles (matches old main.py)
    recalc = bool((cfg.get("post_cost_recalc", {}) or {}).get("enabled", True))
    shipments_after_nc_costed = None
    if recalc:
        shipments_after_nc_costed = add_freight_costs(
            shipments_after_nc,
            df_tariff_wide=tariff_matrix,
            config=cost_cfg,
            out_col="Freight_Cost",
            weight_col_shipments="Weight",
            distance_col_shipments="Euc_Distance",
            weight_col_tariff="Weight_kg",
        )
        shipments_after_nc_costed.to_csv(
            out_dir / f"shipments_after_profiles_costed_{suffix_nc}.csv",
            sep=";",
            encoding="latin1",
            decimal=".",
            index=False,
        )

    # ----------------------------
    # 7) Clustered pattern assignment + apply profiles (KMeans + DBSCAN)
    # ----------------------------
    clustering_yaml = cfg.get("clustering", {}) or {}
    do_clustered = bool(clustering_yaml.get("enabled", False))

    # KMeans results (also aliased as _c for downstream compatibility)
    profiles_c = coords_clustered = None
    pattern_only_c = unchanged_c = shipments_after_c = None
    shipments_after_c_costed = None
    suffix_c = None

    # DBSCAN results
    profiles_dbscan = coords_dbscan = None
    pattern_only_dbscan = unchanged_dbscan = shipments_after_dbscan = None
    shipments_after_dbscan_costed = None
    suffix_dbscan = None

    if do_clustered:
        # ── KMeans ───────────────────────────────────────────────────────
        cl_cfg = ClusteredPatternAssignmentConfig(
            days=int(pat_yaml.get("days", 5)),
            time_limit_ms=time_limit_ms,
            var_weight_max=var_weight_max,
            var_frequency_max=var_frequency_max,
            min_frequency=min_frequency,
            round_border=float(pat_yaml.get("round_border", 0.5)),
            method="kmeans",
            num_clusters=int(clustering_yaml.get("num_clusters", 4)),
            random_state=int(clustering_yaml.get("random_state", 0)),
        )

        profiles_c, coords_clustered = assign_clustered_patterns(
            df_var,
            coord_list,
            cl_cfg,
            save_path=out_dir / "profile_assignment_clustered_kmeans.csv",
        )
        coords_clustered.to_csv(out_dir / "coords_clustered_kmeans.csv", index=False)

        _log_overweight_check(profiles_c, df_var, _app_cfg.max_truck_weight, label="kmeans-clustered")

        pattern_only_c, unchanged_c, shipments_after_c = apply_profiles_to_shipments(
            df_costed, profiles_c, _app_cfg,
        )

        suffix_c = _suffix_from_variability(v_yaml, True, "kmeans")

        pattern_only_c.to_csv(
            out_dir / f"shipments_after_profiles_pattern_only_{suffix_c}.csv",
            sep=";", encoding="latin1", index=False,
        )
        unchanged_c.to_csv(
            out_dir / f"shipments_after_profiles_unchanged_{suffix_c}.csv",
            sep=";", encoding="latin1", index=False,
        )
        shipments_after_c.to_csv(
            out_dir / f"shipments_after_profiles_{suffix_c}.csv",
            sep=";", encoding="latin1", index=False,
        )

        if recalc:
            shipments_after_c_costed = add_freight_costs(
                shipments_after_c,
                df_tariff_wide=tariff_matrix,
                config=cost_cfg,
                out_col="Freight_Cost",
                weight_col_shipments="Weight",
                distance_col_shipments="Euc_Distance",
                weight_col_tariff="Weight_kg",
            )
            shipments_after_c_costed.to_csv(
                out_dir / f"shipments_after_profiles_costed_{suffix_c}.csv",
                sep=";", encoding="latin1", decimal=".", index=False,
            )

        # ── DBSCAN ───────────────────────────────────────────────────────
        cl_cfg_db = ClusteredPatternAssignmentConfig(
            days=int(pat_yaml.get("days", 5)),
            time_limit_ms=time_limit_ms,
            var_weight_max=var_weight_max,
            var_frequency_max=var_frequency_max,
            min_frequency=min_frequency,
            round_border=float(pat_yaml.get("round_border", 0.5)),
            method="dbscan",
            eps=float(clustering_yaml.get("eps", 0.05)),
            min_samples=int(clustering_yaml.get("min_samples", 2)),
        )

        profiles_dbscan, coords_dbscan = assign_clustered_patterns(
            df_var,
            coord_list,
            cl_cfg_db,
            save_path=out_dir / "profile_assignment_clustered_dbscan.csv",
        )
        coords_dbscan.to_csv(out_dir / "coords_clustered_dbscan.csv", index=False)
        suffix_dbscan = _suffix_from_variability(v_yaml, True, "dbscan")

        if not profiles_dbscan.empty:
            _log_overweight_check(profiles_dbscan, df_var, _app_cfg.max_truck_weight, label="dbscan-clustered")

            pattern_only_dbscan, unchanged_dbscan, shipments_after_dbscan = apply_profiles_to_shipments(
                df_costed, profiles_dbscan, _app_cfg,
            )

            pattern_only_dbscan.to_csv(
                out_dir / f"shipments_after_profiles_pattern_only_{suffix_dbscan}.csv",
                sep=";", encoding="latin1", index=False,
            )
            unchanged_dbscan.to_csv(
                out_dir / f"shipments_after_profiles_unchanged_{suffix_dbscan}.csv",
                sep=";", encoding="latin1", index=False,
            )
            shipments_after_dbscan.to_csv(
                out_dir / f"shipments_after_profiles_{suffix_dbscan}.csv",
                sep=";", encoding="latin1", index=False,
            )

            if recalc:
                shipments_after_dbscan_costed = add_freight_costs(
                    shipments_after_dbscan,
                    df_tariff_wide=tariff_matrix,
                    config=cost_cfg,
                    out_col="Freight_Cost",
                    weight_col_shipments="Weight",
                    distance_col_shipments="Euc_Distance",
                    weight_col_tariff="Weight_kg",
                )
                shipments_after_dbscan_costed.to_csv(
                    out_dir / f"shipments_after_profiles_costed_{suffix_dbscan}.csv",
                    sep=";", encoding="latin1", decimal=".", index=False,
                )
        else:
            print("[DBSCAN] All recipients are noise points; no DBSCAN profiles generated.")


    # ----------------------------
    # 7b) Per-recipient before/after summary
    # ----------------------------
    _write_recipient_summary_csv(
        df_original=df_costed,
        pattern_only_nc=pattern_only_nc,
        pattern_only_c=pattern_only_c,
        pattern_only_dbscan=pattern_only_dbscan,
        profiles_nc=profiles_nc,
        profiles_c=profiles_c,
        profiles_dbscan=profiles_dbscan,
        df_var=df_var,
        out_path=out_dir / "recipient_summary.csv",
    )

    # ----------------------------
    # 8) Routing (optional)
    # ----------------------------
    routing_yaml = cfg.get("routing", {}) or {}
    if bool(routing_yaml.get("enabled", False)):
        if durations_rr_path is None or not durations_rr_path.exists():
            print("Warning: routing.enabled=true but durations_rr matrix not available; skipping routing.")
        else:
            route(
                df_added_freightcost=df_costed,
                df_assigned_profile=pattern_only_nc,
                duration_matrix_path=str(durations_rr_path),
                output_json_path=str(out_dir / "routes.json"),
            )
            if do_clustered and pattern_only_c is not None:
                route(
                    df_added_freightcost=df_costed,
                    df_assigned_profile=pattern_only_c,
                    duration_matrix_path=str(durations_rr_path),
                    output_json_path=str(out_dir / "routes_cluster.json"),
                )

    # ----------------------------
    # 9) Maps
    # ----------------------------
    maps_yaml = cfg.get("maps", {}) or {}
    if bool(maps_yaml.get("enabled", True)) and do_clustered:
        map_cfg = MapConfig(
            enabled=True,
            provider=str(maps_yaml.get("provider", "osm")),
            zoom_start=int(maps_yaml.get("zoom_start", 7)),
            anonymize=bool(maps_yaml.get("anonymize", True)),
        )
        _routes_json = out_dir / "routes.json"
        _routes_path = _routes_json if _routes_json.exists() else None
        _sender = (float(sender_lat), float(sender_lon))

        # KMeans map
        if coords_clustered is not None and profiles_c is not None:
            create_cluster_map_html(
                coords_clustered=coords_clustered,
                profiles_clustered=profiles_c,
                out_html=out_dir / "maps" / f"cluster_map_{suffix_c}.html",
                sender_coord=_sender,
                cfg=map_cfg,
                routes_json_path=_routes_path,
            )

        # DBSCAN map (coords contain outlier markers with Cluster=-1 → shown in gray)
        if coords_dbscan is not None and profiles_dbscan is not None and not profiles_dbscan.empty:
            create_cluster_map_html(
                coords_clustered=coords_dbscan,
                profiles_clustered=profiles_dbscan,
                out_html=out_dir / "maps" / f"cluster_map_{suffix_dbscan}.html",
                sender_coord=_sender,
                cfg=map_cfg,
                routes_json_path=_routes_path,
            )

    # ----------------------------
    # 10) Weekday plots
    # ----------------------------
    plots_yaml = cfg.get("plots", {}) or {}
    if bool(plots_yaml.get("enabled", True)):
        write_weekday_plots_pdf(
            df_demand=profiles_nc,
            df_profile=pattern_only_nc,
            df_notprofile=unchanged_nc,
            df_result=shipments_after_nc,
            df_full=df_costed,
            out_pdf=plots_dir / f"weekday_plots_{suffix_nc}.pdf",
            run_name=out_dir.name,
            clustered="Non-Clustered",
        )
        if do_clustered and profiles_c is not None:
            write_weekday_plots_pdf(
                df_demand=profiles_c,
                df_profile=pattern_only_c,
                df_notprofile=unchanged_c,
                df_result=shipments_after_c,
                df_full=df_costed,
                out_pdf=plots_dir / f"weekday_plots_{suffix_c}.pdf",
                run_name=out_dir.name,
                clustered="KMeans Clustered",
            )

        if do_clustered and profiles_dbscan is not None and not profiles_dbscan.empty:
            write_weekday_plots_pdf(
                df_demand=profiles_dbscan,
                df_profile=pattern_only_dbscan,
                df_notprofile=unchanged_dbscan,
                df_result=shipments_after_dbscan,
                df_full=df_costed,
                out_pdf=plots_dir / f"weekday_plots_{suffix_dbscan}.pdf",
                run_name=out_dir.name,
                clustered="DBSCAN Clustered",
            )

        # Comparison charts — up to 4 bars per weekday
        df_profiled_for_plot = shipments_after_nc_costed if shipments_after_nc_costed is not None else shipments_after_nc
        df_kmeans_for_plot   = None
        df_dbscan_for_plot   = None
        if do_clustered and shipments_after_c is not None:
            df_kmeans_for_plot = shipments_after_c_costed if shipments_after_c_costed is not None else shipments_after_c
        if do_clustered and shipments_after_dbscan is not None:
            df_dbscan_for_plot = shipments_after_dbscan_costed if shipments_after_dbscan_costed is not None else shipments_after_dbscan

        # Union of all profiled IDs for the subset page (page 2)
        _profiled_ids: set[int] = set(profiles_nc["Recipient_ID"].astype(int).tolist())
        if do_clustered and profiles_c is not None:
            _profiled_ids |= set(profiles_c["Recipient_ID"].astype(int).tolist())
        if do_clustered and profiles_dbscan is not None and not profiles_dbscan.empty:
            _profiled_ids |= set(profiles_dbscan["Recipient_ID"].astype(int).tolist())

        write_freight_cost_comparison_pdf(
            df_original=df_costed,
            df_profiled=df_profiled_for_plot,
            df_clustered=df_kmeans_for_plot,
            df_clustered_dbscan=df_dbscan_for_plot,
            out_pdf=plots_dir / "freight_cost_comparison.pdf",
            profiled_ids=_profiled_ids,
        )

        write_weight_distribution_pdf(
            df_original=df_costed,
            df_profiled=df_profiled_for_plot,
            df_clustered=df_kmeans_for_plot,
            df_clustered_dbscan=df_dbscan_for_plot,
            out_pdf=plots_dir / "weight_distribution_comparison.pdf",
            profiled_ids=_profiled_ids,
        )

        # Summary uses KMeans as the primary "clustered" reference
        write_pipeline_summary(
            df_original=df_costed,
            df_profiled=df_profiled_for_plot,
            df_clustered=df_kmeans_for_plot,
            df_var=df_var,
            profiled_ids=_profiled_ids,
            pattern_only_nc=pattern_only_nc,
            pattern_only_c=pattern_only_c,
            var_weight_max=var_weight_max,
            var_frequency_max=var_frequency_max,
            min_frequency=min_frequency,
            max_truck_weight=_app_cfg.max_truck_weight,
            plots_dir=plots_dir,
        )

    # ----------------------------
    # Tableau export
    # ----------------------------
    _tableau_profiled = shipments_after_nc_costed if shipments_after_nc_costed is not None else shipments_after_nc
    _tableau_kmeans   = (shipments_after_c_costed      if shipments_after_c_costed      is not None else shipments_after_c)      if do_clustered else None
    _tableau_dbscan   = (shipments_after_dbscan_costed if shipments_after_dbscan_costed is not None else shipments_after_dbscan) if (do_clustered and shipments_after_dbscan is not None) else None
    _write_tableau_export(
        df_original=df_costed,
        df_profiled=_tableau_profiled,
        df_clustered=_tableau_kmeans,
        df_clustered_dbscan=_tableau_dbscan,
        out_path=out_dir / "tableau_export.csv",
    )

    # ----------------------------
    # Return (useful for notebooks/tests)
    # ----------------------------
    return {
        "out_dir": str(out_dir),
        "run_id": out_dir.name,
        "tableau_export": str(out_dir / "tableau_export.csv"),
        "recipient_summary": str(out_dir / "recipient_summary.csv"),

        "shipments_preprocessed": df_pre,
        "shipments_with_coords": df_coords,
        "shipments_with_distances": df_with_sender_distances,
        "shipments_with_costs": df_costed,

        "weekly_frequency": df_freq,
        "weekly_weight": df_w,
        "variability": df_var,

        # NON-CLUSTERED
        "profiles_nonclustered": profiles_nc,
        "run_suffix_nonclustered": suffix_nc,
        "shipments_after_profiles_nonclustered": shipments_after_nc,
        "shipments_after_profiles_pattern_only_nonclustered": pattern_only_nc,
        "shipments_after_profiles_unchanged_nonclustered": unchanged_nc,
        "shipments_after_profiles_costed_nonclustered": shipments_after_nc_costed,

        # KMEANS CLUSTERED (optional)
        "profiles_clustered": profiles_c,
        "coords_clustered": coords_clustered,
        "run_suffix_clustered": suffix_c,
        "shipments_after_profiles_clustered": shipments_after_c,
        "shipments_after_profiles_pattern_only_clustered": pattern_only_c,
        "shipments_after_profiles_unchanged_clustered": unchanged_c,
        "shipments_after_profiles_costed_clustered": shipments_after_c_costed,

        # DBSCAN CLUSTERED (optional)
        "profiles_clustered_dbscan": profiles_dbscan,
        "coords_clustered_dbscan": coords_dbscan,
        "run_suffix_clustered_dbscan": suffix_dbscan,
        "shipments_after_profiles_clustered_dbscan": shipments_after_dbscan,
        "shipments_after_profiles_pattern_only_clustered_dbscan": pattern_only_dbscan,
        "shipments_after_profiles_unchanged_clustered_dbscan": unchanged_dbscan,
        "shipments_after_profiles_costed_clustered_dbscan": shipments_after_dbscan_costed,

        # Matrices (optional depending on compute/load inputs)
        "distances_RR": distances_RR,
        "durations_RR": durations_RR,
        "euclidean_RR": euclidean_RR,
        "matrix_table": matrix_table,
    }
