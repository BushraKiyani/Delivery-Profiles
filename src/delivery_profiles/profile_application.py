from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple

import pandas as pd
from .pattern_assignment import PAT


def _chunk_buffer(
    buffer_df: pd.DataFrame,
    max_weight: float,
    weight_col: str,
) -> List[pd.DataFrame]:
    """
    Greedy first-fit split of a buffer into weight-bounded truck loads.

    Rows are packed in order; a new chunk is started whenever adding the next
    row would exceed max_weight.  A single row heavier than max_weight on its
    own still forms its own (oversized) chunk — it cannot be split further.
    """
    chunks: List[pd.DataFrame] = []
    current_rows: List[Any] = []
    current_w = 0.0

    for _, row in buffer_df.iterrows():
        row_w = float(row[weight_col])
        if current_w + row_w > max_weight and current_rows:
            chunks.append(pd.DataFrame(current_rows))
            current_rows = [row]
            current_w = row_w
        else:
            current_rows.append(row)
            current_w += row_w

    if current_rows:
        chunks.append(pd.DataFrame(current_rows))

    return chunks


@dataclass(frozen=True)
class ProfileApplicationConfig:
    recipient_col: str = "Recipient_ID"
    shipment_id_col: str = "Shipment_ID"
    loading_date_col: str = "Loading_Date"
    weekday_col: str = "Weekday"

    weight_col: str = "Weight"
    distance_col: str = "Euc_Distance"
    freight_cost_col: str = "Freight_Cost"

    profile_freq_col: str = "Frequency"
    profile_pattern_col: str = "Pattern"  # pattern index (0..)

    max_truck_weight: float = 25000.0
    exclude_weekdays: Sequence[int] = (5, 6)  # Sat/Sun


def _build_weekday_calendar(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    df2 = df.copy()
    df2[date_col] = pd.to_datetime(df2[date_col])

    start = df2[date_col].min() - pd.DateOffset(weeks=1)
    end = df2[date_col].max() + pd.DateOffset(weeks=1)

    cal = pd.DataFrame({"Datum": pd.date_range(start=start, end=end, freq="D")})
    cal["Weekday"] = cal["Datum"].dt.dayofweek
    cal = cal.loc[~cal["Weekday"].isin([5, 6])].reset_index(drop=True)  # Mon..Fri
    return cal


def apply_profiles_to_shipments(
    df_shipments: pd.DataFrame,
    profiles: pd.DataFrame,
    cfg: ProfileApplicationConfig = ProfileApplicationConfig(),
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Applies assigned profiles to shipments and returns:
      - pattern_only: consolidated shipments (new ship dates) for profiled recipients (Mon..Fri only)
      - unchanged: shipments not affected (non-profile recipients + weekend shipments)
      - full_after: pattern_only + unchanged
    """
    df = df_shipments.copy()
    prof = profiles.copy()

    # Basic validation
    needed_ship = {cfg.recipient_col, cfg.shipment_id_col, cfg.loading_date_col, cfg.weight_col, cfg.distance_col, cfg.freight_cost_col}
    missing_ship = needed_ship - set(df.columns)
    if missing_ship:
        raise ValueError(f"Shipments missing required columns: {sorted(missing_ship)}")

    needed_prof = {cfg.recipient_col, cfg.profile_freq_col, cfg.profile_pattern_col}
    missing_prof = needed_prof - set(prof.columns)
    if missing_prof:
        raise ValueError(f"Profiles missing required columns: {sorted(missing_prof)}")

    # Types
    df[cfg.loading_date_col] = pd.to_datetime(df[cfg.loading_date_col], errors="coerce")
    df[cfg.recipient_col] = pd.to_numeric(df[cfg.recipient_col], errors="coerce").astype("Int64")
    prof[cfg.recipient_col] = pd.to_numeric(prof[cfg.recipient_col], errors="coerce").astype("Int64")

    df[cfg.weight_col] = pd.to_numeric(df[cfg.weight_col], errors="coerce").fillna(0.0)
    df[cfg.distance_col] = pd.to_numeric(df[cfg.distance_col], errors="coerce")
    df[cfg.freight_cost_col] = pd.to_numeric(df[cfg.freight_cost_col], errors="coerce").fillna(0.0)

    # Weekday
    if cfg.weekday_col not in df.columns:
        df[cfg.weekday_col] = df[cfg.loading_date_col].dt.dayofweek

    # IDs to profile
    prof_ids = set(prof[cfg.recipient_col].dropna().astype(int).tolist())
    prof = prof.set_index(cfg.recipient_col, drop=False)

    # unchanged shipments:
    unchanged = df[
        (~df[cfg.recipient_col].isin(prof_ids))
        | (df[cfg.recipient_col].isin(prof_ids) & df[cfg.weekday_col].isin(cfg.exclude_weekdays))
    ].copy()

    # eligible shipments to consolidate:
    eligible = df[
        df[cfg.recipient_col].isin(prof_ids)
        & (~df[cfg.weekday_col].isin(cfg.exclude_weekdays))
    ].copy()

    if eligible.empty:
        full_after = unchanged.reset_index(drop=True)
        return eligible.iloc[0:0].copy(), unchanged.reset_index(drop=True), full_after

    cal = _build_weekday_calendar(eligible, cfg.loading_date_col)

    out_rows: List[Dict[str, Any]] = []

    # For each recipient: walk backwards and ship on pattern days
    for rid in eligible[cfg.recipient_col].dropna().astype(int).unique():
        df_r = eligible[eligible[cfg.recipient_col].astype(int) == rid].copy()
        df_r = df_r.sort_values(cfg.loading_date_col)

        freq = int(prof.loc[rid, cfg.profile_freq_col])
        pat_idx = int(prof.loc[rid, cfg.profile_pattern_col])

        if freq not in PAT:
            raise ValueError(f"Recipient {rid}: Frequency={freq} not supported. Allowed: {sorted(PAT.keys())}")
        if pat_idx < 0 or pat_idx >= len(PAT[freq]):
            raise ValueError(f"Recipient {rid}: Pattern index {pat_idx} out of range for Frequency={freq}")

        pattern = PAT[freq][pat_idx]  # Mon..Fri (len=5)
        buffer_df = pd.DataFrame(columns=df_r.columns)
        _split_days = 0
        _total_trucks = 0

        for _, crow in cal.iloc[::-1].iterrows():
            ship_day = pd.Timestamp(crow["Datum"])
            weekday = int(crow["Weekday"])  # 0..4
            state = int(pattern[weekday])

            todays = df_r[df_r[cfg.loading_date_col] == ship_day]
            if not todays.empty:
                buffer_df = pd.concat([buffer_df, todays], ignore_index=True)

            if state == 1 and not buffer_df.empty:
                total_w = float(buffer_df[cfg.weight_col].sum())

                if total_w <= cfg.max_truck_weight:
                    avg_delay = float(
                        (pd.Timestamp(ship_day) - pd.to_datetime(buffer_df[cfg.loading_date_col])).dt.days.mean()
                    )
                    out_rows.append(
                        {
                            cfg.recipient_col: rid,
                            cfg.shipment_id_col: buffer_df[cfg.shipment_id_col].tolist(),
                            cfg.loading_date_col: ship_day,
                            cfg.weekday_col: weekday,
                            cfg.weight_col: total_w,
                            cfg.distance_col: float(buffer_df[cfg.distance_col].iloc[0]),
                            cfg.freight_cost_col: float(buffer_df[cfg.freight_cost_col].sum()),
                            "Delay": avg_delay,
                            "Frequency": freq,
                            "Pattern": pat_idx,
                            "Pattern_clear": pattern,
                            "Truck_Number": 1,
                        }
                    )
                    buffer_df = pd.DataFrame(columns=df_r.columns)
                else:
                    # Buffer exceeds one truck — split into max_truck_weight chunks
                    chunks = _chunk_buffer(buffer_df, cfg.max_truck_weight, cfg.weight_col)
                    for truck_num, chunk in enumerate(chunks, start=1):
                        avg_delay = float(
                            (pd.Timestamp(ship_day) - pd.to_datetime(chunk[cfg.loading_date_col])).dt.days.mean()
                        )
                        out_rows.append(
                            {
                                cfg.recipient_col: rid,
                                cfg.shipment_id_col: chunk[cfg.shipment_id_col].tolist(),
                                cfg.loading_date_col: ship_day,
                                cfg.weekday_col: weekday,
                                cfg.weight_col: float(chunk[cfg.weight_col].sum()),
                                cfg.distance_col: float(chunk[cfg.distance_col].iloc[0]),
                                cfg.freight_cost_col: float(chunk[cfg.freight_cost_col].sum()),
                                "Delay": avg_delay,
                                "Frequency": freq,
                                "Pattern": pat_idx,
                                "Pattern_clear": pattern,
                                "Truck_Number": truck_num,
                            }
                        )
                    _split_days += 1
                    _total_trucks += len(chunks)
                    buffer_df = pd.DataFrame(columns=df_r.columns)

        if _split_days:
            print(
                f"[Profile application] Recipient {rid}:"
                f" split into {_total_trucks} trucks on {_split_days} pattern days."
            )

    pattern_only = pd.DataFrame(out_rows)

    full_after = pd.concat([pattern_only, unchanged], ignore_index=True)

    return pattern_only.reset_index(drop=True), unchanged.reset_index(drop=True), full_after.reset_index(drop=True)
