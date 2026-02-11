from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import quote_plus


@dataclass(frozen=True)
class GeoConfig:
    """
    Public-safe defaults:
    - base_url is configurable (no hardcoding in code)
    - caching avoids repeated geocoding calls
    - rate_limit_seconds avoids overloading the service
    """
    base_url: str = "https://asca-rest.lfo.tu-dortmund.de/nominatim/search.php"
    format_param: str = "jsonv2"

    timeout_seconds: int = 20
    max_retries: int = 3
    backoff_factor: float = 0.6

    rate_limit_seconds: float = 1.0  # be polite; Nominatim-style services usually require it
    user_agent: str = "delivery-pattern-optimization/1.0 (contact: your-email@example.com)"


# -----------------------------------------------------------------------------
# Session with retries
# -----------------------------------------------------------------------------

def _build_session(cfg: GeoConfig) -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": cfg.user_agent})

    retry = Retry(
        total=cfg.max_retries,
        connect=cfg.max_retries,
        read=cfg.max_retries,
        status=cfg.max_retries,
        backoff_factor=cfg.backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


# -----------------------------------------------------------------------------
# Core geocoding functions (refactor of your code)
# -----------------------------------------------------------------------------

def build_address(row: pd.Series) -> str:
    """
    Build an address string from your expected columns.
    """
    return f"{row['Recipient_Street']}, {row['Recipient_Postal_Code']}, {row['Recipient_City']}"


def geocode_address(
    session: requests.Session,
    address: str,
    cfg: GeoConfig,
) -> Optional[Tuple[float, float]]:
    """
    Returns (lon, lat) or None.
    Uses quote_plus to safely encode spaces/special characters.
    """
    q = quote_plus(address)
    url = f"{cfg.base_url}?q={q}&format={cfg.format_param}"

    resp = session.get(url, timeout=cfg.timeout_seconds)
    if not resp.ok:
        return None

    try:
        data = resp.json()
    except Exception:
        return None

    if not data:
        return None

    # Nominatim typically returns strings
    lon = float(data[0]["lon"])
    lat = float(data[0]["lat"])
    return lon, lat


def get_receiver_coordinates(
    row: pd.Series,
    session: requests.Session,
    cfg: GeoConfig,
) -> Optional[Dict[str, Any]]:
    """
    Your original output structure preserved:
      {"Empfänger_id": ..., "longitude": ..., "latitude": ...}
    """
    address = build_address(row)
    res = geocode_address(session, address, cfg)
    if res is None:
        return None
    lon, lat = res
    return {
        "Empfänger_id": int(row["Recipient_ID"]),
        "longitude": round(float(lon), 6),
        "latitude": round(float(lat), 6),
    }


# -----------------------------------------------------------------------------
# JSON read/write helpers (compatible with your current JSON format)
# -----------------------------------------------------------------------------

def write_coordinates_to_file(coordinates_list: List[Dict[str, Any]], json_path: str | Path) -> None:
    json_path = Path(json_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(coordinates_list, f, ensure_ascii=False, indent=2)
    print(f"Coordinates have been saved in {json_path} file.")


def read_coordinates_from_file(json_path: str | Path) -> List[Dict[str, Any]]:
    json_path = Path(json_path)
    if not json_path.exists():
        return []
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------------------------------------------------------
# Caching layer
# -----------------------------------------------------------------------------

def _coords_to_index(coords: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    return {int(c["Empfänger_id"]): c for c in coords if c is not None}


def get_and_write_receiver_coordinates(
    df_unique: pd.DataFrame,
    json_coordinate_list_path: str | Path,
    cfg: GeoConfig = GeoConfig(),
    *,
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    """
    Equivalent to your:
      coordinates_list = df.apply(get_receiver_coordinates, axis=1).tolist()
    But:
      - uses a session with retries
      - rate limits
      - caches existing coordinates by Recipient_ID
    """
    df_unique = df_unique.copy()
    df_unique["Recipient_ID"] = df_unique["Recipient_ID"].astype(int)

    existing: List[Dict[str, Any]] = read_coordinates_from_file(json_coordinate_list_path) if use_cache else []
    cache = _coords_to_index(existing)

    session = _build_session(cfg)
    out: List[Dict[str, Any]] = []

    for _, row in df_unique.iterrows():
        rid = int(row["Recipient_ID"])
        if use_cache and rid in cache:
            out.append(cache[rid])
            continue

        coords = get_receiver_coordinates(row, session, cfg)
        if coords is not None:
            out.append(coords)
            cache[rid] = coords

        time.sleep(cfg.rate_limit_seconds)

    # Write merged list (existing + new)
    merged = list(cache.values()) if use_cache else out
    merged = sorted(merged, key=lambda x: int(x["Empfänger_id"]))
    write_coordinates_to_file(merged, json_coordinate_list_path)

    return merged


# -----------------------------------------------------------------------------
# Add coords into main dataframe (refactor of your add_coordinates_to_df)
# -----------------------------------------------------------------------------

def add_coordinates_to_df(
    lon_lat_list: List[Dict[str, Any]],
    df: pd.DataFrame,
    sender_lon: float,
    sender_lat: float,
    *,
    recipient_id_col: str = "Recipient_ID",
    out_rec_lon_col: str = "Recipient_Longitude",
    out_rec_lat_col: str = "Recipient_Latitude",
    out_sender_lon_col: str = "Sender_Longitude",
    out_sender_lat_col: str = "Sender_Latitude",
) -> pd.DataFrame:
    """
    Adds:
      Recipient_Longitude, Recipient_Latitude, Sender_Longitude, Sender_Latitude
    """
    df = df.copy()
    df[recipient_id_col] = df[recipient_id_col].astype(int)

    idx = _coords_to_index(lon_lat_list)

    def update_row(row: pd.Series) -> pd.Series:
        rid = int(row[recipient_id_col])
        c = idx.get(rid)

        row[out_rec_lon_col] = float(c["longitude"]) if c else None
        row[out_rec_lat_col] = float(c["latitude"]) if c else None
        row[out_sender_lon_col] = float(sender_lon)
        row[out_sender_lat_col] = float(sender_lat)
        return row

    df = df.apply(update_row, axis=1)

    df[[out_rec_lon_col, out_rec_lat_col]] = (
        df[[out_rec_lon_col, out_rec_lat_col]].astype(float).round(6)
    )
    return df


def add_coordinates(
    processed_data: pd.DataFrame,
    sender_lon: float,
    sender_lat: float,
    save_path: str | Path,
    json_coordinate_list_path: str | Path,
    cfg: GeoConfig = GeoConfig(),
    *,
    use_cache: bool = True,
) -> tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Full end-to-end like your original add_coordinates():
      - unique recipients
      - geocode + write cache JSON
      - add coords to processed_data
      - save csv (optional but preserved here because your old function did it)
    """
    processed_data = processed_data.copy()

    # Geocode once per recipient
    unique_df = processed_data.drop_duplicates(subset=["Recipient_ID"])
    coords_list = get_and_write_receiver_coordinates(
        unique_df,
        json_coordinate_list_path=json_coordinate_list_path,
        cfg=cfg,
        use_cache=use_cache,
    )

    added = add_coordinates_to_df(coords_list, processed_data, sender_lon, sender_lat)

    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    added.to_csv(path_or_buf=save_path, sep=";", encoding="latin1", decimal=".", index=False)

    print(f"Coordinates have been calculated and the dataframe is saved in: {save_path}")
    return added, coords_list


def round_sort_coordinates_original(file_path: str | Path) -> List[Dict[str, Any]]:
    """
    Backwards-compatible: read coordinate list JSON.
    """
    return read_coordinates_from_file(file_path)