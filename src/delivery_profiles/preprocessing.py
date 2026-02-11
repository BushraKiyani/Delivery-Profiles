from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

try:
    import roman
except Exception:  # pragma: no cover
    roman = None  # type: ignore

try:
    import textdistance as td
except Exception:  # pragma: no cover
    td = None  # type: ignore


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class PreprocessConfig:
    """
    If you have private correction lists, pass them via paths.
    For a public repo, keep them None and the pipeline still runs.
    """
    address_correction_csv: Optional[str] = None          # e.g. Adressenkorrektur.csv
    id_split_csv: Optional[str] = None                    # e.g. ID_split_Namen.csv

    write_preprocessed_csv: bool = False
    preprocessed_csv_path: Optional[str] = None           # where to write if enabled


# -----------------------------------------------------------------------------
# Column renaming (your mapping)
# -----------------------------------------------------------------------------

COLUMN_RENAME_MAP = {
    "ERP - Transport": "Transport",
    "Abf.datum": "Loading_Date",
    "Fahrzeug ID": "Fahrzeugart",
    "Nutzlast": "Fahrzeugkapazität",
    "Abs. Name": "Name_Absender",
    "Abs. Straße": "Sender_Street",
    "Abs Lnd.": "Land_Absender",
    "Abs. Plz": "Sender_Postal_Code",
    "Abs. Ort": "Stadt_Absender",
    "Empf.-ID": "Recipient_ID",
    "Empf. Name": "Name_Empfänger",
    "Empf. Straße": "Recipient_Street",
    "Empf. Lnd": "Land_Empfänger",
    "Empf. Plz": "Recipient_Postal_Code",
    "Empf. Ort": "Recipient_City",
    "Anz. Lief.": "Anzahl_Lieferungen",
    "HU - Weight": "Weight",
    "Distanz Abschnitt": "Distanz",
    "Freight_Cost": "Freight_Cost",
    # recipient
    "ID_Empfï¿½nger": "Recipient_ID",
    "Straï¿½e_Empfï¿½nger": "Recipient_Street",
    "PLZ_Empfï¿½nger": "Recipient_Postal_Code",
    "Stadt_Empfï¿½nger": "Recipient_City",
    "Haus_Empfï¿½nger": "Recipient_House_No",

    # sender
    "Straï¿½e_Absender": "Sender_Street",
    "Sender_Postal_Code": "Sender_Postal_Code",
    "Stadt_Absender": "Sender_City",

    # already good
    "Shipment_ID": "Shipment_ID",
    "Loading_Date": "Loading_Date",
    "Weight": "Weight",
    "Freight_Cost": "Freight_Cost",
}



def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={k: v for k, v in COLUMN_RENAME_MAP.items() if k in df.columns})


# -----------------------------------------------------------------------------
# Street / address cleaning helpers
# -----------------------------------------------------------------------------

def split_street_and_number(s: str) -> pd.Series:
    parts = str(s).split()
    house = ""
    street = ""
    for part in parts:
        if any(char.isdigit() for char in part):
            house += part + " "
        else:
            street += part + " "
    return pd.Series([street.strip(), house.strip()])


def remove_prefix(street: str) -> str:
    return re.sub(r"^(AM|IM)\s+", "", str(street).strip(), flags=re.IGNORECASE)


def replace_roman_numerals(value: str) -> str:
    """
    Example: "II LEEGMOORWEG" -> "2 LEEGMOORWEG"
    """
    if roman is None:
        return str(value)

    value = str(value)
    match = re.match(r"^(I{1,3})(\.?)\s+", value)
    if not match:
        return value

    roman_numeral = match.group(1)
    point = match.group(2)
    try:
        number = roman.fromRoman(roman_numeral)
    except Exception:
        return value

    return value.replace(roman_numeral + point, str(number) + point, 1)


def replace_dash_with_space(street: str) -> str:
    return str(street).replace("-", " ")


def split_city_on_slash(city: str) -> str:
    return str(city).split("/", 1)[0].strip()


def split_house_no_on_dash_or_plus(house: str) -> str:
    split_result = re.split(r"[-+]", str(house))
    return split_result[0].strip()


def normalize_street_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Your older correct_streetnames() logic, but applied to renamed columns consistently.
    """
    out = df.copy()
    if "Recipient_Street" not in out.columns or "Recipient_City" not in out.columns:
        return out

    out["Recipient_Street"] = out["Recipient_Street"].astype(str).str.upper()
    out["Recipient_City"] = out["Recipient_City"].astype(str).str.upper()

    # Remove junk values
    out = out[~out["Recipient_Street"].isin(["#", "32", ".", "nan", "None"])]
    out = out[out["Recipient_City"] != "."]

    # Normalize common variants
    street_array = []
    hausnummerzusatz = list("ABCDEFGHabcdefgh")

    for s in out["Recipient_Street"].astype(str).tolist():
        split_hausnummer = s.split(" ")
        zusatz = split_hausnummer[-1] if split_hausnummer else ""
        if zusatz in hausnummerzusatz:
            zusatz_u = zusatz.upper()
            s = s.replace(" " + zusatz, zusatz_u)

        s = s.replace("/", "-")
        s = s.replace(" - ", "-").replace("- ", "-").replace(" -", "-")
        s = s.replace(",", ".")
        s = s.replace("STRAßE", "STRASSE")

        if ("STR." in s) and ("STRASSE" not in s):
            s = s.replace("STR.", "STRASSE")
        if ("STR " in s) and ("STRASSE" not in s):
            s = s.replace("STR ", "STRASSE ")

        s = s.replace("  ", " ")
        street_array.append(s)

    out["Recipient_Street"] = street_array
    return out


def apply_manual_address_corrections(df: pd.DataFrame, correction_csv: str) -> pd.DataFrame:
    """
    Replace Recipient_Street values based on a CSV correction list.

    Expected columns in correction_csv:
      - Recipient_Street_falsch
      - Recipient_Street_richtig
    """
    out = df.copy()
    corr = pd.read_csv(correction_csv, encoding="latin-1", sep=";")
    for _, row in corr.iterrows():
        wrong = str(row["Recipient_Street_falsch"]).upper()
        right = str(row["Recipient_Street_richtig"]).upper()
        out.loc[out["Recipient_Street"].astype(str).str.upper() == wrong, "Recipient_Street"] = right
    return out


# -----------------------------------------------------------------------------
# Main preprocessing steps (your pre_process + fixed wrapper)
# -----------------------------------------------------------------------------

def pre_process_addresses(df: pd.DataFrame) -> pd.DataFrame:
    """
    Your pre_process() logic, but:
    - no hardcoded file saving
    - safe string ops
    """
    out = df.copy()

    # Ensure required columns
    needed = ["Recipient_Street", "Recipient_City"]
    for c in needed:
        if c not in out.columns:
            return out

    # Split street and house number
    out[["Recipient_Street", "Recipient_House_No"]] = out["Recipient_Street"].apply(split_street_and_number)

    # Normalize fields
    out["Recipient_Street"] = out["Recipient_Street"].apply(remove_prefix)
    out["Recipient_Street"] = out["Recipient_Street"].apply(replace_roman_numerals)
    out["Recipient_Street"] = out["Recipient_Street"].apply(replace_dash_with_space)
    out["Recipient_City"] = out["Recipient_City"].apply(split_city_on_slash)
    out["Recipient_House_No"] = out["Recipient_House_No"].apply(split_house_no_on_dash_or_plus)

    return out


def preprocess_shipments(df: pd.DataFrame, cfg: PreprocessConfig = PreprocessConfig()) -> pd.DataFrame:
    """
    Final public-safe preprocessing entry point.

    What it does:
    1) Rename columns (German -> English canonical)
    2) Apply two known one-off fixes you had
    3) Normalize address strings + split street/house number
    4) Optional manual correction CSV
    5) Optional write to CSV (disabled by default)
    """
    out = df.copy()
    out = rename_columns(out)

    # One-off fixes (corrected: your code used `.out(...)` which is invalid)
    if "Recipient_City" in out.columns:
        out["Recipient_City"] = out["Recipient_City"].replace("GROSSENKETEN", "GROSSENKNETEN")
    if "Recipient_Postal_Code" in out.columns:
        out["Recipient_Postal_Code"] = out["Recipient_Postal_Code"].astype(str).str.replace("4824 ", "04824 ", regex=False)

    # Address normalization
    out = normalize_street_format(out)
    out = pre_process_addresses(out)

    # Optional manual corrections (private file, don’t commit)
    if cfg.address_correction_csv:
        out = apply_manual_address_corrections(out, cfg.address_correction_csv)

    # Basic typing
    if "Loading_Date" in out.columns:
        out["Loading_Date"] = pd.to_datetime(out["Loading_Date"], errors="coerce", dayfirst=True)
    if "Weight" in out.columns:
        out["Weight"] = pd.to_numeric(out["Weight"], errors="coerce")

    # Optional write
    if cfg.write_preprocessed_csv:
        if not cfg.preprocessed_csv_path:
            raise ValueError("write_preprocessed_csv=True but preprocessed_csv_path is None.")
        path = Path(cfg.preprocessed_csv_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(path, sep=";", encoding="latin1", decimal=".", index=False)

    return out
