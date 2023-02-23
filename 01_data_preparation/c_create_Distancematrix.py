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




