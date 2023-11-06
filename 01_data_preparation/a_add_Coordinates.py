import pandas as pd
import numpy as np
import requests
import json


# Gets the coordinates using the Nominatim geocoding API
def get_receiver_coordinates(row):
    address = f"{row['Recipient_Street']}, {row['Recipient_Postal_Code']}, {row['Recipient_City']}"
    url = f"https://asca-rest.lfo.tu-dortmund.de/nominatim/search.php?q={address}&format=jsonv2"
    response = requests.get(url)
    data = response.json()
    if len(data) > 0:
        coordinates = {
            "Empfänger_id": row['Recipient_ID'],
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
        Empfänger_ID = row['Recipient_ID']
        Recipient_Longitude, Recipient_Latitude = None, None
        empfänger_coords = list(filter(lambda x: x['Empfänger_id'] == Empfänger_ID, lon_lat_list))
        if len(empfänger_coords) > 0:
            empfänger_coords = empfänger_coords[0]
            Recipient_Longitude = empfänger_coords['longitude']
            Recipient_Latitude = empfänger_coords['latitude']

        row['Recipient_Longitude'] = Recipient_Longitude
        row['Recipient_Latitude'] = Recipient_Latitude
        row['Sender_Longitude'] = sender_lon
        row['Sender_Latitude'] = sender_lat
        return row
    df = df.apply(update_row, axis=1)
    df[['Recipient_Longitude', 'Recipient_Latitude']] = df[['Recipient_Longitude', 'Recipient_Latitude']].astype(float).round(6)
    return df


def add_coordinates(processed_data, sender_lon, sender_lat, save_path, json_coordinate_list_path):
    # Get Unique data according to Recipient_ID (For getting coordinates once per Recipient_ID)
    unique_processed_data = processed_data.drop_duplicates(subset=['Recipient_ID'])
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







