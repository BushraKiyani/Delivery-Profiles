import pandas as pd
import requests
import numpy as np
import os
from geopy.distance import lonlat, distance
import math

def add_freightcosts(df_touren_distanzen, tarifmatrix_long, columnname):
    frachtkosten_array = []
    for index, row in df_touren_distanzen.iterrows():
        tarifmatrix_long_filtered = tarifmatrix_long[
            (tarifmatrix_long["Distanz"] <= row["Distanz"]) & (
                        tarifmatrix_long["Gewicht"] <= row["avg_Gewicht"])]
        frachtkosten_array.append(tarifmatrix_long_filtered.iloc[-1, -1])
    df_touren_distanzen[columnname] = frachtkosten_array

    #df_touren_distanzen.to_csv(path_or_buf="Resources/Testdaten_TK_aufbereitet.csv", sep=";",encoding="latin1", decimal=".")
    return df_touren_distanzen

def get_distance_duration(koordinaten_list):
    dist_matrix = []
    dur_matrix = []
    for i in range(math.ceil(len(koordinaten_list)/ 25)):
        sub_dist_array = []
        sub_dur_array = []
        for k in range(math.ceil(len(koordinaten_list) / 25)):
            locations = koordinaten_list[k*25:(k+1)*25] + koordinaten_list[i*25:(i+1)*25]
            destinations = list(range(len(koordinaten_list[k*25:(k+1)*25])))
            sources = list(range(len(koordinaten_list[k*25:(k+1)*25]) , (len(koordinaten_list[k*25:(k+1)*25]) +len(koordinaten_list[i*25:(i+1)*25]))))

            body = {"locations": locations , "metrics": ["distance", "duration"],"units": "km", "destinations" : destinations, "sources" : sources}

            headers = {
                'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
                'Authorization': "5b3ce3597851110001cf6248e6bcafc8ce1e458f9c249254ad25a89e",
                # '5b3ce3597851110001cf6248e6bcafc8ce1e458f9c249254ad25a89e' #'5b3ce3597851110001cf6248033cc8f1b7c245168f99842d15f1fa05', "5b3ce3597851110001cf6248763389f407b14e3897e444e9a3aad540"
                'Content-Type': 'application/json; charset=utf-8'
            }
            call = requests.post("https://api.openrouteservice.org/v2/matrix/driving-hgv", json=body, headers=headers)
            #print(call)
            response_dict = call.json()
            #print(response_dict)
            #print(response_dict['distances'])

            if not sub_dist_array:
                sub_dist_array = response_dict['distances']
                sub_dur_array = response_dict['durations']
            else:
                for index, array in enumerate(sub_dist_array):
                    sub_dist_array[index] =sub_dist_array[index] + response_dict['distances'][index]
                    sub_dur_array[index] = sub_dur_array[index] + response_dict['durations'][index]

        dist_matrix = dist_matrix + sub_dist_array
        dur_matrix = dur_matrix +sub_dur_array

    return dist_matrix, dur_matrix

def create_matrix_eukl(koordinaten_list):
    dist_eukl = []

    def calc_dist_km(start_lon, start_lat, end_lon, end_lat):
        start_point = (start_lon, start_lat)
        end_point = (end_lon, end_lat)
        return distance(lonlat(*start_point), lonlat(*end_point)).km *1.4

    for i in koordinaten_list:
        sub_dist_eukl = []
        for k in koordinaten_list:
            start_lon = i[0]
            start_lat = i[1]
            end_lon = k[0]
            end_lat = k[1]
            sub_dist_eukl.append(calc_dist_km(start_lon, start_lat, end_lon, end_lat))
        dist_eukl.append(sub_dist_eukl)
    #print(dist_eukl)
    return dist_eukl

def make_symetic(matrix):
    for i in range(len(matrix)):
        for j in range(len(matrix)):
            matrix[i][j]= matrix[j][i]
    return matrix

if __name__ == '__main__':
    df_var = pd.read_csv(r"../00_Resources/pre_Analysis/Variabilitätsauswertung/Variabilitätsauswertung.csv", encoding="latin_1", sep=";", index_col= "ID_Empfänger")
    df_TK = pd.read_csv(r"../00_Resources/Grunddaten/Datensatz_TK_fertig.csv", encoding="latin_1", sep=";", index_col= "ID_Empfänger")
    df_coordinates = pd.read_csv(r"../00_Resources/Grunddaten/Profilkunden_Koordinaten.csv", encoding="latin_1", sep=";",
                        index_col="ID_Empfänger")

    #df_koord = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\ID_liste.csv", encoding="latin_1", sep=";", index_col= "ID_Empfänger")

    var_gew = 0.75
    var_freq = 0.75
    min_freq = 1
    real_matrix = True
    tarif_matrix = False
    preis_basis = 23.28
    preis_tonne = 35.31

    #df_var filtern
    df_var = df_var[(df_var["avg_Frequenz"]>= min_freq) & (df_var["variability_Gewicht"] <= var_gew) & (df_var["variability_Frequenz"] <= var_freq)]

    #df_instance = df_var.join(df_koord).reset_index()
    df_instance = pd.merge(df_var, df_coordinates, on='ID_Empfänger', how='inner',left_index=True).reset_index()
    print(df_instance.info())
    #df_instance["avg_Gewicht"] = round(df_instance["avg_Gewicht"]/round(df_instance["avg_Frequenz"]))
    #df_instance["avg_Frequenz"] =  round(df_instance["avg_Frequenz"])

    df_instance = df_instance[["ID_Empfänger", "lat", "lon", "avg_Gewicht", "avg_Frequenz"]]
    print(df_instance)

    # Add Depot
    df_depot = pd.DataFrame(data={"ID_Empfänger":[0],  "lat":[48.13635891257301] , "lon":[11.62868820669951], "avg_Gewicht": [0], "avg_Frequenz":[0]})
    df_instance = pd.concat([df_depot, df_instance])

    df_instance["avg_Gewicht"] = df_instance["avg_Gewicht"].round()
    df_instance["avg_Frequenz"] = df_instance["avg_Frequenz"].round()

    print(df_instance)

    coordinates_list = df_instance.append({"ID_Empfänger": "0", "lat": 48.13635891257301, "lon": 11.62868820669951},
                                                     ignore_index=True)

    # Koordinatenspalte erstellen
    df_instance["Koordinaten"] = df_instance[["lon","lat"]].values.tolist()

    print(df_instance["Koordinaten"].values.tolist())

    # Euklinsische Distanzmatrix erstellen
    dist_eukl = create_matrix_eukl(df_instance["Koordinaten"].values.tolist())

    df_distmatrix_eukl = pd.DataFrame(columns=df_instance.ID_Empfänger.values,
                                      index=df_instance.ID_Empfänger.values,
                                      data=dist_eukl)
    print(df_distmatrix_eukl)

    df_distmatrix_eukl.to_csv(
        r"../00_Resources/Matrices/TK_distmatrix_eukl_"+str(min_freq)+"-" + str(var_gew) + "-" + str(var_freq) + ".csv", sep=";",
        encoding="latin1", decimal=".")

    if real_matrix == False:
        # Distanzen hinzufügen
        df_instance["Distanz"] = df_distmatrix_eukl.loc[0].values[0:]
        # Fahrzeiten hinzufügen
        df_instance["Dauer"] = df_distmatrix_eukl.loc[0].values[0:]

    else:
        if not os.path.exists(r"../00_Resources/Matrices/TK_durmatrix_"+str(min_freq)+"-" + str(
               var_gew) + "-" + str(var_freq) + ".csv"):
            # Reale Matrizen erstellen
            dist, dur = get_distance_duration(df_instance["Koordinaten"].values.tolist())

            print(dist)  # distance in km
            dur = (np.array(dur) / 60).tolist()
            # print(dur)  #duration in s

            dist = make_symetic(dist)
            dur = make_symetic(dur)

            df_distmatrix = pd.DataFrame(columns=df_instance.ID_Empfänger.values, index=df_instance.ID_Empfänger.values,
                                             data=dist)
            df_durmatrix = pd.DataFrame(columns=df_instance.ID_Empfänger.values, index=df_instance.ID_Empfänger.values,
                                            data=dur)

            print(df_distmatrix)
            print(df_durmatrix)

            df_distmatrix_stacked = df_distmatrix.stack().reset_index()
            df_durmatrix_stacked = df_durmatrix.stack().reset_index()

            df_distmatrix_stacked.columns = ["from", "to", "distance"]
            df_distmatrix_stacked["time"] = df_durmatrix_stacked[0]

            df_distmatrix_stacked.to_csv(
                r"../00_Resources/Matrices/TK_matrizen_" +str(min_freq)+"-" + str(
                    var_gew) + "-" + str(var_freq) + ".txt", sep=";",
                encoding="latin1", decimal=".", index=False)

            df_distmatrix.to_csv(
                r"../00_Resources/Matrices/TK_distmatrix_"+str(min_freq)+"-" + str(
                   var_gew) + "-" + str(var_freq) + ".csv", sep=";",
                encoding="latin1", decimal=".")
            df_durmatrix.to_csv(
                r"../00_Resources/Matrices/TK_durmatrix_" +str(min_freq)+"-" + str(
                   var_gew) + "-" + str(var_freq) + ".csv", sep=";",
                encoding="latin1", decimal=".")


        #Distanzen hinzufügen
        df_distmatrix = pd.read_csv(r"../00_Resources/Matrices/TK_distmatrix_eukl_"+str(min_freq)+"-"+str(var_gew)+"-"+str(var_freq)+".csv", sep=";",
                    encoding="latin1", decimal=".")
        df_instance["Distanz"] = df_distmatrix.loc[0].values[1:]
        print(df_instance["Distanz"])

        #Fahrzeiten hinzufügen
        df_durmatrix = pd.read_csv(r"../00_Resources/Matrices/TK_durmatrix_"+str(min_freq)+"-" +str(var_gew)+"-"+str(var_freq)+".csv", sep=";",
                    encoding="latin1", decimal=".")
        df_instance["Dauer"] = df_durmatrix.loc[0].values[1:]
        print(df_instance["Dauer"])


    # Add AF Costs
    if tarif_matrix == True:
        df_Tarifmatrix_long = pd.read_csv(
            r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Transportpreismatrix_TK_long.csv",
            encoding="latin-1",
            sep=";", dtype={"Gewicht": float, "Distanz": float})
        df_instance = add_freightcosts(df_instance, df_Tarifmatrix_long, "AF_Kosten")
    else:
        df_instance["AF_Kosten"] = df_instance["avg_Gewicht"] * preis_tonne/1000 + preis_basis

    print(df_instance)

    df_instance.to_csv(r"../00_Resources/Instances/MR_Instance_Nodes/MR_Instance_Nodes"+str(min_freq)+"_"+str(var_gew)+"_"+str(var_freq)+".csv", sep=";",
                encoding="latin1", decimal=".")