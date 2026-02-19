# Delivery Profiles
Delivery Profiles is a Python pipeline for analyzing shipment behavior and generating delivery patterns that can reduce freight cost volatility while preserving service quality.
The project covers the complete flow from raw shipment records to optimized profile assignments, with optional clustering and map/plot outputs.

The pipeline supports:
- Geocoding with caching
- Distance matrix computation (OSRM) or loading
- Freight cost modeling
- Variability filtering
- Pattern optimization (OR-Tools)
- Optional geographic clustering
- Profile application to shipment schedules
- Map and plot visualization

## High-Level Workflow
The pipeline runs the following stages:

### 1. Preprocessing
- Column normalization
- Address cleaning
- Date & numeric conversions
- Standardized schema output

### 2. Geocoding
- Uses a Nominatim-compatible endpoint
- Stores coordinates in a JSON cache
- Avoids repeated API calls

### 3. Distance Matrix

Two modes:
- **compute** → OSRM route matrix calculation
- **load** → load precomputed CSV matrices

Also computes Euclidean (Haversine) distances.

### 4. Cost Modeling

Adds freight cost via:
- Tariff matrix lookup
- Base + tonnage model

### 5. Variability Analysis

Filters recipients by:
- Minimum shipment frequency
- Weight variability threshold
- Frequency variability threshold

### 6. Pattern Assignment

- Non-clustered optimization (always runs)
- Optional clustered optimization (KMeans + shared patterns)
- Uses OR-Tools internally (knapsack-style demand smoothing)

### 7. Profile Application

- Applies optimized weekday patterns
- Produces:
  - pattern-only shipments
  - unchanged shipments
  - combined shipment dataset

### 8. Post-Cost Recalculation (Optional)

Recomputes freight costs after profile application.

### 9. Maps & Visualization (Optional)

- Cluster map (Folium HTML)
- Weekday demand comparison plots (PDF)

---

## Repository Structure

```text
.
├── config/
│   └── default.yaml
├── scripts/
│   ├── run_pipeline.py
│   └── make_plots.py
├── src/delivery_profiles/
│   ├── pipeline.py
│   ├── preprocessing.py
│   ├── geo.py
│   ├── distance_matrix.py
│   ├── cost_model.py
│   ├── variability.py
│   ├── pattern_assignment.py
│   ├── clustered_pattern_assignment.py
│   ├── profile_application.py
│   ├── maps.py
│   └── weekday_plots.py
├── pyproject.toml
└── README.md
```

## Requirements

- Python 3.9+
- pip / venv

Core dependencies:

- pandas
- numpy
- scikit-learn
- ortools
- requests
- PyYAML
- matplotlib
- folium

Install manually:

```bash
pip install pandas numpy scikit-learn ortools requests pyyaml matplotlib folium
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -e .
pip install pandas numpy scikit-learn ortools requests pyyaml matplotlib folium
```

## Configuration

Main config file:
- `config/default.yaml`
  
Important sections:

### `paths`
Defines raw data, output, and cache locations.

### `run_naming`
Automatically creates run-specific output folders.
Example:
`outputs/runs/minF2_varW0.75_varF0.75/`

### `geocoding`
- endpoint
- rate limit
- timeout
- cache usage

### `distance_matrix`
- `mode: compute | load`
- OSRM settings (if compute)
- CSV paths (if load)

### `cost_model`
- `tariff_type: matrix | base_plus_ton`
If `tariff_type = base_plus_ton`, freight cost is calculated as:
Freight Cost = Base Price + (Weight in tons × Price per ton)

### `variability`
- `min_frequency`
- `var_weight_max`
- `var_frequency_max`

### `pattern_assignment`
- optimization days
- time limit
- rounding border

### `clustering`
- `enabled: true | false`
- number of clusters

### `maps`
- `enabled: true | false`
- `provider: osm | google_roadmap | google_satellite`

## Running the Pipeline

From project root:

```bash
python scripts/run_pipeline.py \
  --config config/default.yaml \
  --shipments data/raw/shipments.csv \
  --tariff data/raw/tariff_matrix.csv \
  --sender-lon 7.4653 \
  --sender-lat 51.5136
```

### Required Arguments

- `--shipments`
- `--sender-lon`
- `--sender-lat`

Required if `tariff_type = matrix`:

- `--tariff`

## Output Structure

When `run_naming` is enabled:

```text
outputs/
└── runs/
    └── minF2_varW0.75_varF0.75/
        ├── shipments_with_coords.csv
        ├── shipments_with_distances.csv
        ├── shipments_with_costs.csv
        ├── variability.csv
        ├── profile_assignment.csv
        ├── profile_assignment_clustered.csv
        ├── shipments_after_profiles_*.csv
        ├── matrices/
        ├── plots/
        └── maps/
```

Each threshold configuration produces a separate run folder.

No outputs are overwritten.

## Maps

Cluster maps are generated as:

`outputs/runs/<run_id>/maps/cluster_map_*.html`

They are interactive Folium maps.

Supports:

- OpenStreetMap
- Google roadmap (if configured)
- Google satellite (if configured)

## Generate Weekday Plot PDF

Use:

```bash
python scripts/make_plots.py
```

Update `run_dir` inside the script to match your run folder.

## GitHub Note

The repository intentionally does not include data or output folders.
## License

No license.


