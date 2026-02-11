from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from delivery_profiles.config import load_config
from delivery_profiles.pipeline import run_pipeline_from_config


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run delivery pattern optimization pipeline")
    p.add_argument("--config", default="config/default.yaml", help="Path to YAML config")
    p.add_argument("--shipments", required=True, help="Path to shipments CSV")
    p.add_argument("--tariff", required=False, help="Path to tariff matrix CSV (required if tariff_type=matrix)")
    p.add_argument("--sender-lon", required=True, type=float, help="Sender longitude")
    p.add_argument("--sender-lat", required=True, type=float, help="Sender latitude")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)

    shipments_path = Path(args.shipments)
    if not shipments_path.exists():
        raise FileNotFoundError(f"Shipments file not found: {shipments_path}")

    shipments = pd.read_csv(shipments_path, sep=";", encoding="latin1")

    tariff_matrix = None
    if args.tariff:
        tariff_path = Path(args.tariff)
        if not tariff_path.exists():
            raise FileNotFoundError(f"Tariff file not found: {tariff_path}")
        tariff_matrix = pd.read_csv(tariff_path, sep=";", encoding="latin1")

    results = run_pipeline_from_config(
        shipments,
        tariff_matrix=tariff_matrix,
        sender_lon=args.sender_lon,
        sender_lat=args.sender_lat,
        cfg=cfg,
    )

    # scripts/run_pipeline.py  (only the part after calling run_pipeline_from_config)

    out_dir = Path(results["out_dir"])  # pipeline returns this now
    out_dir.mkdir(parents=True, exist_ok=True)

    # always write non-clustered profiles
    profiles_nc = results.get("profiles_nonclustered")
    if profiles_nc is not None and not profiles_nc.empty:
        profiles_nc.to_csv(out_dir / "profiles_nonclustered.csv", sep=";", encoding="latin1", decimal=".", index=False)

    # write clustered if enabled & produced
    profiles_c = results.get("profiles_clustered")
    if profiles_c is not None and not profiles_c.empty:
        profiles_c.to_csv(out_dir / "profiles_clustered.csv", sep=";", encoding="latin1", decimal=".", index=False)

    print("Done. Outputs written to:", out_dir)

if __name__ == "__main__":
    main()