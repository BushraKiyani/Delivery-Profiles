import pandas as pd
import requests
import numpy as np
import time
#from geopy.distance import lonlat, distance
import math
import json
from haversine import haversine_vector, Unit, haversine
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
def round_sort_coordinates(locations):
    # Use map and lambda function to round off the latitude and longitude values
    locations = list(map(lambda loc: {'Empfänger_id': loc['Empfänger_id'], 'latitude': round(float(loc['latitude']), 6),
                                      'longitude': round(float(loc['longitude']), 6)}, locations))

    # Extract unique ids using set comprehension and sort the list of dictionaries by the "Empfänger_id" key
    sorted_locations = sorted({loc['Empfänger_id']:loc for loc in locations}.values(), key=lambda x: x["Empfänger_id"])

    return sorted_locations

# Gets the distances and the durations via OSRM API call, return and save separate distance/duration matrices.
def calculate_distances_durations(sorted_locations,distances_path_C, duration_path_C, chunk_size=100):
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

    distances.to_csv(path_or_buf=distances_path_C, sep=",", decimal=".", index=True)
    durations.to_csv(path_or_buf=duration_path_C, sep=",", decimal=".", index=True)
    print(f"Real Distance and Duration matrices between customers have been calculated and saved in: {distances_path_C} and {duration_path_C}, respectively")

    return distances, durations


"""Takes Sorted Coordinates JSON file and Output file Path+Name, Calculates the Euclidean distances save the file in specified
 location with the provided name and returns the Euclidean distance matrix"""


def calculate_euclidean_distance_matrix(sorted_locations, euk_distance_path_C):
    # Load JSON data into a pandas DataFrame
    df = pd.json_normalize(sorted_locations)

    # Convert latitude and longitude columns to floats
    df[['latitude', 'longitude']] = df[['latitude', 'longitude']].astype(float)

    # Extract latitude and longitude columns into a NumPy array
    coordinates = df[['latitude', 'longitude']].to_numpy()

    # Function to calculate Haversine distance between two arrays of coordinates
    def haversine_distance(coord1, coord2):
        return haversine(coord1, coord2, unit=Unit.KILOMETERS)

    # Calculate Haversine distance matrix
    num_locations = len(coordinates)
    euclidean_distance_matrix = np.zeros((num_locations, num_locations))
    for i in range(num_locations):
        euclidean_distance_matrix[i] = np.apply_along_axis(haversine_distance, 1, coordinates, coordinates[i])

    # Convert the distance matrix to a pandas DataFrame
    euclidean_distance_matrix = pd.DataFrame(euclidean_distance_matrix, columns=df['Empfänger_id'], index=df['Empfänger_id'])

    # Save the distance matrix to a CSV file
    euclidean_distance_matrix.to_csv(path_or_buf=euk_distance_path_C, sep=",", decimal=".", index=True)
    print(f"Euclidean distance matrix between customers has been calculated and saved in: {euk_distance_path_C}")

    return euclidean_distance_matrix

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


def create_table(euclidean, distances, durations, matrix_table_path_C):
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
    result.to_csv(path_or_buf=matrix_table_path_C, sep=",",
                  decimal=".", index=False)
    print(f"Combined matrix table has been created and saved in: {matrix_table_path_C}")
    return result


##################### Sender Distance Calculation #############################
def calculate_distances_durations_sender(df_sendigun, sender_lon, sender_lat, distances_path_S, duration_path_S, chunk_size=100):
    df_sendigun[['Absender_lat', 'Absender_lon', 'Empfänger_lat', 'Empfänger_lon']] = df_sendigun[
        ['Absender_lat', 'Absender_lon', 'Empfänger_lat', 'Empfänger_lon']].astype(float)
    base_url = "https://asca-rest.lfo.tu-dortmund.de/osrm/table/v1/driving/"
    params = {"annotations": "distance,duration"}  # get distances and durations
    num_chunks = math.ceil(len(df_sendigun) / chunk_size)

    # Initialize empty DataFrames to store distances and durations
    distances = pd.DataFrame(columns=df_sendigun.index, index=['Absender'])
    durations = pd.DataFrame(columns=df_sendigun.index, index=['Absender'])

    # Fixed Absender location
    absender_location = {'longitude': sender_lon, 'latitude': sender_lat}

    for i in range(num_chunks):
        i_start, i_end = i * chunk_size, min((i + 1) * chunk_size, len(df_sendigun))

        chunk = df_sendigun[i_start:i_end]

        locations_str = f"{absender_location['longitude']},{absender_location['latitude']};"
        locations_str += ";".join([f"{row['Empfänger_lon']},{row['Empfänger_lat']}" for _, row in chunk.iterrows()])
        url = base_url + locations_str

        params["sources"] = "0"  # Absender is the source
        params["destinations"] = ";".join(str(i + 1) for i in range(len(chunk)))  # Empfänger locations are the destinations

        response = requests.get(url, params=params)
        data = response.json()

        # Fill the distances and durations DataFrames with the received data
        distances.loc['Absender', chunk.index] = data["distances"][0]
        durations.loc['Absender', chunk.index] = data["durations"][0]

        # Add distances and durations to the df_sendigun DataFrame
        df_sendigun.loc[chunk.index, 'Real_Distance'] = data["distances"][0]
        df_sendigun.loc[chunk.index, 'Duration'] = data["durations"][0]

    distances.to_csv(path_or_buf=distances_path_S, sep=",", decimal=".", index=True)
    durations.to_csv(path_or_buf=duration_path_S, sep=",", decimal=".", index=True)
    print(f"Real distances and durations between customers and the sender have been added to the dataframe in columns Real_Distance and Duration and saved in: {distances_path_S} and {duration_path_S}")
    return df_sendigun
def calculate_euclidean_distance_sender(df_sendigun, sender_lon, sender_lat,euk_distance_path_S ):
    # Fixed Absender location
    absender_location = (sender_lat, sender_lon) # (lat, lon)

    # Calculate Haversine distance for each row and add it to a new column
    df_sendigun['Euc_Distance'] = df_sendigun.apply(
        lambda row: haversine(absender_location, (row['Empfänger_lat'], row['Empfänger_lon']), unit=Unit.KILOMETERS),
        axis=1)

    # Save the haversine distance to a CSV file
    df_sendigun['Euc_Distance'].to_csv(euk_distance_path_S, sep=",", decimal=".", index=True)
    print(f"Euclidean distances between customers and the sender have been added to the dataframe in column Euc_Distance and save in:{euk_distance_path_S}")
    return df_sendigun

########################Combine Distances Calculation###########################
def create_distance_matrices(df, coordinate_list, sender_lon, sender_lat, distances_path_C,duration_path_C,euk_distance_path_C,matrix_table_path_C, distances_path_S, duration_path_S, euk_distance_path_S, df_distance_path, chunk_size=100):
    # Round the Coordinates and Sort according to Empfänger_id
    sorted_locations = round_sort_coordinates(coordinate_list)
    # Get distances and durations from OSRM
    distances, durations = calculate_distances_durations(sorted_locations,distances_path_C,duration_path_C,chunk_size)
    # Get Euclidean distance matrix
    euclidean = calculate_euclidean_distance_matrix(sorted_locations,euk_distance_path_C)
    # Table of all distances
    distance_table = create_table(euclidean, distances, durations, matrix_table_path_C)
    # Sender-Customer durations and distances
    distances_sender_df = calculate_distances_durations_sender(df,sender_lon, sender_lat,distances_path_S, duration_path_S, chunk_size)
    # Sender-Customer Euclidean distances
    distances_euc_sender_df = calculate_euclidean_distance_sender(distances_sender_df, sender_lon, sender_lat, euk_distance_path_S)
    # Save the dataframe with distances
    distances_euc_sender_df.to_csv(path_or_buf=df_distance_path, sep=";", encoding="latin1",
                    decimal=".", index=False)
    print(f"All distances have been added to dataframe df_added_distances and saved in: {df_distance_path}")
    # return real distance, duration, Euclidean distance Matrices and Distances Table
    return distances, durations, euclidean, distance_table, distances_euc_sender_df





