from __future__ import annotations

import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# -----------------------------------------------------------------------------
# Config + session
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class OSRMConfig:
    base_url: str = "https://asca-rest.lfo.tu-dortmund.de/osrm/table/v1/driving/"
    annotations: str = "distance,duration"

    timeout_seconds: int = 60
    max_retries: int = 3
    backoff_factor: float = 0.6
    rate_limit_seconds: float = 0.2  # small delay between calls

    chunk_size: int = 100  # OSRM table endpoints often limit table sizes


def _build_session(cfg: OSRMConfig) -> requests.Session:
    s = requests.Session()
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
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s


# -----------------------------------------------------------------------------
# Coordinate normalization (compatible with your JSON structure)
# -----------------------------------------------------------------------------

def round_sort_coordinates(locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Input: list like [{"Empfänger_id": 123, "latitude": "...", "longitude": "..."}]
    Output: unique by Empfänger_id, rounded to 6 decimals, sorted ascending by ID.
    """
    cleaned = []
    for loc in locations:
        cleaned.append(
            {
                "Empfänger_id": int(loc["Empfänger_id"]),
                "latitude": round(float(loc["latitude"]), 6),
                "longitude": round(float(loc["longitude"]), 6),
            }
        )
    uniq = {d["Empfänger_id"]: d for d in cleaned}
    return sorted(uniq.values(), key=lambda x: x["Empfänger_id"])


def coords_from_dataframe(
    df: pd.DataFrame,
    *,
    id_col: str = "Recipient_ID",
    lat_col: str = "Recipient_Latitude",
    lon_col: str = "Recipient_Longitude",
    out_id_key: str = "Empfänger_id",
) -> List[Dict[str, Any]]:
    """
    Build location list in your JSON shape from a dataframe.
    """
    tmp = df[[id_col, lat_col, lon_col]].drop_duplicates().copy()
    tmp[id_col] = tmp[id_col].astype(int)
    tmp[lat_col] = tmp[lat_col].astype(float)
    tmp[lon_col] = tmp[lon_col].astype(float)

    out = []
    for _, r in tmp.iterrows():
        out.append(
            {
                out_id_key: int(r[id_col]),
                "latitude": round(float(r[lat_col]), 6),
                "longitude": round(float(r[lon_col]), 6),
            }
        )
    return round_sort_coordinates(out)


# -----------------------------------------------------------------------------
# Haversine / "Euclidean" distance matrix (fast)
# -----------------------------------------------------------------------------
def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance between two points (lat/lon in degrees), result in km."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return float(EARTH_RADIUS_KM * c)

def haversine_matrix_km(coords_lat_lon: np.ndarray) -> np.ndarray:
    """
    coords_lat_lon: shape (n,2) -> [lat, lon] in degrees
    returns: shape (n,n) distances in km
    """
    lat = np.radians(coords_lat_lon[:, 0])[:, None]
    lon = np.radians(coords_lat_lon[:, 1])[:, None]
    dlat = lat - lat.T
    dlon = lon - lon.T
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat) * np.cos(lat.T) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return EARTH_RADIUS_KM * c

def haversine_distance_matrix_km(sorted_locations: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Computes symmetric haversine distance matrix (km) between all recipients.
    No external 'haversine' dependency.
    """
    df = pd.json_normalize(sorted_locations)
    df["latitude"] = df["latitude"].astype(float)
    df["longitude"] = df["longitude"].astype(float)

    ids = df["Empfänger_id"].astype(int).tolist()

    # coords as numpy array shape (n,2): [lat, lon]
    coords = df[["latitude", "longitude"]].to_numpy(dtype=float)

    mat = haversine_matrix_km(coords)
    return pd.DataFrame(mat, index=ids, columns=ids)

# -----------------------------------------------------------------------------
# OSRM table distances/durations with chunking (fixed indexing!)
# -----------------------------------------------------------------------------

def osrm_table_chunk(
    session: requests.Session,
    cfg: OSRMConfig,
    chunk1: List[Dict[str, Any]],
    chunk2: List[Dict[str, Any]],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calls OSRM table for chunk1 -> chunk2.
    Returns (distances, durations) arrays of shape (len(chunk1), len(chunk2)).
    """
    params = {"annotations": cfg.annotations}

    locations_str = ";".join(
        [f"{loc['longitude']},{loc['latitude']}" for loc in (chunk1 + chunk2)]
    )
    url = cfg.base_url + locations_str

    # sources are 0..len(chunk1)-1, destinations are len(chunk1)..len(chunk1)+len(chunk2)-1
    params["sources"] = ";".join(str(i) for i in range(len(chunk1)))
    params["destinations"] = ";".join(str(i + len(chunk1)) for i in range(len(chunk2)))

    resp = session.get(url, params=params, timeout=cfg.timeout_seconds)
    if not resp.ok:
        raise RuntimeError(f"OSRM request failed {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    if "distances" not in data or "durations" not in data:
        raise RuntimeError(f"Unexpected OSRM response keys: {list(data.keys())}")

    return np.asarray(data["distances"], dtype=float), np.asarray(data["durations"], dtype=float)


def calculate_distances_durations_osrm(
    sorted_locations: List[Dict[str, Any]],
    cfg: OSRMConfig = OSRMConfig(),
    *,
    symmetrize: bool = False,
    save_distances_path: Optional[str | Path] = None,
    save_durations_path: Optional[str | Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Chunked OSRM distance + duration matrices.

    Critical fix vs your version:
    - we fill using explicit row/col ID lists, not loc[start:end].

    symmetrize:
    - if True, force symmetric by averaging A->B and B->A
      (OSRM driving can be asymmetric; default False preserves OSRM truth)
    """
    session = _build_session(cfg)

    ids = [int(loc["Empfänger_id"]) for loc in sorted_locations]
    n = len(ids)
    distances = pd.DataFrame(np.nan, index=ids, columns=ids)
    durations = pd.DataFrame(np.nan, index=ids, columns=ids)

    chunk_size = cfg.chunk_size
    num_chunks = math.ceil(n / chunk_size)

    for i in range(num_chunks):
        for j in range(num_chunks):
            i_start, i_end = i * chunk_size, min((i + 1) * chunk_size, n)
            j_start, j_end = j * chunk_size, min((j + 1) * chunk_size, n)

            chunk1 = sorted_locations[i_start:i_end]
            chunk2 = sorted_locations[j_start:j_end]

            row_ids = [int(loc["Empfänger_id"]) for loc in chunk1]
            col_ids = [int(loc["Empfänger_id"]) for loc in chunk2]

            dists, durs = osrm_table_chunk(session, cfg, chunk1, chunk2)

            # Fill explicitly (safe even if IDs are not contiguous)
            distances.loc[row_ids, col_ids] = dists
            durations.loc[row_ids, col_ids] = durs

            time.sleep(cfg.rate_limit_seconds)

    if symmetrize:
        distances = (distances + distances.T) / 2.0
        durations = (durations + durations.T) / 2.0

    # Save (optional)
    if save_distances_path:
        p = Path(save_distances_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        distances.to_csv(p, sep=",", decimal=".", index=True)

    if save_durations_path:
        p = Path(save_durations_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        durations.to_csv(p, sep=",", decimal=".", index=True)

    return distances, durations


# -----------------------------------------------------------------------------
# Combined table of pairwise distances (upper triangle)
# -----------------------------------------------------------------------------

def create_matrix_table(
    euclidean: pd.DataFrame,
    distances: pd.DataFrame,
    durations: pd.DataFrame,
    *,
    save_path: Optional[str | Path] = None,
) -> pd.DataFrame:
    """
    Returns a table with columns:
      Start, End, Real, Duration, Euclidean
    for Start < End (upper triangle).
    """
    ids = list(euclidean.columns)
    rows: List[Dict[str, Any]] = []

    for i, start_id in enumerate(ids):
        for end_id in ids[i + 1 :]:
            rows.append(
                {
                    "Start": start_id,
                    "End": end_id,
                    "Real": float(distances.at[start_id, end_id]),
                    "Duration": float(durations.at[start_id, end_id]),
                    "Euclidean": float(euclidean.at[start_id, end_id]),
                }
            )

    result = pd.DataFrame(rows)

    if save_path:
        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(p, sep=",", decimal=".", index=False)

    return result


# -----------------------------------------------------------------------------
# Sender -> recipients distances/durations + euclidean
# -----------------------------------------------------------------------------

def calculate_sender_to_recipients_osrm(
    df: pd.DataFrame,
    sender_lon: float,
    sender_lat: float,
    cfg: OSRMConfig = OSRMConfig(),
    *,
    rec_lon_col: str = "Recipient_Longitude",
    rec_lat_col: str = "Recipient_Latitude",
    out_real_col: str = "Real_Distance",
    out_duration_col: str = "Duration",
    save_distances_path: Optional[str | Path] = None,
    save_durations_path: Optional[str | Path] = None,
) -> pd.DataFrame:
    """
    Adds Real_Distance and Duration columns for sender->recipient using OSRM.
    Chunked for large numbers of recipients.
    """
    session = _build_session(cfg)
    out = df.copy()

    out[rec_lat_col] = out[rec_lat_col].astype(float)
    out[rec_lon_col] = out[rec_lon_col].astype(float)

    n = len(out)
    chunk_size = cfg.chunk_size
    num_chunks = math.ceil(n / chunk_size)

    # Optional matrices (1 x N)
    dist_row = np.full((n,), np.nan, dtype=float)
    dur_row = np.full((n,), np.nan, dtype=float)

    base_url = cfg.base_url
    params = {"annotations": cfg.annotations}

    for i in range(num_chunks):
        i_start, i_end = i * chunk_size, min((i + 1) * chunk_size, n)
        chunk = out.iloc[i_start:i_end]

        locations_str = f"{sender_lon},{sender_lat};" + ";".join(
            [f"{r[rec_lon_col]},{r[rec_lat_col]}" for _, r in chunk.iterrows()]
        )

        url = base_url + locations_str
        params["sources"] = "0"
        params["destinations"] = ";".join(str(k + 1) for k in range(len(chunk)))

        resp = session.get(url, params=params, timeout=cfg.timeout_seconds)
        if not resp.ok:
            raise RuntimeError(f"OSRM sender request failed {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        dists = np.asarray(data["distances"][0], dtype=float)
        durs = np.asarray(data["durations"][0], dtype=float)

        dist_row[i_start:i_end] = dists
        dur_row[i_start:i_end] = durs

        out.loc[out.index[i_start:i_end], out_real_col] = dists
        out.loc[out.index[i_start:i_end], out_duration_col] = durs

        time.sleep(cfg.rate_limit_seconds)

    # Save optional "row matrices"
    if save_distances_path:
        p = Path(save_distances_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([dist_row], index=["Absender"], columns=out.index).to_csv(p, sep=",", decimal=".", index=True)

    if save_durations_path:
        p = Path(save_durations_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([dur_row], index=["Absender"], columns=out.index).to_csv(p, sep=",", decimal=".", index=True)

    return out


def calculate_sender_to_recipients_euclidean(
    df: pd.DataFrame,
    sender_lon: float,
    sender_lat: float,
    *,
    rec_lon_col: str = "Recipient_Longitude",
    rec_lat_col: str = "Recipient_Latitude",
    out_col: str = "Euc_Distance",
    save_path: Optional[str | Path] = None,
) -> pd.DataFrame:
    """
    Adds Euc_Distance column (haversine km) from sender to each recipient.
    No external 'haversine' dependency.
    """
    out = df.copy()

    out[rec_lat_col] = out[rec_lat_col].astype(float)
    out[rec_lon_col] = out[rec_lon_col].astype(float)

    out[out_col] = out.apply(
        lambda r: haversine_km(float(sender_lat), float(sender_lon), float(r[rec_lat_col]), float(r[rec_lon_col])),
        axis=1,
    )

    if save_path:
        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        out[[out_col]].to_csv(p, sep=",", decimal=".", index=True)

    return out



# -----------------------------------------------------------------------------
# High-level convenience function (like your create_distance_matrices)
# -----------------------------------------------------------------------------

def create_distance_matrices(
    df_shipments_with_coords: pd.DataFrame,
    coordinate_list: List[Dict[str, Any]],
    sender_lon: float,
    sender_lat: float,
    *,
    cfg: OSRMConfig = OSRMConfig(),
    save_distances_C: Optional[str | Path] = None,
    save_durations_C: Optional[str | Path] = None,
    save_euclidean_C: Optional[str | Path] = None,
    save_matrix_table: Optional[str | Path] = None,
    save_distances_S: Optional[str | Path] = None,
    save_durations_S: Optional[str | Path] = None,
    save_euclidean_S: Optional[str | Path] = None,
    save_df_with_distances: Optional[str | Path] = None,
    symmetrize_osrm: bool = False,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    End-to-end helper (keeps your original "one call does it all" workflow).

    Returns:
      distances_RR, durations_RR, euclidean_RR, distance_table, df_with_sender_distances
    """
    # 1) Round/sort coordinates
    sorted_locations = round_sort_coordinates(coordinate_list)

    # 2) OSRM RR matrices
    distances, durations = calculate_distances_durations_osrm(
        sorted_locations,
        cfg=cfg,
        symmetrize=symmetrize_osrm,
        save_distances_path=save_distances_C,
        save_durations_path=save_durations_C,
    )

    # 3) Euclidean (haversine) RR matrix
    euclidean = haversine_distance_matrix_km(sorted_locations)
    if save_euclidean_C:
        p = Path(save_euclidean_C)
        p.parent.mkdir(parents=True, exist_ok=True)
        euclidean.to_csv(p, sep=",", decimal=".", index=True)

    # 4) Combined table (upper triangle)
    distance_table = create_matrix_table(
        euclidean=euclidean,
        distances=distances,
        durations=durations,
        save_path=save_matrix_table,
    )

    # 5) Sender->recipient real distance + duration
    df_with_real = calculate_sender_to_recipients_osrm(
        df=df_shipments_with_coords,
        sender_lon=sender_lon,
        sender_lat=sender_lat,
        cfg=cfg,
        save_distances_path=save_distances_S,
        save_durations_path=save_durations_S,
    )

    # 6) Sender->recipient euclidean distance
    df_with_all = calculate_sender_to_recipients_euclidean(
        df=df_with_real,
        sender_lon=sender_lon,
        sender_lat=sender_lat,
        save_path=save_euclidean_S,
    )

    if save_df_with_distances:
        p = Path(save_df_with_distances)
        p.parent.mkdir(parents=True, exist_ok=True)
        df_with_all.to_csv(p, sep=";", encoding="latin1", decimal=".", index=False)

    return distances, durations, euclidean, distance_table, df_with_all

EARTH_RADIUS_KM = 6371.0088

