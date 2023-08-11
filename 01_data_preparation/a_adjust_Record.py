import pandas as pd
import numpy as np
import textdistance as td
import requests
import json
import re
import roman

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
    korrekturliste = pd.read_csv(r"../00_Resources/Grunddaten/Adressenkorrektur.csv", encoding="latin-1", sep=";")
    for index, row in korrekturliste.iterrows():
        df.loc[df["Straße_Empfänger"] == row["Straße_Empfänger_falsch"], "Straße_Empfänger"] = row["Straße_Empfänger_richtig"].upper()
    return df

def correct_streetnames(df):
    df["Empf. Straße"] = df["Empf. Straße"].str.upper()
    df["Empf. Ort"] = df["Empf. Ort"].str.upper()
    df = df[df["Straße_Empfänger"] != "#"]
    df = df[df["Straße_Empfänger"] != "32"]
    df = df[df["Straße_Empfänger"] != 32]
    df = df[df["Straße_Empfänger"] != "."]
    df = df[df["Stadt_Empfänger"] != "."]

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

def check_ID_liste_dublicate(df):
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

def change_ID_Empfänger(ID_liste, df):
    for index, row in ID_liste.iterrows():
        df.loc[(df.Straße_Empfänger == row["Straße_Empfänger"]) & (df.PLZ_Empfänger == row["PLZ_Empfänger"]), 'ID_Empfänger'] = row["ID_Empfänger"]
    return df



def split_IDs(df):
    ID_split_list = pd.read_csv(r"../00_Resources/Grunddaten/Grunddaten/ID_split_Namen.csv",
                              encoding="latin-1", sep=";")
    ID_max = df["ID_Empfänger"].max()
    for index, row in ID_split_list.iterrows():
        df.loc[(df.Name_Empfänger == row["Name_Empfänger"]) & (
                    df.Straße_Empfänger == row["Straße_Empfänger"]), 'ID_Empfänger'] = ID_max + row["ID_Ergänzug"]
        if row["Name_Empfänger_2"] != None:
            df.loc[(df.Name_Empfänger == row["Name_Empfänger_2"]) & (
                    df.Straße_Empfänger == row["Straße_Empfänger"]), 'ID_Empfänger'] = ID_max + row["ID_Ergänzug"]

    return df

def add_Empfänger_Namen(ID_liste, df):
    namen_array =[]

    for index, row in ID_liste.iterrows():
        df_filtered = df.loc[(df["ID_Empfänger"] == row["ID_Empfänger"])]
        namen_array.append(df_filtered["Name_Empfänger"].drop_duplicates().values)
        #print(df_filtered["Name_Empfänger"].drop_duplicates().values)

    ID_liste["Name_Empfänger"] = namen_array
    return ID_liste





def calc_period(df_touren):
    df_touren["Beladedatum"] = pd.to_datetime(df_touren["Beladedatum"], dayfirst=True)

    time_from = df_touren.loc[1, "Beladedatum"]
    perioden_array = []
    for index, row in df_touren.iterrows():
        perioden_array.append(pd.Timedelta(row["Beladedatum"] - time_from).days)
    df_touren["Periode"] = perioden_array
    return df_touren

# Splits Street number and House number
def split_street_and_number(s):
    parts = s.split()
    Haus = ""
    Straße = ""
    for part in parts:
        if any(char.isdigit() for char in part):
            Haus += part + " "
        else:
            Straße += part + " "
    Haus.strip()
    Straße.strip()
    return pd.Series([Straße, Haus])

# Removes "AM" and "IM" Prefixes
def remove_prefix(row):
    return re.sub(r'^(AM|IM)\s+', '', row['Straße_Empfänger'])


# Replaces Roman numerals with integers (II LEEGMOORWEG with 2 LEEGMOORWEG  )
def replace_roman_numerals(value):
    match = re.match(r'^(I{1,3})(\.?)\s+', value)
    if match:
        roman_numeral = match.group(1)
        point = match.group(2)
        return value.replace(roman_numeral + point, str(roman.fromRoman(roman_numeral)) + point)
    else:
        return value

# Replaces dash with space
def replace_dash_with_space(row):
    return row['Straße_Empfänger'].replace('-', ' ')

# Splits the Stadt_Empfänger column on '/' and keeps the value before slash
def split_on_slash(row):
    split_df = row['Stadt_Empfänger'].split('/', 1)
    return split_df[0]

# Splits the Haus_Empfänger column on '-' or '+', and keeps the first part before the '-' or '+'
def split_on_dash_or_plus(row):
    split_result = re.split(r'[-+]', row['Haus_Empfänger'])
    return split_result[0]

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


def pre_process(rohdaten):
    # Split Street and House number
    rohdaten[['Straße_Empfänger', 'Haus_Empfänger']] = rohdaten['Straße_Empfänger'].apply(split_street_and_number)
    # Remove "AM" and "IM" Prefixes
    rohdaten['Straße_Empfänger'] = rohdaten.apply(remove_prefix, axis=1)
    # Replace Roman numerals with integers (II LEEGMOORWEG with 2 LEEGMOORWEG  )
    rohdaten['Straße_Empfänger'] = rohdaten['Straße_Empfänger'].apply(replace_roman_numerals)
    # Replace dash with space in Straße_Empfänger
    rohdaten['Straße_Empfänger'] = rohdaten.apply(replace_dash_with_space, axis=1)
    # Split the Stadt_Empfänger column on '/'
    rohdaten['Stadt_Empfänger'] = rohdaten.apply(split_on_slash, axis=1)
    # Split the Haus_Empfänger column on '-' or '+', and keep the first part before the '-' or '+'
    rohdaten['Haus_Empfänger'] = rohdaten.apply(split_on_dash_or_plus, axis=1)
    # Save updated file as "Pre-Processed-data.csv"
    rohdaten.to_csv(path_or_buf=r"../00_Resources/Grunddaten/preprocessed_data.csv", sep=";", encoding="latin1",
                    decimal=".", index=False)
    return rohdaten
def round_sort_coordinates_original(file_path):
    with open(file_path) as f:
        locations = json.load(f)
    return locations

if __name__ == "__main__":
    # Load the file rohdaten
    #rohdaten = pd.read_csv(r"../00_Resources/Rohdaten.csv", encoding="latin_1", sep=";", decimal=',')

    # Replace 'GROSSENKETEN' with 'GROSSENKNETEN' in the Stadt_Empfänger column (Exact Change in Street One name)
    #rohdaten['Stadt_Empfänger'] = rohdaten['Stadt_Empfänger'].replace('GROSSENKETEN', 'GROSSENKNETEN')
    # Replace '4824' with '04824' in the PLZ_Empfänger column (Exact change in one Postal Code)
    #rohdaten['PLZ_Empfänger'] = rohdaten['PLZ_Empfänger'].replace('4824 ', '04824 ')
    # pre-process the data
    #data_processed = pre_process(rohdaten)
    transport_preis = pd.read_csv(r"../00_Resources/Transportpreismatrix_TK.csv", encoding="latin_1", sep=";", decimal=',')
    data_processed = pd.read_csv(r"../00_Resources/Grunddaten/preprocessed_data1.csv", encoding="latin_1", sep=";", decimal=',')
    # add coordinates
    df_added_coordinates, list_coordinates = add_coordinates(data_processed)
    # Calculate distance matrices
    distances, durations, euclidean, distance_table, df_added_distances = create_distance_matrices(df_added_coordinates, list_coordinates, chunk_size=100)
    # Calculate Freight Cost
    df_added_freightcost = add_costs(df_added_distances, transport_preis, 'Frachtkosten')
    # Shipments and weight per week per ID_recipient
    df_frequency, df_weight = evaluation_after_KW1(df_added_freightcost)
    # Variability analysis
    df_var_evaluation = variability_evaluation(df_frequency, df_weight, df_added_freightcost)

    # Apply Profiles
    var_weight = 1.33
    var_frequency = 1.33
    min_frequency = 0.5
    save_path_special = "var_gewicht" + str(var_weight) + "_var_frequenz" + str(
            var_frequency) + "_mindest_frequenz" + str(min_frequency)
    # Setting up the path to files
    save_path_base = r"../00_Resources/profile_results"
    df_assigned_pattern = pattern_assignment(df_var_evaluation, var_weight, var_frequency, min_frequency,save_path_base, save_path_special)
    df_assigned_profile = profile_application(df_added_freightcost, df_assigned_pattern)
    df_recal_freightcost= recalulate_costs(df_assigned_profile, transport_preis, 'Frachtkosten')







