import pandas as pd
import numpy as np
import textdistance as td
import requests

def change_Columnname(df):
    df = df.rename(columns= {"ERP - Transport": "Transport",
                             "Abf.datum": "Beladedatum",
                             "Fahrzeug ID": "Fahrzeugart",
                             "Nutzlast":  "Fahrzeugkapazität",
                             "Abs. Name": "Name_Absender",
                             "Abs. Straße": "Straße_Absender",
                             "Abs Lnd.": "Land_Absender",
                             "Abs. Plz": "PLZ_Absender",
                             "Abs. Ort": "Stadt_Absender",
                             "Empf.-ID": "ID_Empfänger",
                             "Empf. Name": "Name_Empfänger",
                             "Kundenkategorie": "Kategorisierung",
                             "Empf. Straße": "Straße_Empfänger",
                             "Empf. Lnd": "Land_Empfänger",
                             "Empf. Plz": "PLZ_Empfänger",
                             "Empf. Ort": "Stadt_Empfänger",
                             "Anz. Lief.": "Anzahl_Lieferungen",
                             "Stopps": "Stopps",
                             "HU - Gewicht": "Gewicht",
                             "Distanz Abschnitt" :"Distanz",
                             "Frachtkosten":  "Frachtkosten",
                             })
    return df

def change_streetnames_by_hand(df):
    korrekturliste = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Grunddaten\Adressenkorrektur.csv", encoding="latin-1", sep=";")
    for index, row in korrekturliste.iterrows():
        df.loc[df["Straße_Empfänger"] == row["Straße_Empfänger_falsch"], "Straße_Empfänger"] = row["Straße_Empfänger_richtig"].upper()
    return df

def correct_streetnames(df):
    street_array = []
    for i in df["Straße_Empfänger"]:
        hausnummerzusatz = ["A","B","C","D","E","F","G","H","a","b","c","d","e","f","g","h"]
        split_hausnummer = i.split(" ")
        zusatz = split_hausnummer[-1]
        if (zusatz in hausnummerzusatz):
            zusatz = zusatz.upper()
            if len(zusatz) == 1:
                pos_string = hausnummerzusatz.index(zusatz)
                i = i.replace(" "+str(zusatz), hausnummerzusatz[pos_string])

        i = i.replace("/","-")
        i = i.replace(" - ","-")
        i = i.replace("- ", "-")
        i = i.replace(" -", "-")
        i = i.replace(",",".")

        i = i.replace("STRAßE", "STRASSE")
        if ("STR." in i) & ("STRASSE" not in i):
            i = i.replace("STR.", "STRASSE")
        if ("STR " in i) & ("STRASSE" not in i):
            i = i.replace("STR ", "STRASSE ")
        i = i.replace("  ", " ")



        street_array.append(i)
    #print(street_array)
    df["Straße_Empfänger"] = street_array

    return df

def check_adressenliste_dublicate(df):
    df_filtered_rare = df[df["Anzahl_ID_Empfänger"]<=9000]
    PLZ_array = []
    Straße_Empfänger_array_0 = []
    Straße_Empfänger_array_1 = []

    Name_Empfänger_array_0 =[]
    Name_Empfänger_array_1=[]

    Straße_Levenshtein_distance_array_norm =[]
    Straße_Levenshtein_distance_array_abs = []
    Name_Levenshtein_distance_array_norm = []
    Name_Levenshtein_distance_array_abs = []
    ID_Empfänger_0 = []
    ID_Empfänger_1 = []
    Anzahl_Sendungen_array_0 = []
    Anzahl_Sendungen_array_1 = []

    for index_rare, row_rare in df_filtered_rare.iterrows():
        df_filtered_PLZ = df[df["PLZ_Empfänger"] == row_rare["PLZ_Empfänger"]]
        for index_df, row_df in df_filtered_PLZ.iterrows():
            PLZ_array.append(row_rare["PLZ_Empfänger"])
            ID_Empfänger_0.append(row_rare["ID_Empfänger"])
            ID_Empfänger_1.append(row_rare["ID_Empfänger"])

            Anzahl_Sendungen_array_0.append(row_rare["Anzahl_ID_Empfänger"])
            Anzahl_Sendungen_array_1.append(row_df["Anzahl_ID_Empfänger"])

            Straße_Empfänger_array_0.append(row_rare["Straße_Empfänger"])
            Straße_Empfänger_array_1.append(row_df["Straße_Empfänger"])
            Straße_Levenshtein_distance_array_norm.append(td.levenshtein.normalized_distance(row_rare["Straße_Empfänger"],row_df["Straße_Empfänger"]))
            Straße_Levenshtein_distance_array_abs.append(td.levenshtein(row_rare["Straße_Empfänger"], row_df["Straße_Empfänger"]))

            Name_Levenshtein_distance_array_hilfe_norm= []
            Name_Levenshtein_distance_array_hilfe_abs = []
            for name_0 in row_rare["Name_Empfänger"]:
                for name_1 in row_df["Name_Empfänger"]:
                    Name_Levenshtein_distance_array_hilfe_norm.append(td.levenshtein.normalized_distance(name_0,name_1))
                    Name_Levenshtein_distance_array_hilfe_abs.append(td.levenshtein(name_0, name_1))


            Name_Levenshtein_distance_array_norm.append(min(Name_Levenshtein_distance_array_hilfe_norm))
            Name_Levenshtein_distance_array_abs.append(min(Name_Levenshtein_distance_array_hilfe_abs))

            Name_Empfänger_array_0.append(row_rare["Name_Empfänger"])
            Name_Empfänger_array_1.append(row_df["Name_Empfänger"])

    data = {"PLZ_Empfänger": PLZ_array,"Straße_Empfänger_0": Straße_Empfänger_array_0, "Straße_Empfänger_1": Straße_Empfänger_array_1,"Name_Empfänger_0": Name_Empfänger_array_0,"Name_Empfänger_1":Name_Empfänger_array_1, "Straße_Levenshteindistanz_norm": Straße_Levenshtein_distance_array_norm, "Name_Levenshteindistanz_norm": Name_Levenshtein_distance_array_norm,"Straße_Levenshteindistanz_abs": Straße_Levenshtein_distance_array_abs, "Name_Levenshteindistanz_abs": Name_Levenshtein_distance_array_abs, "Anzahl_Sendungen_0": Anzahl_Sendungen_array_0, "Anzahl_Sendungen_1": Anzahl_Sendungen_array_1}
    df_Levenshteindistance = pd.DataFrame(data= data)
    df_Levenshteindistance = df_Levenshteindistance.sort_values(["PLZ_Empfänger","Anzahl_Sendungen_0","Straße_Empfänger_0","Anzahl_Sendungen_1"],ascending=[True, False, False, False])
    #df_Levenshteindistance = df_Levenshteindistance[((df_Levenshteindistance["Name_Levenshteindistanz_norm"]<=0.25)& (df_Levenshteindistance["Straße_Levenshteindistanz_norm"]<=0.25)& (df_Levenshteindistance["Straße_Levenshteindistanz_norm"]!=0))| ((df_Levenshteindistance["Name_Levenshteindistanz_abs"]<=5)& (df_Levenshteindistance["Straße_Levenshteindistanz_abs"]<=5)& (df_Levenshteindistance["Straße_Levenshteindistanz_abs"]!=0))]
    df_Levenshteindistance = df_Levenshteindistance[((((df_Levenshteindistance["Name_Levenshteindistanz_norm"]<=0.25)|(df_Levenshteindistance["Name_Levenshteindistanz_abs"]<=4))&
                                                      ((df_Levenshteindistance["Straße_Levenshteindistanz_norm"]<=0.25)| (df_Levenshteindistance["Straße_Levenshteindistanz_abs"]<=4)))
                                                      & (df_Levenshteindistance["Straße_Levenshteindistanz_norm"]!=0) & ((df_Levenshteindistance["Anzahl_Sendungen_0"]<=5)|(df_Levenshteindistance["Anzahl_Sendungen_1"]<=5)))]

    return df_Levenshteindistance

def adjust_streetnames_in_PLZ(df,df_Levenshteindistance):
    for index, row in df_Levenshteindistance.iterrows():
        if row["Anzahl_Sendungen_0"] >= row["Anzahl_Sendungen_1"]:
            df.loc[(df["PLZ_Empfänger"] == row["PLZ_Empfänger"])& (df["Straße_Empfänger"]== row["Straße_Empfänger_0"]),"Straße_Empfänger"] = row["Straße_Empfänger_0"]
        if row["Anzahl_Sendungen_0"]< row["Anzahl_Sendungen_1"]:
            df.loc[(df["PLZ_Empfänger"] == row["PLZ_Empfänger"]) & (df["Straße_Empfänger"] == row["Straße_Empfänger_1"]), "Straße_Empfänger"] = row["Straße_Empfänger_1"]
    return df

def change_ID_Empfänger(adressenliste, df):
    for index, row in adressenliste.iterrows():
        df.loc[(df.Straße_Empfänger == row["Straße_Empfänger"]) & (df.PLZ_Empfänger == row["PLZ_Empfänger"]), 'ID_Empfänger'] = row["ID_Empfänger"]
    return df


def change_Kategorisierung(adressenliste, df):
    for index, row in df.iterrows():
        try:
            df.loc[(df.ID_Empfänger == row["ID_Empfänger"]), 'Kategorisierung'] = df[df["ID_Empfänger"]== row["ID_Empfänger"]]["alte_Kategorisierung"].mode()[0]
        except IndexError:
            print("nichts")
    return df

def split_IDs(df):
    ID_split_list = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Grunddaten\ID_split_Namen.csv",
                              encoding="latin-1", sep=";")
    ID_max = df["ID_Empfänger"].max()
    for index, row in ID_split_list.iterrows():
        df.loc[(df.Name_Empfänger == row["Name_Empfänger"]) & (
                    df.Straße_Empfänger == row["Straße_Empfänger"]), 'ID_Empfänger'] = ID_max + row["ID_Ergänzug"]
        if row["Name_Empfänger_2"] != None:
            df.loc[(df.Name_Empfänger == row["Name_Empfänger_2"]) & (
                    df.Straße_Empfänger == row["Straße_Empfänger"]), 'ID_Empfänger'] = ID_max + row["ID_Ergänzug"]

    return df

def add_Empfänger_Namen(adressenliste, df):
    namen_array =[]

    for index, row in adressenliste.iterrows():
        df_filtered = df.loc[(df["ID_Empfänger"] == row["ID_Empfänger"])]
        namen_array.append(df_filtered["Name_Empfänger"].drop_duplicates().values)
        #print(df_filtered["Name_Empfänger"].drop_duplicates().values)

    adressenliste["Name_Empfänger"] = namen_array
    return adressenliste

def add_Empfänger_Kategorie(adressenliste, df):
    Kat_array =[]

    for index, row in adressenliste.iterrows():
        df_filtered = df.loc[(df["ID_Empfänger"] == row["ID_Empfänger"])]
        Kat_array.append(df_filtered.mode()["Kategorisierung"][0])

    adressenliste["Kategorisierung"] = Kat_array
    return adressenliste


def add_Koordinaten(raw_list):

    def get_geolocation(PLZ, Straße):
        base_url = 'https://nominatim.openstreetmap.org/search?'
        query = 'postalcode=' + str(PLZ) + "&" + "street=" + Straße

        output_spec = 'format=json&addressdetails=0'
        search_params = query + '&' + output_spec
        request_url = base_url + search_params
        print(Straße)
        print(PLZ)
        try:
            response_dict = requests.get(request_url).json()[0]
            return response_dict['lat'], response_dict['lon']
        except IndexError:
            return "nicht gefunden", "nicht gefunden"

    lat_array = []
    lon_array = []

    for index, row in raw_list.iterrows():
        street = row["Straße_Empfänger"]
        PLZ = row["PLZ_Empfänger"]

        lat, lon = get_geolocation(str(PLZ), street)

        lat_array.append(lat)
        lon_array.append(lon)

    raw_list["lat"] = lat_array
    raw_list["lon"] = lon_array

    #df_touren.loc[:, "lat":] = df_touren.loc[:, "lat":].apply(pd.to_numeric)
    return raw_list

def add_coordinates(df_touren,coordinates_list):
    #print(coordinates_list.dtypes)
    #coordinates_list = coordinates_list.astype({"lat": float, "lon": float})
    coordinates_list = coordinates_list.set_index("ID_Empfänger")
    lat_array_empfänger = []
    lon_array_empfänger = []
    lat_array_absender = []
    lon_array_absender = []

    for index, row in df_touren.iterrows():
        print(row["ID_Empfänger"])
        lat_array_empfänger.append(coordinates_list.loc[row["ID_Empfänger"], "lat"])
        lon_array_empfänger.append(coordinates_list.loc[row["ID_Empfänger"], "lon"])
        lat_array_absender.append(53.12433928160658)
        lon_array_absender.append(9.337199734018563)

    df_touren["empfaenger_lon"] = lon_array_empfänger
    df_touren["empfaenger_lat"] = lat_array_empfänger
    df_touren["versandzentrum_lon"] = lon_array_absender
    df_touren["versandzentrum_lat"] = lat_array_absender

    return df_touren

def calc_period(df_touren):
    df_touren["Beladedatum"] = pd.to_datetime(df_touren["Beladedatum"], dayfirst=True)

    time_from = df_touren.loc[1, "Beladedatum"]
    perioden_array = []
    for index, row in df_touren.iterrows():
        perioden_array.append(pd.Timedelta(row["Beladedatum"] - time_from).days)
    df_touren["Periode"] = perioden_array
    return df_touren

if __name__ == "__main__":
    df_rohdaten = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Grunddaten\Rohdaten_TK.csv", encoding="latin-1", sep=";", dtype={"Empf. Plz": object, "Empf. Straße": object})

    df_rohdaten["Kundenkategorie"] = df_rohdaten["Kundenkategorie"].str.upper()
    df_rohdaten["Empf. Straße"] = df_rohdaten["Empf. Straße"].str.upper()
    df_rohdaten["Empf. Ort"] = df_rohdaten["Empf. Ort"].str.upper()

    df_rohdaten["alte_ID_Empfänger"] = df_rohdaten["Empf.-ID"]
    df_rohdaten["alte_Kategorisierung"] = df_rohdaten["Kundenkategorie"]
    df_rohdaten["alte_Straße_Empfänger"] = df_rohdaten["Empf. Straße"]

    df_rohdaten = change_Columnname(df_rohdaten)

    df_rohdaten = df_rohdaten[df_rohdaten["Straße_Empfänger"] != "#"]
    df_rohdaten = df_rohdaten[df_rohdaten["Straße_Empfänger"] != "32"]
    df_rohdaten = df_rohdaten[df_rohdaten["Straße_Empfänger"] != 32]
    df_rohdaten = df_rohdaten[df_rohdaten["Straße_Empfänger"] != "."]
    df_rohdaten = df_rohdaten[df_rohdaten["Stadt_Empfänger"] != "."]

    df_rohdaten = correct_streetnames(df_rohdaten)

    df_rohdaten = change_streetnames_by_hand(df_rohdaten)
    df_rohdaten["Straße_Empfänger"] = df_rohdaten["Straße_Empfänger"].str.upper()

    # Dressenliste ersten mit neuen IDs pro Lieferort
    adressenliste = df_rohdaten[["Straße_Empfänger","PLZ_Empfänger", "Stadt_Empfänger"]].drop_duplicates(keep= "last",subset=["Straße_Empfänger","PLZ_Empfänger"]).reset_index(drop=True)
    adressenliste.index = adressenliste.index +1
    adressenliste = adressenliste.reset_index().rename(columns= {"index":"ID_Empfänger"})

    # Neue ID zuordnen
    df_rohdaten = change_ID_Empfänger(adressenliste, df_rohdaten)

    adressenliste = add_Empfänger_Namen(adressenliste, df_rohdaten)

    adressenliste["Anzahl_ID_Empfänger"] = df_rohdaten.groupby("ID_Empfänger").agg("count")["Transport"].values
    adressenliste.to_csv(path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Adressenliste.csv",
                    sep=";", encoding="latin1", decimal=".")

    # Gleiche IDs zusammenführen
    df_Levenshteindistance = check_adressenliste_dublicate(adressenliste)
    df_Levenshteindistance.to_csv(
        path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Adressenliste_Levenshteindistance.csv",
        sep=";", encoding="latin1", decimal=".")

    df_rohdaten = adjust_streetnames_in_PLZ(df_rohdaten,df_Levenshteindistance)

    # ID Liste erstellen
    ID_liste = df_rohdaten[["Straße_Empfänger","PLZ_Empfänger", "Stadt_Empfänger"]].drop_duplicates(keep= "last",subset=["Straße_Empfänger","PLZ_Empfänger"]).reset_index(drop=True)
    ID_liste.index = ID_liste.index +1
    ID_liste = ID_liste.reset_index().rename(columns= {"index":"ID_Empfänger"})
    ID_liste = add_Empfänger_Namen(ID_liste,df_rohdaten)
    #ID_liste = add_Empfänger_Kategorie(ID_liste, df_rohdaten)
    #ID_liste = add_Koordinaten(ID_liste)

    #ID_liste.to_csv(path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\ID_liste_no_split.csv",
    #               sep=";", encoding="latin1", decimal=".")
    ID_liste = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\ID_liste_no_split.csv",
                                  encoding="latin_1", sep=";", dtype={"lat": float, "lon": float})

    df_rohdaten = add_coordinates(df_rohdaten,ID_liste) # Koordinaten hinzufügen

    df_rohdaten = calc_period(df_rohdaten) #Periode hinzufügen
    df_rohdaten["ID_Sendung"] = df_rohdaten.index #ID_Sendung hinzufügen

    ID_liste = ID_liste.reset_index()
    df_rohdaten = split_IDs(df_rohdaten) # neue IDs Übertragen
    df_rohdaten = change_Kategorisierung(ID_liste, df_rohdaten) # häufigste Kategorisierung für Kunden übernehmen

    ID_liste = df_rohdaten[["ID_Empfänger", "Kategorisierung","Straße_Empfänger","PLZ_Empfänger", "Stadt_Empfänger", "empfaenger_lon", "empfaenger_lat"]].drop_duplicates(keep= "last",subset=["ID_Empfänger","Straße_Empfänger","PLZ_Empfänger"]).reset_index(drop=True)
    ID_liste = ID_liste.rename(columns= {"empfaenger_lon": "lon","empfaenger_lat":"lat"})
    ID_liste = add_Empfänger_Namen(ID_liste, df_rohdaten)
    ID_liste = add_Empfänger_Kategorie(ID_liste, df_rohdaten)

    ID_liste.to_csv(path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\ID_liste.csv",
                   sep=";", encoding="latin1", decimal=".")

    df_rohdaten.to_csv(path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Datensatz_TK_bereinigt.csv",
                       sep=";", encoding="latin1", decimal=".")