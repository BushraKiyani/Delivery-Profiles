import pandas as pd
import textdistance as td
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
