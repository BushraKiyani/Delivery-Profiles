import requests
import pandas as pd
import json

# Get the coordinates using the Nominatim geocoding API
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

# write the Coordinates in a JSON file
def write_coordinates_to_file(coordinates_list):
    # convert the coordinates list to a JSON string
    json_string = json.dumps(coordinates_list)

    # writing the JSON string to a file
    with open('Koordinatenliste.json', 'w') as f:
        f.write(json_string)
        
# get and write the receiver coordinates using get_receiver_coordinates() and write_coordinates_to_file() functions
def get_and_write_receiver_coordinates(df):
    coordinates_list = df.apply(get_receiver_coordinates, axis=1).tolist()
    coordinates_list = [x for x in coordinates_list if x is not None]
    write_coordinates_to_file(coordinates_list)
    return coordinates_list


# Add coordinates to the dataframe
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

if __name__ == "__main__":
    rohdaten = pd.read_csv(r"../00_Resources/rohdaten.csv", encoding="latin_1", sep=";", decimal=',')
    lon_lat_list = get_and_write_receiver_coordinates(rohdaten)
    rohdaten = add_coordinates_to_df(lon_lat_list, rohdaten, 9.3371997, 53.1243393)
    rohdaten.to_csv(path_or_buf=r"../00_Resources/Grunddaten/added_Koordinaten.csv", sep=";", encoding="latin1", decimal=".", index=False)