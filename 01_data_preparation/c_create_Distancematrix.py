import pandas as pd
import requests
import numpy as np
import time
from geopy.distance import lonlat, distance
import math

def create_matrix_eukl(df_coordinates_list, factor = 1.4):
    df_koordinaten_geopy = df_coordinates_list.copy()
    df_koordinaten_geopy = df_koordinaten_geopy.set_index("ID_Empfänger", drop=True)

    dist_matrix_eukl = pd.DataFrame(columns=df_koordinaten_geopy.index, index=df_koordinaten_geopy.index)

    def calc_dist_m(start_lon, start_lat, end_lon, end_lat):
        start_point = (start_lon, start_lat)
        end_point = (end_lon, end_lat)
        return distance(lonlat(*start_point), lonlat(*end_point)).km * factor

    for row in dist_matrix_eukl.index:
        for col in dist_matrix_eukl.columns:
            start_lon = df_koordinaten_geopy.loc[row, "lon"]
            start_lat = df_koordinaten_geopy.loc[row, "lat"]
            end_lon = df_koordinaten_geopy.loc[col, "lon"]
            end_lat = df_koordinaten_geopy.loc[col, "lat"]
            dist_matrix_eukl.loc[row, col] = calc_dist_m(start_lon, start_lat, end_lon, end_lat)

    dist_matrix_eukl = dist_matrix_eukl.apply(pd.to_numeric, errors='coerce', axis=1)
    return dist_matrix_eukl

# round the coordinates upto 6 decimal places, extract unique ids and sort according to Empfänger_id
def round_sort_coordinates(file_path):
    with open(file_path) as f:
        locations = json.load(f)

    # Use map and lambda function to round off the latitude and longitude values
    locations = list(map(lambda loc: {'Empfänger_id': loc['Empfänger_id'], 'latitude': round(float(loc['latitude']), 4), 'longitude': round(float(loc['longitude']), 4)}, locations))

    # Extract unique ids using set comprehension and sort the list of dictionaries by the "Empfänger_id" key
    sorted_locations = sorted({loc['Empfänger_id']:loc for loc in locations}.values(), key=lambda x: x["Empfänger_id"])

    return sorted_locations

# Get distances and durations via OSRM API call, return and save separate distance/duration matrices.
def calculate_distances_durations(sorted_locations, chunk_size=100):
    base_url = "https://asca-rest.lfo.tu-dortmund.de/osrm/table/v1/driving/"
    params = {"annotations": "distance,duration"}  # get distances and durations
    num_chunks = math.ceil(len(sorted_locations) / chunk_size)

    # Initialize empty DataFrames to store distances and durations
    distances = pd.DataFrame(columns=[loc["Empfänger_id"] for loc in sorted_locations],
                             index=[loc["Empfänger_id"] for loc in sorted_locations])
    durations = pd.DataFrame(columns=[loc["Empfänger_id"] for loc in sorted_locations],
                             index=[loc["Empfänger_id"] for loc in sorted_locations])

    for i in range(num_chunks):
        for j in range(num_chunks):
            i_start, i_end = i * chunk_size, min((i + 1) * chunk_size, len(sorted_locations))
            j_start, j_end = j * chunk_size, min((j + 1) * chunk_size, len(sorted_locations))

            chunk1 = sorted_locations[i_start:i_end]
            chunk2 = sorted_locations[j_start:j_end]

            locations_str = ";".join([f"{loc['longitude']},{loc['latitude']}" for loc in chunk1 + chunk2])
            url = base_url + locations_str

            params["sources"] = ";".join(str(i) for i in range(len(chunk1)))
            params["destinations"] = ";".join(str(i + len(chunk1)) for i in range(len(chunk2)))

            response = requests.get(url, params=params)
            data = response.json()

            # Fill the distances and durations DataFrames with the received data
            chunk_distances = pd.DataFrame(data["distances"],
                                           columns=[loc["Empfänger_id"] for loc in chunk2],
                                           index=[loc["Empfänger_id"] for loc in chunk1])
            chunk_durations = pd.DataFrame(data["durations"],
                                           columns=[loc["Empfänger_id"] for loc in chunk2],
                                           index=[loc["Empfänger_id"] for loc in chunk1])

            distances.loc[chunk1[0]["Empfänger_id"]:chunk1[-1]["Empfänger_id"],
                          chunk2[0]["Empfänger_id"]:chunk2[-1]["Empfänger_id"]] = chunk_distances
            durations.loc[chunk1[0]["Empfänger_id"]:chunk1[-1]["Empfänger_id"],
                          chunk2[0]["Empfänger_id"]:chunk2[-1]["Empfänger_id"]] = chunk_durations

    distances.to_csv(path_or_buf=r"../00_Resources/Matrices/Real_Distanzmatrix.csv", sep=";", encoding="latin1",
                   decimal=".", index=False)
    durations.to_csv(path_or_buf=r"../00_Resources/Matrices/Real_Fahrzeitmatrix.csv", sep=";", encoding="latin1",
                   decimal=".", index=False)

    return distances, durations

if __name__ == "__main__":
    ##df_coordinates_list = pd.read_csv(
       ## r"../00_Resources/Grunddaten/Profilkunden_Koordinaten.csv",
        ##encoding="latin-1", sep=";", dtype={"ID_Empfänger":object, "lat": float,"lon": float})

    ##df_coordinates_list = df_coordinates_list[["ID_Empfänger", "lat", "lon"]]
    ##df_versandzentrum = {"ID_Empfänger":"Depot","lat":48.13635891257301,"lon":11.62868820669951}
    ##df_coordinates_list = df_coordinates_list.append(df_versandzentrum, ignore_index=True)

    ##dist_matrix_eukl = create_matrix_eukl(df_coordinates_list, 1.4)
    ##dist_matrix_eukl.to_csv(path_or_buf=r"../00_Resources/Grunddaten/distance_matrix_eukl.csv", index=True, sep=";",
                            ##encoding="latin1",decimal=".")
    ##dist_matrix_eukl.to_csv(path_or_buf=r"../00_Resources/Grunddaten/distance_matrix_eukl_EU.csv", index=True, sep=";",
                            ##encoding="latin1", decimal=",")
    file_path = "../01_data_preparation/Koordinatenliste.json"
    sorted_locations = round_sort_coordinates(file_path)
    distances, durations = calculate_distances_durations(sorted_locations)
    print(distances, durations)




