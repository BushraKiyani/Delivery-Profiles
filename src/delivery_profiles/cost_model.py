from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Sequence, Any

import pandas as pd


# ============================================================================
# 1) Tariff / Cost Model
# ============================================================================

TariffType = Literal["matrix", "base_plus_ton"]


@dataclass(frozen=True)
class CostModelConfig:
    """
    tariff_type:
      - "matrix": use a tariff matrix (weight bins x distance bins) with stepwise pricing
      - "base_plus_ton": base_price + weight_kg * (price_per_ton / 1000)

    base_price and price_per_ton are only used when tariff_type == "base_plus_ton".
    """
    tariff_type: TariffType = "matrix"
    base_price: float = 0.0
    price_per_ton: float = 0.0


def transform_tariff_matrix_wide_to_long(
    df_tariff_wide: pd.DataFrame,
    weight_col: str = "Weight_kg",
) -> pd.DataFrame:
    """
    Convert a wide tariff matrix into long format.

    Expected wide format:
      - one column weight_col (e.g., "Weight_kg")
      - remaining columns are distance bin thresholds (e.g., "0", "50", "100", ...)

    Returns long format with columns:
      - weight_col
      - "Euc_Distance"
      - "Kosten"
    """
    if weight_col not in df_tariff_wide.columns:
        raise ValueError(f"Tariff wide matrix must contain '{weight_col}' column.")

    df_long = pd.melt(
        df_tariff_wide,
        id_vars=weight_col,
        value_vars=[c for c in df_tariff_wide.columns if c != weight_col],
        var_name="Euc_Distance",
        value_name="Kosten",
    )

    df_long[weight_col] = pd.to_numeric(df_long[weight_col], errors="coerce")
    df_long["Euc_Distance"] = pd.to_numeric(df_long["Euc_Distance"], errors="coerce")
    df_long["Kosten"] = pd.to_numeric(df_long["Kosten"], errors="coerce")

    df_long = df_long.dropna(subset=[weight_col, "Euc_Distance", "Kosten"])
    return df_long.sort_values([weight_col, "Euc_Distance"]).reset_index(drop=True)


def compute_freight_cost(
    df_tariff_long: pd.DataFrame,
    weight_kg: float,
    distance_value: float,
    config: CostModelConfig,
    weight_col: str = "Weight_kg",
    distance_col_long: str = "Euc_Distance",
    cost_col_long: str = "Kosten",
) -> float:
    """
    Compute freight cost for a single shipment based on either:
      - tariff matrix (stepwise)
      - base + tonnage

    For "matrix":
      chooses the last row where:
        tariff_long[distance_col_long] <= distance_value
        tariff_long[weight_col] <= weight_kg
      then returns that row's cost_col_long.
    """
    if config.tariff_type == "base_plus_ton":
        return float(config.base_price + (weight_kg * config.price_per_ton / 1000.0))

    required = {weight_col, distance_col_long, cost_col_long}
    missing = required - set(df_tariff_long.columns)
    if missing:
        raise ValueError(f"Tariff long matrix missing required columns: {sorted(missing)}")

    filt = df_tariff_long[
        (df_tariff_long[distance_col_long] <= float(distance_value))
        & (df_tariff_long[weight_col] <= float(weight_kg))
    ]

    if filt.empty:
        # fallback to smallest bin if nothing matches
        fallback = df_tariff_long.sort_values([weight_col, distance_col_long]).iloc[0]
        return float(fallback[cost_col_long])

    return float(filt.iloc[-1][cost_col_long])


def add_freight_costs(
    df_shipments: pd.DataFrame,
    *,
    df_tariff_wide: Optional[pd.DataFrame] = None,
    df_tariff_long: Optional[pd.DataFrame] = None,
    config: CostModelConfig = CostModelConfig(),
    out_col: str = "Freight_Cost",
    weight_col_shipments: str = "Weight",
    distance_col_shipments: str = "Euc_Distance",
    # Tariff matrix column names (long format)
    weight_col_tariff: str = "Weight_kg",
    distance_col_tariff_long: str = "Euc_Distance",
    cost_col_tariff_long: str = "Kosten",
) -> pd.DataFrame:
    """
    Add freight cost column to shipments.

    Provide either:
      - df_tariff_wide (wide tariff matrix) OR
      - df_tariff_long (already long format)
    """
    if config.tariff_type == "matrix":
        if df_tariff_long is None and df_tariff_wide is None:
            raise ValueError("For tariff_type='matrix', provide df_tariff_wide or df_tariff_long.")
        if df_tariff_long is None:
            df_tariff_long = transform_tariff_matrix_wide_to_long(
                df_tariff_wide, weight_col=weight_col_tariff
            )
    else:
        df_tariff_long = df_tariff_long if df_tariff_long is not None else pd.DataFrame()

    df = df_shipments.copy()
    df[weight_col_shipments] = pd.to_numeric(df[weight_col_shipments], errors="coerce")
    df[distance_col_shipments] = pd.to_numeric(df[distance_col_shipments], errors="coerce")

    def _row_cost(row: pd.Series) -> float:
        w = float(row[weight_col_shipments])
        d = float(row[distance_col_shipments])
        return compute_freight_cost(
            df_tariff_long=df_tariff_long,
            weight_kg=w,
            distance_value=d,
            config=config,
            weight_col=weight_col_tariff,
            distance_col_long=distance_col_tariff_long,
            cost_col_long=cost_col_tariff_long,
        )

    df[out_col] = df.apply(_row_cost, axis=1)
    return df


# ============================================================================
# 2) Add distance from matrix (old d_add_Distanz_Frachtkosten.py piece)
# ============================================================================

def add_distance_from_matrix(
    df_shipments: pd.DataFrame,
    dist_matrix: pd.DataFrame,
    *,
    recipient_col: str = "Recipient_ID",
    origin_col: str = "Stadt_Absender",
    out_col: str = "Euc_Distance",
) -> pd.DataFrame:
    """
    Add a distance column to df_shipments by looking up values in dist_matrix
    using [recipient, origin] keys.

    dist_matrix is expected like:
      - rows indexed by recipient IDs
      - columns named by origin (e.g., city/depot)
    """
    df = df_shipments.copy()
    distances = []

    for _, row in df.iterrows():
        r = row[recipient_col]
        o = row[origin_col]
        try:
            distances.append(dist_matrix.loc[r, o])
        except KeyError:
            distances.append(dist_matrix.loc[str(r), o])

    df[out_col] = pd.to_numeric(distances, errors="coerce")
    return df


# ============================================================================
# 3) Profile consolidation + delay (merged from b_calc_costs.py)
# ============================================================================

# Pattern library (Mon..Fri)
PAT: dict[int, list[list[int]]] = {
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


def calc_avg_delay(df_send: pd.DataFrame, shippingdate: pd.Timestamp, loading_date_col: str = "Loading_Date") -> float:
    """
    Average delay in days between shippingdate and the original loading dates.
    Expects df_send[loading_date_col] to be datetime.
    """
    if df_send.empty:
        return 0.0
    deltas = (shippingdate - df_send[loading_date_col]).dt.days
    return float(deltas.mean())


def build_weekday_calendar(
    df: pd.DataFrame,
    date_column: str,
    *,
    include_weekends: bool = False,
) -> pd.DataFrame:
    """
    Build a calendar dataframe indexed by date, with weekday column.

    Matches your b_calc_costs.py logic:
      start = min(date) - 1 week
      end   = max(date) + 1 week
      drop weekends unless include_weekends=True
    """
    df2 = df.copy()
    df2.loc[:, date_column] = pd.to_datetime(df2[date_column])

    start = df2[date_column].min() - pd.DateOffset(weeks=1)
    end = df2[date_column].max() + pd.DateOffset(weeks=1)

    all_days = pd.date_range(start=start, end=end, freq="D")
    df_dates = pd.DataFrame({"Datum": all_days})
    df_dates["Weekday"] = df_dates["Datum"].dt.dayofweek

    if not include_weekends:
        df_dates = df_dates.loc[~df_dates["Weekday"].isin([5, 6])]

    df_dates = df_dates.set_index("Datum", drop=False)
    return df_dates


def consolidate_shipments_by_profile(
    df_shipments: pd.DataFrame,
    df_profile: pd.DataFrame,
    *,
    recipient_col: str = "Recipient_ID",
    shipment_id_col: str = "Shipment_ID",
    loading_date_col: str = "Loading_Date",
    weight_col: str = "Weight",
    distance_col: str = "Euc_Distance",
    freight_cost_col: str = "Freight_Cost",
    max_truck_weight: float = 25000.0,
    exclude_weekdays: Sequence[int] = (5, 6),
    profile_frequency_col: str = "Frequency",
    profile_pattern_col: str = "Pattern",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    This is the cleaned core of b_calc_costs.profile_application().

    It:
    - keeps shipments not in profile OR on excluded weekdays (Sat/Sun) unchanged
    - groups remaining shipments for each Recipient_ID according to assigned (Frequency, Pattern)
    - walks backwards through a calendar and "ships" accumulated loads on pattern days
    - outputs:
        df_result_pattern: consolidated rows (one row per planned shipment date)
        df_shipments_not_filter: untouched rows
        df_result: concatenation (consolidated + untouched)
    """
    df_prof = df_profile.copy()
    df_ship = df_shipments.copy()

    df_prof[recipient_col] = df_prof[recipient_col].astype(int)
    df_prof = df_prof.set_index(recipient_col, drop=False)

    df_ship[recipient_col] = df_ship[recipient_col].astype(int)
    df_ship[loading_date_col] = pd.to_datetime(df_ship[loading_date_col])
    df_ship["Weekday"] = df_ship[loading_date_col].dt.dayofweek
    df_ship = df_ship.set_index(recipient_col, drop=False)

    # shipments not filtered: either recipient not in profile OR excluded weekday
    prof_ids = set(df_prof[recipient_col].values.tolist())
    df_shipments_not_filter = df_ship.loc[
        (~df_ship[recipient_col].isin(prof_ids))
        | (df_ship[recipient_col].isin(prof_ids) & (df_ship["Weekday"].isin(exclude_weekdays)))
    ].copy()

    df_shipments_not_filter = df_shipments_not_filter[
        [recipient_col, shipment_id_col, loading_date_col, weight_col, distance_col, freight_cost_col, "Weekday"]
    ]

    # shipments to consolidate
    df_shipments_profile = df_ship.loc[
        df_ship[recipient_col].isin(prof_ids) & (~df_ship["Weekday"].isin(exclude_weekdays))
    ].copy()

    df_dates = build_weekday_calendar(df_shipments_profile.reset_index(drop=True), loading_date_col, include_weekends=False)

    data_result_pattern: list[list[Any]] = []

    # Consolidate per recipient
    for rid in df_shipments_profile[recipient_col].unique():
        df_r = df_shipments_profile.loc[df_shipments_profile[recipient_col] == rid].copy()

        freq = int(df_prof.loc[rid, profile_frequency_col])
        pat_idx = int(df_prof.loc[rid, profile_pattern_col])
        if freq not in PAT:
            raise ValueError(f"Frequency={freq} not found in PAT library.")
        if pat_idx < 0 or pat_idx >= len(PAT[freq]):
            raise ValueError(f"Pattern index {pat_idx} out of range for frequency={freq}.")

        pattern = PAT[freq][pat_idx]  # length 5 (Mon..Fri)

        buffer_df = pd.DataFrame(columns=df_r.columns)

        # walk backwards (latest -> earliest), like your original code
        for _, cal_row in df_dates.iloc[::-1].iterrows():
            weekday = int(cal_row["Weekday"])  # 0..4
            ship_day = pd.Timestamp(cal_row["Datum"])

            state = int(pattern[weekday])  # 0/1

            # append shipments that originally happened that day
            todays = df_r.loc[df_r[loading_date_col] == ship_day]
            if not todays.empty:
                buffer_df = pd.concat([buffer_df, todays], ignore_index=True)

            # if pattern ships today and we have something in buffer and within max weight -> ship it
            if state == 1 and not buffer_df.empty and float(buffer_df[weight_col].sum()) <= float(max_truck_weight):
                avg_delay = calc_avg_delay(buffer_df, ship_day, loading_date_col=loading_date_col)

                data_result_pattern.append(
                    [
                        int(rid),
                        [int(x) for x in buffer_df[shipment_id_col].tolist()],
                        ship_day,
                        float(buffer_df[weight_col].sum()),
                        float(buffer_df[distance_col].iloc[0]),  # keep first distance (same recipient)
                        int(weekday),
                        float(avg_delay),
                    ]
                )
                buffer_df = pd.DataFrame(columns=df_r.columns)

    df_result_pattern = pd.DataFrame(
        data_result_pattern,
        columns=[recipient_col, shipment_id_col, loading_date_col, weight_col, distance_col, "Weekday", "Delay"],
    )

    # Combine results
    df_result = pd.concat([df_result_pattern, df_shipments_not_filter.reset_index(drop=True)], ignore_index=True)

    return df_result_pattern, df_shipments_not_filter.reset_index(drop=True), df_result


# ============================================================================
# 4) Backwards-compatible wrappers (optional)
# ============================================================================

def transform_tarifmatrix(df_tarifmatrix_wide: pd.DataFrame) -> pd.DataFrame:
    """Alias to ease migration from old code."""
    return transform_tariff_matrix_wide_to_long(df_tarifmatrix_wide, weight_col="Weight_kg")


def Freight_Cost_berechnen(
    df_tarifmatrix_long: pd.DataFrame,
    Weight: float,
    distanz: float,
    tariff_type: str,
    price_basis: float,
    price_per_ton: float,
) -> float:
    """Alias to ease migration from old code."""
    cfg = (
        CostModelConfig(tariff_type="matrix")
        if tariff_type == "matrix"
        else CostModelConfig(tariff_type="base_plus_ton", base_price=price_basis, price_per_ton=price_per_ton)
    )
    return compute_freight_cost(
        df_tariff_long=df_tarifmatrix_long,
        weight_kg=Weight,
        distance_value=distanz,
        config=cfg,
        weight_col="Weight_kg",
        distance_col_long="Euc_Distance",
        cost_col_long="Kosten",
    )


def add_cost(
    df_touren_distanzen: pd.DataFrame,
    transport_preis: pd.DataFrame,
    df_freightcost_path: str,
    columnname: str,
    tariff_type: str,
    price_basis: float,
    price_per_ton: float,
) -> pd.DataFrame:
    """
    Backward-compatible wrapper for your old add_cost().
    No file writing here (do it in scripts).
    """
    cfg = (
        CostModelConfig(tariff_type="matrix")
        if tariff_type == "matrix"
        else CostModelConfig(tariff_type="base_plus_ton", base_price=price_basis, price_per_ton=price_per_ton)
    )

    df_out = add_freight_costs(
        df_shipments=df_touren_distanzen,
        df_tariff_wide=transport_preis,
        config=cfg,
        out_col=columnname,
        weight_col_shipments="Weight",
        distance_col_shipments="Euc_Distance",
        weight_col_tariff="Weight_kg",
        distance_col_tariff_long="Euc_Distance",
        cost_col_tariff_long="Kosten",
    )

    # keep your print line for continuity
    print(f"Freight costs have been added and file is saved in: {df_freightcost_path}")
    return df_out


def add_distance(df_touren_koordinaten: pd.DataFrame, dist_matrix: pd.DataFrame, columnname: str) -> pd.DataFrame:
    """Backward-compatible wrapper for add_distance()."""
    return add_distance_from_matrix(
        df_shipments=df_touren_koordinaten,
        dist_matrix=dist_matrix,
        recipient_col="Recipient_ID",
        origin_col="Stadt_Absender",
        out_col=columnname,
    )
