# Delivery Profiles
Delivery Profiles is a Python pipeline for analyzing shipment behavior and generating delivery patterns that can reduce freight cost volatility while preserving service quality.
The project covers the complete flow from raw shipment records to optimized profile assignments, with optional clustering and map/plot outputs.

## What the pipeline does

At a high level, the pipeline runs these stages:
1. **Preprocessing**
   - Normalizes and renames shipment columns.
   - Cleans recipient addresses (street/city/house number normalization).
   - Handles date and numeric conversions.
     
2. **Geocoding**
   - Geocodes recipient addresses via a configurable Nominatim-compatible endpoint.
   - Uses a local JSON cache to avoid repeated API calls.

3. **Distance matrix**
   - Either computes route-distance/duration matrices via OSRM, or loads precomputed matrices from CSV.

4. **Cost modeling**
   - Adds freight costs using either:
     - a tariff matrix, or
     - a base+tonnage model.

5. **Variability analysis**
   - Determines which recipients are eligible for profile optimization based on frequency and variability thresholds.

6. **Pattern assignment**
   - Assigns weekday delivery patterns (non-clustered).
   - Optionally performs clustered assignment as a second optimization mode.

7. **Profile application**
   - Applies assigned patterns to shipment schedules.
   - Writes pattern-only, unchanged, and combined shipment outputs.

8. **Outputs and visualization**
   - Organizes results in run-specific folders.
   - Optionally generates cluster maps and weekday plot PDFs.

## Repository structure

```text
.
├── config/
│   └── default.yaml           # Main pipeline configuration
├── scripts/
│   ├── run_pipeline.py        # CLI entry point for end-to-end run
│   └── make_plots.py          # Example script to create weekday plot PDF
├── src/delivery_profiles/
│   ├── pipeline.py            # Pipeline orchestration
│   ├── preprocessing.py       # Data cleaning and normalization
│   ├── geo.py                 # Geocoding + coordinate cache
│   ├── distance_matrix.py     # OSRM matrix compute/load helpers
│   ├── cost_model.py          # Freight cost calculations
│   ├── variability.py         # Variability/frequency filtering
│   ├── pattern_assignment.py  # Non-clustered profile assignment
│   ├── clustered_pattern_assignment.py
│   ├── profile_application.py # Apply profiles to shipments
│   ├── maps.py                # Folium HTML map output
│   └── weekday_plots.py       # PDF weekday plot generation
└── pyproject.toml
```

## Requirements

- Python **3.9+**
- `pip` or another Python package manager

Core libraries used by the project include:

- `pandas`, `numpy`
- `requests`, `PyYAML`
- `scikit-learn`
- `ortools`
- `matplotlib`
- `folium`
- `roman`, `textdistance`

> Note: `pyproject.toml` currently defines project metadata but does not list runtime dependencies. Install required packages manually (or add them to your environment manager of choice).

## Installation

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
pip install pandas numpy requests pyyaml scikit-learn ortools matplotlib folium roman textdistance
```

## Configuration

Default configuration is in:

- `config/default.yaml`

Key sections:

- `paths`: raw/processed/output and cache locations
- `run_naming`: controls automatic run folder naming
- `geocoding`: endpoint, timeouts, rate limiting, cache usage
- `distance_matrix`: choose `compute` (OSRM) or `load` (CSV files)
- `cost_model`: tariff mode (`matrix` or `base_plus_ton`)
- `variability`: thresholds for recipient eligibility
- `pattern_assignment`: optimization settings
- `clustering`: toggle and cluster count
- `maps`: map generation settings

## Running the pipeline

Use the CLI script:

```bash
python scripts/run_pipeline.py \
  --config config/default.yaml \
  --shipments path/to/shipments.csv \
  --tariff path/to/tariff_matrix.csv \
  --sender-lon 7.4653 \
  --sender-lat 51.5136
```

### Arguments
- `--config` (optional): path to YAML config (default `config/default.yaml`)
- `--shipments` (required): shipment CSV input
- `--tariff` (optional): tariff matrix CSV (required when `cost_model.tariff_type=matrix`)
- `--sender-lon` / `--sender-lat` (required): depot coordinates

### Input CSV expectations

The preprocessing stage supports several historical column variants and maps them to standardized names (e.g., `Recipient_ID`, `Recipient_Street`, `Recipient_City`, `Weight`, `Loading_Date`).

For best results, ensure shipment data includes:

- recipient identifier and address fields
- loading date
- weight
- sender city (for some distance/cost routines)

## Output layout

When `run_naming.enabled` is true, outputs are written to:

- `outputs/runs/minF{...}_varW{...}_varF{...}/`

Typical artifacts include:

- `preprocessed_shipments.csv`
- `shipments_with_coords.csv`
- distance matrices in `matrices/`
- `shipments_with_costs.csv`
- `profiles_nonclustered.csv`
- `profiles_clustered.csv` (if clustering enabled)
- profile-applied shipment outputs (`pattern_only`, `unchanged`, combined)
- plots and map HTML files

## Generate weekday plots (optional)

The helper script `scripts/make_plots.py` demonstrates how to build a PDF of weekday demand/comparison plots from one run directory.

If you use it, update `run_dir` inside the script to match your target run path before executing.

## Development notes

- Project package: `delivery_profiles`
- Main orchestration entry: `delivery_profiles.pipeline.run_pipeline_from_config`
- Config loader: `delivery_profiles.config.load_config`

## Troubleshooting

- **Geocoding is slow or rate-limited**: increase cache usage and adjust `geocoding.rate_limit_seconds`.
- **No tariff file error**: provide `--tariff` when using matrix pricing.
- **Missing distance files in load mode**: verify `distance_matrix.load.*` paths exist.
- **Map generation issues**: disable maps (`maps.enabled: false`) to isolate pipeline logic.

## License

No license file is currently included in this repository. Add a `LICENSE` file if you plan to distribute this project.


