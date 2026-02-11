from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import folium
import pandas as pd


@dataclass(frozen=True)
class MapConfig:
    enabled: bool = True
    # "osm" (safe default) or "google_roadmap" / "google_satellite"
    provider: str = "osm"
    zoom_start: int = 7
    anonymize: bool = True


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _add_google_tiles(m: folium.Map, kind: str) -> None:
    """
    Adds Google tiles as a base layer.
    NOTE: This is a common Folium trick. If you need strict Google ToS compliance,
    use Google Maps JS API with an API key instead.
    """
    if kind == "google_roadmap":
        folium.TileLayer(
            tiles="https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
            attr="Google",
            name="Google Roadmap",
            subdomains=["mt0", "mt1", "mt2", "mt3"],
            overlay=False,
            control=True,
        ).add_to(m)
    elif kind == "google_satellite":
        folium.TileLayer(
            tiles="https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            attr="Google",
            name="Google Satellite",
            subdomains=["mt0", "mt1", "mt2", "mt3"],
            overlay=False,
            control=True,
        ).add_to(m)


def create_cluster_map_html(
    coords_clustered: pd.DataFrame,
    profiles_clustered: pd.DataFrame,
    *,
    out_html: Path,
    sender_coord: Optional[Tuple[float, float]] = None,
    cfg: MapConfig = MapConfig(),
    # expected columns from your new clustered assignment:
    coord_id_col: str = "Empfänger_id",
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    cluster_col: str = "Cluster",
    prof_id_col: str = "Recipient_ID",
    prof_cluster_col: str = "Cluster",
    prof_pattern_col: str = "Pattern_clear",
) -> Path:
    """
    Creates an interactive HTML map:
    - markers colored by cluster
    - popup shows recipient + cluster + assigned pattern
    """
    if coords_clustered is None or coords_clustered.empty:
        raise ValueError("coords_clustered is empty. Did clustering run / coords saved?")

    if profiles_clustered is None or profiles_clustered.empty:
        raise ValueError("profiles_clustered is empty. Did clustered pattern assignment run?")

    # normalize types
    coords = coords_clustered.copy()
    coords[coord_id_col] = pd.to_numeric(coords[coord_id_col], errors="coerce").astype("Int64")
    coords[cluster_col] = pd.to_numeric(coords[cluster_col], errors="coerce").astype("Int64")
    coords[lat_col] = pd.to_numeric(coords[lat_col], errors="coerce")
    coords[lon_col] = pd.to_numeric(coords[lon_col], errors="coerce")
    coords = coords.dropna(subset=[coord_id_col, cluster_col, lat_col, lon_col]).copy()

    prof = profiles_clustered.copy()
    prof[prof_id_col] = pd.to_numeric(prof[prof_id_col], errors="coerce").astype("Int64")
    prof[prof_cluster_col] = pd.to_numeric(prof[prof_cluster_col], errors="coerce").astype("Int64")
    prof = prof.set_index([prof_id_col, prof_cluster_col])

    # center
    center = (float(coords[lat_col].mean()), float(coords[lon_col].mean()))

    # base map
    m = folium.Map(location=center, zoom_start=int(cfg.zoom_start), tiles="OpenStreetMap")

    if cfg.provider in ("google_roadmap", "google_satellite"):
        _add_google_tiles(m, cfg.provider)

    # color palette
    base_colors = [
        "red", "blue", "green", "orange", "purple", "cadetblue",
        "darkred", "darkblue", "darkgreen", "gray"
    ]
    cluster_ids = sorted(coords[cluster_col].dropna().unique().tolist())
    cluster_color_map: Dict[int, str] = {int(c): base_colors[i % len(base_colors)] for i, c in enumerate(cluster_ids)}

    # markers
    for _, r in coords.iterrows():
        rid = int(r[coord_id_col])
        cl = int(r[cluster_col])

        try:
            pattern = prof.loc[(rid, cl)][prof_pattern_col]
        except Exception:
            pattern = "NA"

        if cfg.anonymize:
            popup = f"Recipient: {rid} | Cluster: {cl} | Profile: {pattern}"
        else:
            popup = f"Recipient_ID={rid}, Cluster={cl}, Pattern={pattern}"

        folium.CircleMarker(
            location=(float(r[lat_col]), float(r[lon_col])),
            radius=5,
            color=cluster_color_map.get(cl, "black"),
            fill=True,
            fill_color=cluster_color_map.get(cl, "black"),
            popup=popup,
        ).add_to(m)

    # sender marker
    if sender_coord is not None:
        folium.Marker(
            location=[sender_coord[0], sender_coord[1]],
            popup="Sender/Depot",
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(m)

    folium.LayerControl().add_to(m)

    _ensure_dir(out_html.parent)
    m.save(str(out_html))
    return out_html
