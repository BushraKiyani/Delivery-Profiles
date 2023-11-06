import pandas as pd
import textdistance as td
import re
import roman

def change_Columnname(df):
    df = df.rename(columns= {"ERP - Transport": "Transport",
                             "Abf.datum": "Loading_Date",
                             "Fahrzeug ID": "Fahrzeugart",
                             "Nutzlast":  "Fahrzeugkapazität",
                             "Abs. Name": "Name_Absender",
                             "Abs. Straße": "Sender_Street",
                             "Abs Lnd.": "Land_Absender",
                             "Abs. Plz": "Sender_Postal_Code",
                             "Abs. Ort": "Stadt_Absender",
                             "Empf.-ID": "Recipient_ID",
                             "Empf. Name": "Name_Empfänger",
                             "Empf. Straße": "Recipient_Street",
                             "Empf. Lnd": "Land_Empfänger",
                             "Empf. Plz": "Recipient_Postal_Code",
                             "Empf. Ort": "Recipient_City",
                             "Anz. Lief.": "Anzahl_Lieferungen",
                             "Stopps": "Stopps",
                             "HU - Weight": "Weight",
                             "Distanz Abschnitt" :"Distanz",
                             "Freight_Cost":  "Freight_Cost",
                             })
    return df

def change_streetnames_by_hand(df):
    korrekturliste = pd.read_csv(r"../00_Resources/Basic_Data/Adressenkorrektur.csv", encoding="latin-1", sep=";")
    for index, row in korrekturliste.iterrows():
        df.loc[df["Recipient_Street"] == row["Recipient_Street_falsch"], "Recipient_Street"] = row["Recipient_Street_richtig"].upper()
    return df

def correct_streetnames(df):
    df["Empf. Straße"] = df["Empf. Straße"].str.upper()
    df["Empf. Ort"] = df["Empf. Ort"].str.upper()
    df = df[df["Recipient_Street"] != "#"]
    df = df[df["Recipient_Street"] != "32"]
    df = df[df["Recipient_Street"] != 32]
    df = df[df["Recipient_Street"] != "."]
    df = df[df["Recipient_City"] != "."]

    street_array = []
    for i in df["Recipient_Street"]:
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
    df["Recipient_Street"] = street_array

    return df

def check_ID_liste_dublicate(df):
    df_filtered_rare = df[df["Anzahl_Recipient_ID"]<=9000]
    PLZ_array = []
    Recipient_Street_array_0 = []
    Recipient_Street_array_1 = []

    Name_Empfänger_array_0 =[]
    Name_Empfänger_array_1=[]

    Straße_Levenshtein_distance_array_norm =[]
    Straße_Levenshtein_distance_array_abs = []
    Name_Levenshtein_distance_array_norm = []
    Name_Levenshtein_distance_array_abs = []
    Recipient_ID_0 = []
    Recipient_ID_1 = []
    Anzahl_Shipments_array_0 = []
    Anzahl_Shipments_array_1 = []

    for index_rare, row_rare in df_filtered_rare.iterrows():
        df_filtered_PLZ = df[df["Recipient_Postal_Code"] == row_rare["Recipient_Postal_Code"]]
        for index_df, row_df in df_filtered_PLZ.iterrows():
            PLZ_array.append(row_rare["Recipient_Postal_Code"])
            Recipient_ID_0.append(row_rare["Recipient_ID"])
            Recipient_ID_1.append(row_rare["Recipient_ID"])

            Anzahl_Shipments_array_0.append(row_rare["Anzahl_Recipient_ID"])
            Anzahl_Shipments_array_1.append(row_df["Anzahl_Recipient_ID"])

            Recipient_Street_array_0.append(row_rare["Recipient_Street"])
            Recipient_Street_array_1.append(row_df["Recipient_Street"])
            Straße_Levenshtein_distance_array_norm.append(td.levenshtein.normalized_distance(row_rare["Recipient_Street"],row_df["Recipient_Street"]))
            Straße_Levenshtein_distance_array_abs.append(td.levenshtein(row_rare["Recipient_Street"], row_df["Recipient_Street"]))

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

    data = {"Recipient_Postal_Code": PLZ_array,"Recipient_Street_0": Recipient_Street_array_0, "Recipient_Street_1": Recipient_Street_array_1,"Name_Empfänger_0": Name_Empfänger_array_0,"Name_Empfänger_1":Name_Empfänger_array_1, "Straße_Levenshteindistanz_norm": Straße_Levenshtein_distance_array_norm, "Name_Levenshteindistanz_norm": Name_Levenshtein_distance_array_norm,"Straße_Levenshteindistanz_abs": Straße_Levenshtein_distance_array_abs, "Name_Levenshteindistanz_abs": Name_Levenshtein_distance_array_abs, "Anzahl_Shipments_0": Anzahl_Shipments_array_0, "Anzahl_Shipments_1": Anzahl_Shipments_array_1}
    df_Levenshteindistance = pd.DataFrame(data= data)
    df_Levenshteindistance = df_Levenshteindistance.sort_values(["Recipient_Postal_Code","Anzahl_Shipments_0","Recipient_Street_0","Anzahl_Shipments_1"],ascending=[True, False, False, False])
    #df_Levenshteindistance = df_Levenshteindistance[((df_Levenshteindistance["Name_Levenshteindistanz_norm"]<=0.25)& (df_Levenshteindistance["Straße_Levenshteindistanz_norm"]<=0.25)& (df_Levenshteindistance["Straße_Levenshteindistanz_norm"]!=0))| ((df_Levenshteindistance["Name_Levenshteindistanz_abs"]<=5)& (df_Levenshteindistance["Straße_Levenshteindistanz_abs"]<=5)& (df_Levenshteindistance["Straße_Levenshteindistanz_abs"]!=0))]
    df_Levenshteindistance = df_Levenshteindistance[((((df_Levenshteindistance["Name_Levenshteindistanz_norm"]<=0.25)|(df_Levenshteindistance["Name_Levenshteindistanz_abs"]<=4))&
                                                      ((df_Levenshteindistance["Straße_Levenshteindistanz_norm"]<=0.25)| (df_Levenshteindistance["Straße_Levenshteindistanz_abs"]<=4)))
                                                      & (df_Levenshteindistance["Straße_Levenshteindistanz_norm"]!=0) & ((df_Levenshteindistance["Anzahl_Shipments_0"]<=5)|(df_Levenshteindistance["Anzahl_Shipments_1"]<=5)))]

    return df_Levenshteindistance

def adjust_streetnames_in_PLZ(df,df_Levenshteindistance):
    for index, row in df_Levenshteindistance.iterrows():
        if row["Anzahl_Shipments_0"] >= row["Anzahl_Shipments_1"]:
            df.loc[(df["Recipient_Postal_Code"] == row["Recipient_Postal_Code"])& (df["Recipient_Street"]== row["Recipient_Street_0"]),"Recipient_Street"] = row["Recipient_Street_0"]
        if row["Anzahl_Shipments_0"]< row["Anzahl_Shipments_1"]:
            df.loc[(df["Recipient_Postal_Code"] == row["Recipient_Postal_Code"]) & (df["Recipient_Street"] == row["Recipient_Street_1"]), "Recipient_Street"] = row["Recipient_Street_1"]
    return df

def change_Recipient_ID(ID_liste, df):
    for index, row in ID_liste.iterrows():
        df.loc[(df.Recipient_Street == row["Recipient_Street"]) & (df.Recipient_Postal_Code == row["Recipient_Postal_Code"]), 'Recipient_ID'] = row["Recipient_ID"]
    return df



def split_IDs(df):
    ID_split_list = pd.read_csv(r"../00_Resources/Basic_Data/Basic_Data/ID_split_Namen.csv",
                              encoding="latin-1", sep=";")
    ID_max = df["Recipient_ID"].max()
    for index, row in ID_split_list.iterrows():
        df.loc[(df.Name_Empfänger == row["Name_Empfänger"]) & (
                    df.Recipient_Street == row["Recipient_Street"]), 'Recipient_ID'] = ID_max + row["ID_Ergänzug"]
        if row["Name_Empfänger_2"] != None:
            df.loc[(df.Name_Empfänger == row["Name_Empfänger_2"]) & (
                    df.Recipient_Street == row["Recipient_Street"]), 'Recipient_ID'] = ID_max + row["ID_Ergänzug"]

    return df

def add_Empfänger_Namen(ID_liste, df):
    namen_array =[]

    for index, row in ID_liste.iterrows():
        df_filtered = df.loc[(df["Recipient_ID"] == row["Recipient_ID"])]
        namen_array.append(df_filtered["Name_Empfänger"].drop_duplicates().values)
        #print(df_filtered["Name_Empfänger"].drop_duplicates().values)

    ID_liste["Name_Empfänger"] = namen_array
    return ID_liste


def calc_period(df_touren):
    df_touren["Loading_Date"] = pd.to_datetime(df_touren["Loading_Date"], dayfirst=True)

    time_from = df_touren.loc[1, "Loading_Date"]
    perioden_array = []
    for index, row in df_touren.iterrows():
        perioden_array.append(pd.Timedelta(row["Loading_Date"] - time_from).days)
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
    return re.sub(r'^(AM|IM)\s+', '', row['Recipient_Street'])


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
    return row['Recipient_Street'].replace('-', ' ')

# Splits the Recipient_City column on '/' and keeps the value before slash
def split_on_slash(row):
    split_df = row['Recipient_City'].split('/', 1)
    return split_df[0]

# Splits the Recipient_House_No column on '-' or '+', and keeps the first part before the '-' or '+'
def split_on_dash_or_plus(row):
    split_result = re.split(r'[-+]', row['Recipient_House_No'])
    return split_result[0]

def pre_process(rohData):
    # Split Street and House number
    rohData[['Recipient_Street', 'Recipient_House_No']] = rohData['Recipient_Street'].apply(split_street_and_number)
    # Remove "AM" and "IM" Prefixes
    rohData['Recipient_Street'] = rohData.apply(remove_prefix, axis=1)
    # Replace Roman numerals with integers (II LEEGMOORWEG with 2 LEEGMOORWEG  )
    rohData['Recipient_Street'] = rohData['Recipient_Street'].apply(replace_roman_numerals)
    # Replace dash with space in Recipient_Street
    rohData['Recipient_Street'] = rohData.apply(replace_dash_with_space, axis=1)
    # Split the Recipient_City column on '/'
    rohData['Recipient_City'] = rohData.apply(split_on_slash, axis=1)
    # Split the Recipient_House_No column on '-' or '+', and keep the first part before the '-' or '+'
    rohData['Recipient_House_No'] = rohData.apply(split_on_dash_or_plus, axis=1)
    # Save updated file as "Pre-Processed-data.csv"
    rohData.to_csv(path_or_buf=r"../00_Resources/Basic_Data/preprocessed_data.csv", sep=";", encoding="latin1",
                    decimal=".", index=False)
    return rohData
if __name__ == "__main__":
    # Load the file rohData
    #rohData = pd.read_csv(r"../00_Resources/RohData.csv", encoding="latin_1", sep=";", decimal=',')

    # Replace 'GROSSENKETEN' with 'GROSSENKNETEN' in the Recipient_City column (Exact Change in Street One name)
    #rohData['Recipient_City'] = rohData['Recipient_City'].replace('GROSSENKETEN', 'GROSSENKNETEN')
    # Replace '4824' with '04824' in the Recipient_Postal_Code column (Exact change in one Postal Code)
    #rohData['Recipient_Postal_Code'] = rohData['Recipient_Postal_Code'].replace('4824 ', '04824 ')
    # pre-process the data
    #data_processed = pre_process(rohData)
    transport_preis = pd.read_csv(r"../00_Resources/Transportpreismatrix_TK.csv", encoding="latin_1", sep=";", decimal=',')
    data_processed = pd.read_csv(r"../00_Resources/Basic_Data/preprocessed_data1.csv", encoding="latin_1", sep=";", decimal=',')
    # add coordinates
