import pandas as pd
import requests
import numpy as np
import time
from geopy.distance import lonlat, distance
import math
import json
from scipy.spatial.distance import cdist

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

# round the coordinates upto 6 decimal places, and sort according to Empfänger_id
def round_sort_coordinates(file_path):
    with open(file_path) as f:
        locations = json.load(f)

    # Use map and lambda function to round off the latitude and longitude values
    locations = list(map(lambda loc: {'Empfänger_id': loc['Empfänger_id'], 'latitude': round(float(loc['latitude']), 6),
                                      'longitude': round(float(loc['longitude']), 6)}, locations))

    # Extract unique ids using set comprehension and sort the list of dictionaries by the "Empfänger_id" key
    sorted_locations = sorted({loc['Empfänger_id']:loc for loc in locations}.values(), key=lambda x: x["Empfänger_id"])

    return sorted_locations

# Gets the distances and the durations via OSRM API call, return and save separate distance/duration matrices.
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
    # Get Symmetric distance Matrix
    matrix = distances.values
    symmetric_matrix = np.triu(matrix) + np.triu(matrix, 1).T
    distances = pd.DataFrame(symmetric_matrix, index=distances.index, columns=distances.columns)
    # Get Symmetric duration Matrix
    matrix1 = durations.values
    symmetric_matrix1 = np.triu(matrix1) + np.triu(matrix1, 1).T
    durations = pd.DataFrame(symmetric_matrix1, index=durations.index, columns=durations.columns)

    distances.to_csv(path_or_buf=r"../00_Resources/Matrices/Real_Distanzmatrix.csv", sep=",",
                    decimal=".", index=True)
    durations.to_csv(path_or_buf=r"../00_Resources/Matrices/Real_Durationsmatrix.csv", sep=",",
                    decimal=".", index=True)

    return distances, durations



"""Takes Sorted Coordinates JSON file and Output file Path+Name, Calculates the Euclidean distances save the file in specified
 location with the provided name and returns the Euclidean distance matrix"""
def calculate_euclidean_distance_matrix(sorted_json_file):
    # Load JSON data into a pandas DataFrame
    df = pd.json_normalize(sorted_json_file)

    # Convert latitude and longitude columns to floats
    df[['latitude', 'longitude']] = df[['latitude', 'longitude']].astype(float)

    # Extract latitude and longitude columns into a NumPy array
    coordinates = df[['latitude', 'longitude']].to_numpy()

    # Calculate Euclidean distance matrix using scipy.spatial.distance.cdist
    Euc_distance_matrix = cdist(coordinates, coordinates)

    # Convert the distance matrix back to a pandas DataFrame
    Euc_distance_matrix = pd.DataFrame(Euc_distance_matrix, columns=df['Empfänger_id'], index=df['Empfänger_id'])

    # Save the distance matrix to a CSV file
    Euc_distance_matrix.to_csv(path_or_buf=r"../00_Resources/Matrices/Euklidische_Distanzmatrix.csv", sep=",", decimal=".", index=True)
    return Euc_distance_matrix

# returns combined table of all distances and save it in Matrices folder as Combined_Matrixtable.csv
def create_row(start_id, end_id, euclidean, distances, durations):
    if start_id != end_id:
        real_distance = distances.at[start_id, end_id]
        duration = durations.at[start_id, end_id]
        euclidean_distance = euclidean.at[start_id, end_id]

        return {
            'Start': start_id,
            'End': end_id,
            'Real': real_distance,
            'Duration': duration,
            'Euclidean': euclidean_distance
        }
    return None

def create_table(euclidean, distances, durations):
    empfanger_ids = euclidean.columns
    accumulator = []

    for start_id in empfanger_ids:
        for end_id in empfanger_ids:
            if start_id < end_id:
                row = create_row(start_id, end_id, euclidean, distances, durations)
                if row:
                    accumulator.append(row)

    result = pd.DataFrame(accumulator)
    # Save the table to a CSV file
    result.to_csv(path_or_buf=r"../00_Resources/Matrices/Combined_Matrixtable.csv", sep=",",
                  decimal=".", index=False)
    return result


if __name__ == "__main__":
    df_coordinates_list = pd.read_csv(
       r"../00_Resources/Grunddaten/Profilkunden_Koordinaten.csv",
        encoding="latin-1", sep=";", dtype={"ID_Empfänger":object, "lat": float,"lon": float})

    df_coordinates_list = df_coordinates_list[["ID_Empfänger", "lat", "lon"]]
    df_versandzentrum = {"ID_Empfänger":"Depot","lat":48.13635891257301,"lon":11.62868820669951}
    df_coordinates_list = df_coordinates_list.append(df_versandzentrum, ignore_index=True)

    dist_matrix_eukl = create_matrix_eukl(df_coordinates_list, 1.4)
    dist_matrix_eukl.to_csv(path_or_buf=r"../00_Resources/Grunddaten/distance_matrix_eukl.csv", index=True, sep=";",
                            encoding="latin1",decimal=".")
    dist_matrix_eukl.to_csv(path_or_buf=r"../00_Resources/Grunddaten/distance_matrix_eukl_EU.csv", index=True, sep=";",
                            encoding="latin1", decimal=",")
    ###############################################################################################################
    # load the Coordinates JSON file
    file_path = "../01_data_preparation/Koordinatenliste.json"
    # Round the Coordinates and Sort according to Empfänger_id
    sorted_locations = round_sort_coordinates(file_path)
    # Get distances and durations from OSRM
    distances, durations = calculate_distances_durations(sorted_locations)
    # Get Euclidean distance matrix
    euclidean = calculate_euclidean_distance_matrix(sorted_locations)
    # Table of all distances
    distance_table = create_table(euclidean, distances, durations)
    # Print real distance, duration, Euclidean distance Matrices and Distances Table
    print(distances, durations, euclidean, distance_table)




