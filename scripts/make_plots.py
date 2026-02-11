from pathlib import Path
import pandas as pd
from delivery_profiles.weekday_plots import write_weekday_plots_pdf

run_dir = Path("outputs/runs/minF2_varW1.33_varF1.33")

# parse run_dir name -> suffix
parts = run_dir.name.split("_")
min_frequency = parts[0].replace("minF", "")
var_weight = parts[1].replace("varW", "")
var_frequency = parts[2].replace("varF", "")

suffix = f"vw{var_weight}_vf{var_frequency}_mf{min_frequency}"

plots_dir = run_dir / "plots"
plots_dir.mkdir(parents=True, exist_ok=True)

# 1) demand plot input (profile assignment result)
df_demand = pd.read_csv(run_dir / "profile_assignment.csv", sep=";", encoding="latin1")

# 2) shipment-level outputs (pattern-only / unchanged / combined)
df_pattern_only = pd.read_csv(run_dir / f"shipments_after_profiles_pattern_only_{suffix}.csv", sep=";", encoding="latin1")
df_unchanged    = pd.read_csv(run_dir / f"shipments_after_profiles_unchanged_{suffix}.csv", sep=";", encoding="latin1")
df_result       = pd.read_csv(run_dir / f"shipments_after_profiles_{suffix}.csv", sep=";", encoding="latin1")
df_full         = pd.read_csv(run_dir / "shipments_with_costs.csv", sep=";", encoding="latin1")

write_weekday_plots_pdf(
    df_demand=df_demand,
    df_profile=df_pattern_only,
    df_notprofile=df_unchanged,
    df_result=df_result,
    df_full=df_full,
    out_pdf=plots_dir / f"weekday_plots_{suffix}.pdf",
    run_name=run_dir.name,
    clustered="Non-Clustered",
)

print("Saved:", plots_dir / f"weekday_plots_{suffix}.pdf")