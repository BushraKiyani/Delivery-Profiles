import pandas as pd
import numpy as np
import requests
import json


# Gets the coordinates using the Nominatim geocoding API
def get_receiver_coordinates(row):
    address = f"{row['Straße_Empfänger']}, {row['PLZ_Empfänger']}, {row['Stadt_Empfänger']}"
    url = f"https://asca-rest.lfo.tu-dortmund.de/nominatim/search.php?q={address}&format=jsonv2"
    response = requests.get(url)
    data = response.json()
    if len(data) > 0:
        coordinates = {
            "Empfänger_id": row['ID_Empfänger'],
            "longitude": data[0]['lon'],
            "latitude": data[0]['lat'],
        }
        return coordinates
    return None

# Writes Coordinates in a JSON file named as 'Koordinatenliste.json'
def write_coordinates_to_file(coordinates_list, json_coordinate_list_path):
    # convert the coordinates list to a JSON string
    json_string = json.dumps(coordinates_list)

    # write the JSON string to a file
    with open(json_coordinate_list_path, 'w') as f:
        f.write(json_string)
    print(f"Coordinates have been saved in {json_coordinate_list_path} file.")

# gets and writes the receiver coordinates using get_receiver_coordinates() and
# write_coordinates_to_file() functions
def get_and_write_receiver_coordinates(df,json_coordinate_list_path):
    coordinates_list = df.apply(get_receiver_coordinates, axis=1).tolist()
    coordinates_list = [x for x in coordinates_list if x is not None]
    write_coordinates_to_file(coordinates_list, json_coordinate_list_path)
    return coordinates_list
# Adds coordinates to the dataframe
def add_coordinates_to_df(lon_lat_list, df, sender_lon, sender_lat):
    """
    Takes a list of longitude and latitude values, a DataFrame with receiver ID and address information,
    and the sender's fixed longitude and latitude values. Adds the longitude and latitude to the corresponding
    rows in the DataFrame for each receiver address.
    """
    def update_row(row):
        Empfänger_ID = row['ID_Empfänger']
        Empfänger_lon, Empfänger_lat = None, None
        empfänger_coords = list(filter(lambda x: x['Empfänger_id'] == Empfänger_ID, lon_lat_list))
        if len(empfänger_coords) > 0:
            empfänger_coords = empfänger_coords[0]
            Empfänger_lon = empfänger_coords['longitude']
            Empfänger_lat = empfänger_coords['latitude']

        row['Empfänger_lon'] = Empfänger_lon
        row['Empfänger_lat'] = Empfänger_lat
        row['Absender_lon'] = sender_lon
        row['Absender_lat'] = sender_lat
        return row
    df = df.apply(update_row, axis=1)
    df[['Empfänger_lon', 'Empfänger_lat']] = df[['Empfänger_lon', 'Empfänger_lat']].astype(float).round(6)
    return df


def add_coordinates(processed_data, sender_lon, sender_lat, save_path, json_coordinate_list_path):
    # Get Unique data according to ID_Empfänger (For getting coordinates once per ID_Empfänger)
    unique_processed_data = processed_data.drop_duplicates(subset=['ID_Empfänger'])
    # Get Coordinates
    cor = get_and_write_receiver_coordinates(unique_processed_data,json_coordinate_list_path)
    # Add Coordinates to the dataframe
    added_coordinates = add_coordinates_to_df(cor, processed_data, sender_lon, sender_lat)
    # Save the file as "added_Koordinaten.csv"
    added_coordinates.to_csv(path_or_buf=save_path, sep=";", encoding="latin1", decimal=".", index=False)
    print(f"Coordinates have been calculated and the dataframe is saved in: {save_path}")
    return added_coordinates, cor


def round_sort_coordinates_original(file_path):
    with open(file_path) as f:
        locations = json.load(f)
    return locations







