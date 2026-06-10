from __future__ import annotations

import json
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


_ROUTE_COLORS: Dict[str, str] = {
    "Monday":    "blue",
    "Tuesday":   "green",
    "Wednesday": "orange",
    "Thursday":  "red",
    "Friday":    "purple",
}


def _add_route_overlays(
    m: folium.Map,
    routes_json_path: Path,
    coords: pd.DataFrame,
    sender_coord: Tuple[float, float],
    *,
    coord_id_col: str = "Empfänger_id",
    lat_col: str = "latitude",
    lon_col: str = "longitude",
) -> None:
    """
    Read routes.json and draw per-weekday, per-vehicle polylines.
    Each weekday gets its own FeatureGroup (toggleable via LayerControl).
    A legend box is injected as static HTML.
    """
    try:
        with open(routes_json_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[Maps] Could not load routes from {routes_json_path}: {e}")
        return

    if not isinstance(data, list):
        data = [data]

    # Build {int_rid: (lat, lon)} lookup from coords df
    coord_lookup: Dict[int, Tuple[float, float]] = {}
    for _, r in coords.iterrows():
        try:
            rid_val = int(r[coord_id_col])
            coord_lookup[rid_val] = (float(r[lat_col]), float(r[lon_col]))
        except Exception:
            pass

    weekdays_drawn: list = []

    for weekday_entry in data:
        weekday = str(weekday_entry.get("Weekday", "Unknown"))
        color   = _ROUTE_COLORS.get(weekday, "gray")
        fg      = folium.FeatureGroup(name=f"Routes — {weekday}", show=True)
        drew_any = False

        for vehicle_route in weekday_entry.get("Routes", []):
            stops    = vehicle_route.get("route", [])
            if not stops:
                continue

            vid      = vehicle_route.get("vehicle_id", "?")
            duration = float(vehicle_route.get("duration", 0))

            # Build sequence: depot → stop1 → … → depot
            pts: list = [sender_coord]
            for stop in stops:
                try:
                    rid = int(stop.get("Recipient_ID", -1))
                except (ValueError, TypeError):
                    continue
                if rid in coord_lookup:
                    pts.append(coord_lookup[rid])
                # silently skip recipients without coordinates

            if len(pts) < 2:
                continue

            pts.append(sender_coord)  # return to depot

            tooltip = f"Vehicle {vid} | {weekday} | {duration:.1f} min"
            folium.PolyLine(
                locations=pts,
                color=color,
                weight=2.5,
                opacity=0.8,
                tooltip=tooltip,
                popup=folium.Popup(tooltip, max_width=220),
            ).add_to(fg)
            drew_any = True

        if drew_any:
            fg.add_to(m)
            if weekday not in weekdays_drawn:
                weekdays_drawn.append(weekday)

    if not weekdays_drawn:
        return

    # Inject legend (only weekdays that actually have routes)
    legend_rows = "".join(
        f'<div style="display:flex;align-items:center;margin:2px 0">'
        f'<span style="display:inline-block;width:14px;height:4px;'
        f'background:{_ROUTE_COLORS.get(d,"gray")};border-radius:2px;margin-right:6px"></span>'
        f'{d}</div>'
        for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        if d in weekdays_drawn
    )
    legend_html = (
        '<div style="position:fixed;bottom:40px;right:10px;z-index:1000;background:white;'
        'padding:10px 14px;border:1px solid #aaa;border-radius:6px;font-size:12px;'
        'box-shadow:2px 2px 6px rgba(0,0,0,.25)">'
        f'<b style="display:block;margin-bottom:4px">Route Weekdays</b>{legend_rows}'
        '</div>'
    )
    m.get_root().html.add_child(folium.Element(legend_html))


def create_cluster_map_html(
    coords_clustered: pd.DataFrame,
    profiles_clustered: pd.DataFrame,
    *,
    out_html: Path,
    sender_coord: Optional[Tuple[float, float]] = None,
    cfg: MapConfig = MapConfig(),
    routes_json_path: Optional[Path] = None,
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
    - optional route polylines (per weekday) when routes_json_path is provided
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

    # sender marker — black pin with house icon, distinct from all cluster circle markers
    if sender_coord is not None:
        folium.Marker(
            location=[sender_coord[0], sender_coord[1]],
            popup="Sender / Depot",
            icon=folium.Icon(color="black", icon="home", prefix="glyphicon"),
        ).add_to(m)

    # route polylines (only when routing.enabled=true and routes.json exists)
    if routes_json_path is not None and routes_json_path.exists():
        depot = sender_coord if sender_coord is not None else (float(coords[lat_col].mean()), float(coords[lon_col].mean()))
        _add_route_overlays(
            m,
            routes_json_path,
            coords,
            depot,
            coord_id_col=coord_id_col,
            lat_col=lat_col,
            lon_col=lon_col,
        )

    folium.LayerControl().add_to(m)

    _ensure_dir(out_html.parent)
    m.save(str(out_html))
    return out_html
