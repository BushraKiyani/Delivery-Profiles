import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import datetime
from Datenaufbreitung import Datensatzanpassung

def check_df_quality_ID_Empfänger(df, savepath):
    df["Kundenkategorie"] = df["Kundenkategorie"].str.upper()
    df["Empf. Straße"] = df["Empf. Straße"].str.upper()
    df["Empf. Ort"] = df["Empf. Ort"].str.upper()
    df = Datensatzanpassung.change_Columnname(df)

    ID_Empfänger_array = df["ID_Empfänger"].drop_duplicates().values

    num_Kundenamen_array = []
    num_Straßen_array = []
    num_Kategorien_array = []
    for ID in ID_Empfänger_array:
        num_Kundenamen_array.append((df[df["ID_Empfänger"] == ID]["Name_Empfänger"].drop_duplicates()).count())
        num_Straßen_array.append((df[df["ID_Empfänger"] == ID]["Straße_Empfänger"].drop_duplicates()).count())
        num_Kategorien_array.append((df[df["ID_Empfänger"] == ID]["Kategorisierung"].drop_duplicates()).count())
    print(num_Kundenamen_array)
    print(num_Straßen_array)
    print(num_Kategorien_array)
    data = {"ID_Empfänger": ID_Empfänger_array, "Anzahl_Kundennamen": num_Kundenamen_array, "Anzahl_Straßennamen": num_Straßen_array, "Anzahl_Kategorien": num_Kategorien_array}
    df_result = pd.DataFrame(data= data)
    df_result.to_csv(savepath, sep=";", encoding="latin1", decimal=".")
    return df_result

def check_df_quality_Name_Empfänger(df, savepath):
    df["Kundenkategorie"] = df["Kundenkategorie"].str.upper()
    df["Empf. Straße"] = df["Empf. Straße"].str.upper()
    df["Empf. Ort"] = df["Empf. Ort"].str.upper()
    df = Datensatzanpassung.change_Columnname(df)

    ID_Empfänger_array = df["Name_Empfänger"].drop_duplicates().values

    num_ID_Empfänger_array = []
    num_Straßen_array = []
    num_Kategorien_array = []
    for ID in ID_Empfänger_array:
        num_ID_Empfänger_array.append((df[df["Name_Empfänger"] == ID]["ID_Empfänger"].drop_duplicates()).count())
        num_Straßen_array.append((df[df["Name_Empfänger"] == ID]["Straße_Empfänger"].drop_duplicates()).count())
        num_Kategorien_array.append((df[df["Name_Empfänger"] == ID]["Kategorisierung"].drop_duplicates()).count())
    print(num_ID_Empfänger_array)
    print(num_Straßen_array)
    print(num_Kategorien_array)
    data = {"ID_Empfänger": ID_Empfänger_array, "Anzahl_ID_Empfänger": num_ID_Empfänger_array, "Anzahl_Straßennamen": num_Straßen_array, "Anzahl_Kategorien": num_Kategorien_array}
    df_result = pd.DataFrame(data= data)
    df_result.to_csv(savepath, sep=";", encoding="latin1", decimal=".")
    return df_result


if __name__ == '__main__':
    savepath_base = r'C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Datenqualität'

    df_touren = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Grunddaten\Rohdaten_TK.csv",
        encoding="latin_1", sep=";")
    dateiname = "\Rohdatenqualität_ID_Empfänger.csv"
    df_touren = check_df_quality_ID_Empfänger(df_touren, savepath_base + dateiname)

    df_touren = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Grunddaten\Rohdaten_TK.csv",
        encoding="latin_1", sep=";")
    dateiname = "\Rohdatenqualität_Name_Empfänger.csv"
    df_touren = check_df_quality_Name_Empfänger(df_touren, savepath_base + dateiname)


