import pandas as pd
import requests
import numpy as np
import time

from geopy.distance import lonlat, distance
import math

def create_coordinates_list(df_touren_koordinaten):
    versandzentren_array = df_touren_koordinaten.index.unique()
    lat_array = []
    lon_array = []
    for i in versandzentren_array:
        lat = df_touren_koordinaten.loc[i, "versandzentrum_lat"]
        lon = df_touren_koordinaten.loc[i, "versandzentrum_lon"]
        lat = lat[1]
        lon = lon[1]
        lat_array.append(lat)
        lon_array.append(lon)

    df_versandzentren = {"ID": versandzentren_array, "lat": lat_array, "lon": lon_array}
    df_versandzentren = pd.DataFrame(df_versandzentren)

    df_coordinates_list = df_touren_koordinaten.loc[:,["ID_Empfänger", "empfaenger_lat", "empfaenger_lon"]].copy()
    df_coordinates_list.columns = ["ID", "lat", "lon"]
    df_coordinates_list = df_coordinates_list.drop_duplicates(keep="first").sort_values(by="ID").reset_index(drop=True)
    df_coordinates_list["ID"] = df_coordinates_list["ID"].astype(str)

    df_coordinates_list_comp = df_coordinates_list.append(df_versandzentren).reset_index(drop=True)

    return df_coordinates_list_comp

def create_matrix_eukl(df_coordinates_list):
    df_koordinaten_geopy = df_coordinates_list.copy()
    df_koordinaten_geopy = df_koordinaten_geopy.set_index("ID_Empfänger", drop=True)

    dist_matrix_eukl = pd.DataFrame(columns=df_koordinaten_geopy.index, index=df_koordinaten_geopy.index)

    def calc_dist_m(start_lon, start_lat, end_lon, end_lat):
        start_point = (start_lon, start_lat)
        end_point = (end_lon, end_lat)
        return distance(lonlat(*start_point), lonlat(*end_point)).km

    for row in dist_matrix_eukl.index:
        for col in dist_matrix_eukl.columns:
            start_lon = df_koordinaten_geopy.loc[row, "lon"]
            start_lat = df_koordinaten_geopy.loc[row, "lat"]
            end_lon = df_koordinaten_geopy.loc[col, "lon"]
            end_lat = df_koordinaten_geopy.loc[col, "lat"]
            dist_matrix_eukl.loc[row, col] = calc_dist_m(start_lon, start_lat, end_lon, end_lat)

    dist_matrix_eukl = dist_matrix_eukl.apply(pd.to_numeric, errors='coerce', axis=1)
    return dist_matrix_eukl

def create_matrix_real(df_coordinates_list):
    df_koordinaten = df_coordinates_list.copy()
    df_koordinaten = df_koordinaten.set_index("ID_Empfänger", drop=True)
    df_koordinaten.index =df_koordinaten.index.map(str)

    distance_matrix_real_TK = pd.DataFrame(columns=df_koordinaten.index,
                                               index=df_koordinaten.index)
    duration_matrix_real_TK = pd.DataFrame(columns=df_koordinaten.index,
                                               index=df_koordinaten.index)

    try:
        duration_matrix_real_TK = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\duration_matrix_real.csv",
        encoding="latin-1",
        sep=";", index_col="ID_Empfänger", dtype={"ID_Empfänger": object})
    except:
        print("")

    try:
        distance_matrix_real_TK = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\distance_matrix_real.csv",
        encoding="latin-1",
        sep=";", index_col="ID_Empfänger", dtype={"ID_Empfänger": object})
    except:
        print("")


    duration_matrix_real_TK_copy = duration_matrix_real_TK.copy()
    distance_matrix_real_TK_copy = distance_matrix_real_TK.copy()

    for index, row in duration_matrix_real_TK_copy.iterrows():
        if row["Rotenburg (Wümme)"] != None:
            duration_matrix_real_TK_copy.drop(index = index)

    for index, row in distance_matrix_real_TK_copy.iterrows():
        if row["Rotenburg (Wümme)"] != None:
            distance_matrix_real_TK_copy.drop(index = index)

    def get_distance_duration(koordinaten_list):
        destination_array = list(range(len(koordinaten_destination)))

        body = {"locations": koordinaten_list, "metrics": ["distance", "duration"], "destinations" : destination_array, "units": "m"}

        headers = {
            'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
            'Authorization':"5b3ce3597851110001cf6248e6bcafc8ce1e458f9c249254ad25a89e" ,#'5b3ce3597851110001cf6248e6bcafc8ce1e458f9c249254ad25a89e' #'5b3ce3597851110001cf6248033cc8f1b7c245168f99842d15f1fa05', "5b3ce3597851110001cf6248763389f407b14e3897e444e9a3aad540"
            'Content-Type': 'application/json; charset=utf-8'
        }
        call = requests.post('https://api.openrouteservice.org/v2/matrix/driving-hgv', json=body, headers=headers)
        print(call)
        response_dict = call.json()
        #print(response_dict)
        #print(len(response_dict['distances']))
        #print(len(response_dict['durations']))

        return response_dict['distances'], response_dict['durations']

    def assign_to_distance_matrix(df_distance_matrix_part):
        for row in df_distance_matrix_part.index:
            for col in df_distance_matrix_part.columns:
                distance_matrix_real_TK.loc[row, col] = df_distance_matrix_part.loc[row, col]

    def assign_to_duration_matrix(df_duration_matrix_part):
        for row in df_duration_matrix_part.index:
            for col in df_duration_matrix_part.columns:
                duration_matrix_real_TK.loc[row, col] = df_duration_matrix_part.loc[row, col]


    for row in range(math.ceil(len(duration_matrix_real_TK_copy.index) / 25)):
        for col in range(math.ceil(len(duration_matrix_real_TK_copy.index) / 25)):
            koordinaten_start = duration_matrix_real_TK_copy.index.values[(row + 1) * 25 - 25:(row + 1) * 25]
            koordinaten_destination = duration_matrix_real_TK_copy.index.values[(col + 1) * 25 - 25:(col + 1) * 25]
            length_destination_array = len(koordinaten_destination)
            #print("koordinaten_start")
            #print(koordinaten_start)
            #print("koordinaten_destination")
            #print(koordinaten_destination)

            koordinaten_destination_array = []
            # koordinaten aller Ziele
            for p in koordinaten_destination:
                p =str(p)
                lat = df_koordinaten.loc[p, "lat"]
                lon = df_koordinaten.loc[p, "lon"]
                lon_lat = [lon, lat]
                koordinaten_destination_array.append(lon_lat)

            # Koordinaten des Starts
            koordinaten_start_array = []
            for p in koordinaten_start:
                p = str(p)
                lat = df_koordinaten.loc[p, "lat"]
                lon = df_koordinaten.loc[p, "lon"]
                lon_lat = [lon, lat]
                koordinaten_start_array.append(lon_lat)

            #Koordinaten Start und Ziele
            koordinaten_gesamt = []
            koordinaten_gesamt.extend(koordinaten_destination_array)
            koordinaten_gesamt.extend(koordinaten_start_array)

            # Daten abrufen
            distance_matrix_part_values, duration_matrix_part_values = get_distance_duration(koordinaten_gesamt)


            destination_cols_len = len(koordinaten_destination)

            df_distance_matrix_part = pd.DataFrame(data=distance_matrix_part_values[destination_cols_len:], index=koordinaten_start,
                                                 columns=koordinaten_destination, dtype=float).drop_duplicates()
            df_duration_matrix_part = pd.DataFrame(data=duration_matrix_part_values[destination_cols_len:], index=koordinaten_start,
                                                 columns=koordinaten_destination, dtype=float).drop_duplicates()
            #print(df_distance_matrix_part)

            #df_distance_matrix_part = df_distance_matrix_part.loc[:, ~df_distance_matrix_part.columns.duplicated()]
            #df_duration_matrix_part = df_duration_matrix_part.loc[:, ~df_duration_matrix_part.columns.duplicated()]

            assign_to_distance_matrix(df_distance_matrix_part)
            assign_to_duration_matrix(df_duration_matrix_part)

            duration_matrix_real_TK.to_csv(
                path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\duration_matrix_real.csv",
                index=True, sep=";",
                encoding="latin1", decimal=".")
            print("gespeichert")
            distance_matrix_real_TK.to_csv(
                path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\distance_matrix_real.csv",
                index=True, sep=";",
                encoding="latin1", decimal=".")

            print("wait 1 sec")
            time.sleep(1.6)
            print("{} row_index".format(row))
            print("{} col_index".format(col))

    """
    print("starte Sync")
    #Sync. Sites
    for col in dist_matrix_mapbox_distance.columns:
        for row in dist_matrix_mapbox_distance.index:
            dist_matrix_mapbox_distance.loc[col, row] = dist_matrix_mapbox_distance.loc[row, col]
            dist_matrix_mapbox_duration.loc[col, row] = dist_matrix_mapbox_duration.loc[row, col]

    dist_matrix_mapbox_distance = dist_matrix_mapbox_distance.apply(pd.to_numeric, errors='coerce', axis=1)
    dist_matrix_mapbox_duration = dist_matrix_mapbox_duration.apply(pd.to_numeric, errors='coerce', axis=1)
    print("Sync beendet")
    """


    #dist_matrix_mapbox_duration.to_csv(path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\duration_matrix_real.csv", index=True, sep=";",
    #                       encoding="latin1", decimal=".")
    #dist_matrix_mapbox_distance.to_csv(path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\distance_matrix_real.csv", index=True, sep=";",
    #                        encoding="latin1", decimal=".")


    return dist_matrix_mapbox_distance, dist_matrix_mapbox_duration

def create_Distancematrix(df_Rohdaten_aufbereitet):
    df_coordinates_list = create_coordinates_list(df_Rohdaten_aufbereitet)
    print("Koordinatenliste erstellt")
    dist_matrix_eukl = create_matrix_eukl(df_coordinates_list)
    print("eukl Matrix")
    dist_matrix_real, dur_matrix_real = create_matrix_real(df_coordinates_list)
    print("reale Matrizen")
    return dist_matrix_eukl,dist_matrix_real, dur_matrix_real


if __name__ == "__main__":
    df_touren_koordinaten = pd.read_csv(
        r"../00_Resources/Grunddaten/Datensatz_TK_bereinigt.csv",
        encoding="latin-1", sep=";")

    df_coordinates_list = pd.read_csv(
        r"../00_Resources/Grunddaten/ID_liste.csv",
        encoding="latin-1", sep=";", dtype={"ID_Empfänger":object, "lat": float,"lon": float})

    df_coordinates_list = df_coordinates_list[["ID_Empfänger", "lat", "lon"]]
    df_versandzentrum = {"ID_Empfänger":"Rotenburg (Wümme)","lat":53.12433928160658,"lon":9.337199734018563}
    df_coordinates_list = df_coordinates_list.append(df_versandzentrum, ignore_index= True)

    dist_matrix_eukl = create_matrix_eukl(df_coordinates_list)
    dist_matrix_eukl.to_csv(path_or_buf=r"../00_Resources/Grunddaten/distance_matrix_eukl.csv", index=True, sep=";",encoding="latin1",decimal=".")

    #dist_matrix_real, dur_matrix_real = create_matrix_real(df_coordinates_list)
    #dur_matrix_real.to_csv(path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\duration_matrix_real_TK.csv", index=True, sep=";", encoding="latin1",decimal=".")
    #dist_matrix_real.to_csv(path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\distance_matrix_real_TK.csv", index=True, sep=";", encoding="latin1",decimal=".")
    #print("matrix_real")
    #print(dist_matrix_real)
    #print(dur_matrix_real)




