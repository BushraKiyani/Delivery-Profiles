# src/delivery_profiles/config.py

from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass
class ProjectConfig:
    raw_data: Path
    processed_data: Path
    outputs: Path
    coordinate_cache: Path


def load_config(path: str = "config/default.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def build_paths(cfg: dict) -> ProjectConfig:
    return ProjectConfig(
        raw_data=Path(cfg["paths"]["data"]["raw"]),
        processed_data=Path(cfg["paths"]["data"]["processed"]),
        outputs=Path(cfg["paths"]["data"]["outputs"]),
        coordinate_cache=Path(cfg["paths"]["cache"]["coordinates"]),
    )
