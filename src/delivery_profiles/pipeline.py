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
from .maps import create_cluster_map_html, MapConfig


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

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


def _suffix_from_variability(v: Dict[str, Any], clustered: bool) -> str:
    base = (
        f"vw{_fmt_float(v.get('var_weight_max', 100))}"
        f"_vf{_fmt_float(v.get('var_frequency_max', 100))}"
        f"_mf{int(float(v.get('min_frequency', 1)))}"
    )
    return ("clustered_" + base) if clustered else base


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
        base_url=str(geo_yaml.get("base_url")),
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
    df_with_sender_distances: pd.DataFrame

    if dist_mode == "compute":
        osrm_yaml = (dist_yaml.get("osrm", {}) or {})
        osrm_cfg = OSRMConfig(
            base_url=str(osrm_yaml.get("base_url", OSRMConfig().base_url)),
            chunk_size=int(osrm_yaml.get("chunk_size", OSRMConfig().chunk_size)),
            rate_limit_seconds=float(osrm_yaml.get("rate_limit_seconds", OSRMConfig().rate_limit_seconds)),
            timeout_seconds=int(osrm_yaml.get("timeout_seconds", OSRMConfig().timeout_seconds)),
            symmetrize=bool(osrm_yaml.get("symmetrize", False)),
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

    profiles_nc = assign_patterns(
        df_var,
        pa_cfg,
        save_path=out_dir / "profile_assignment.csv",
    )

    pattern_only_nc, unchanged_nc, shipments_after_nc = apply_profiles_to_shipments(
        df_costed,
        profiles_nc,
        ProfileApplicationConfig(),
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
    # 7) Clustered pattern assignment + apply profiles (optional, like old main.py)
    # ----------------------------
    clustering_yaml = cfg.get("clustering", {}) or {}
    do_clustered = bool(clustering_yaml.get("enabled", False))

    profiles_c = coords_clustered = None
    pattern_only_c = unchanged_c = shipments_after_c = None
    shipments_after_c_costed = None
    suffix_c = None

    if do_clustered:
        cl_cfg = ClusteredPatternAssignmentConfig(
            days=int(pat_yaml.get("days", 5)),
            time_limit_ms=time_limit_ms,
            var_weight_max=var_weight_max,
            var_frequency_max=var_frequency_max,
            min_frequency=min_frequency,
            round_border=float(pat_yaml.get("round_border", 0.5)),
            num_clusters=int(clustering_yaml.get("num_clusters", 4)),
            random_state=int(clustering_yaml.get("random_state", 0)),
        )

        profiles_c, coords_clustered = assign_clustered_patterns(
            df_var,
            coord_list,
            cl_cfg,
            save_path=out_dir / "profile_assignment_clustered.csv",
        )
        coords_clustered.to_csv(out_dir / "coords_clustered.csv", index=False)

        pattern_only_c, unchanged_c, shipments_after_c = apply_profiles_to_shipments(
            df_costed,
            profiles_c,
            ProfileApplicationConfig(),
        )

        suffix_c = _suffix_from_variability(v_yaml, clustered=True)

        pattern_only_c.to_csv(
            out_dir / f"shipments_after_profiles_pattern_only_{suffix_c}.csv",
            sep=";",
            encoding="latin1",
            index=False,
        )
        unchanged_c.to_csv(
            out_dir / f"shipments_after_profiles_unchanged_{suffix_c}.csv",
            sep=";",
            encoding="latin1",
            index=False,
        )
        shipments_after_c.to_csv(
            out_dir / f"shipments_after_profiles_{suffix_c}.csv",
            sep=";",
            encoding="latin1",
            index=False,
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
                sep=";",
                encoding="latin1",
                decimal=".",
                index=False,
            )


    # ----------------------------
    # 8) Maps
    # ----------------------------
    maps_yaml = cfg.get("maps", {}) or {}
    if bool(maps_yaml.get("enabled", True)) and coords_clustered is not None and profiles_c is not None:
        map_cfg = MapConfig(
            enabled=True,
            provider=str(maps_yaml.get("provider", "osm")),  # "osm" | "google_roadmap" | "google_satellite"
            zoom_start=int(maps_yaml.get("zoom_start", 7)),
            anonymize=bool(maps_yaml.get("anonymize", True)),
        )

        out_html = create_cluster_map_html(
            coords_clustered=coords_clustered,
            profiles_clustered=profiles_c,
            out_html=out_dir / "maps" / f"cluster_map_{suffix_c}.html",
            sender_coord=(float(sender_lat), float(sender_lon)),
            cfg=map_cfg,
        )

    # ----------------------------
    # Return (useful for notebooks/tests)
    # ----------------------------
    return {
        "out_dir": str(out_dir),
        "run_id": out_dir.name,

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

        # CLUSTERED (optional)
        "profiles_clustered": profiles_c,
        "coords_clustered": coords_clustered,
        "run_suffix_clustered": suffix_c,
        "shipments_after_profiles_clustered": shipments_after_c,
        "shipments_after_profiles_pattern_only_clustered": pattern_only_c,
        "shipments_after_profiles_unchanged_clustered": unchanged_c,
        "shipments_after_profiles_costed_clustered": shipments_after_c_costed,

        # Matrices (optional depending on compute/load inputs)
        "distances_RR": distances_RR,
        "durations_RR": durations_RR,
        "euclidean_RR": euclidean_RR,
        "matrix_table": matrix_table,
    }
