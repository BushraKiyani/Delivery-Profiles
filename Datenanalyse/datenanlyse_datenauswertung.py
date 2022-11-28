import pandas as pd
import holidays as hd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def auswertung_nach_kunden(df_touren, speicherpfad, filter_array = None):
    if (filter_array != None):
        df_touren =  df_touren[df_touren["Kategorisierung"].isin(filter_array)]

    df_touren["Kalenderwoche"] = df_touren["Beladedatum"].dt.week
    for date in hd.DEU(state="SL", years=2020):
        df_touren = df_touren[df_touren["Kalenderwoche"] != date.isocalendar()[1]]

    wochen = df_touren["Kalenderwoche"].drop_duplicates().count()
    #print(wochen)

    data_dict = {}
    data_dict["ID_Empfänger"] = df_touren["ID_Empfänger"].drop_duplicates()

    kat_array = []
    weight_array = []
    cost_array = []
    deliveries_array = []
    avg_weight_array = []
    avg_sendungen_woche_array = []
    avg_frachtkosten_sendung_array = []




    for ID in data_dict["ID_Empfänger"]:
        df_touren_filtered_customer = df_touren[df_touren["ID_Empfänger"] == ID]
        kat_array.append(df_touren_filtered_customer["Kategorisierung"].values[0])
        weight_array.append(df_touren_filtered_customer["Gewicht"].sum())
        cost_array.append(df_touren_filtered_customer["Frachtkosten"].sum())
        deliveries_array.append(df_touren_filtered_customer["ID_Sendung"].count())
        avg_weight_array.append(
            df_touren_filtered_customer["Gewicht"].sum() / df_touren_filtered_customer["ID_Sendung"].count())
        avg_sendungen_woche_array.append(df_touren_filtered_customer["ID_Sendung"].count() / wochen)
        avg_frachtkosten_sendung_array.append(
            df_touren_filtered_customer["Frachtkosten"].sum() / df_touren_filtered_customer["ID_Sendung"].count())

    data_dict["Kategorisierung"] = kat_array
    data_dict["Gewicht"] = weight_array
    data_dict["Frachtkosten"] = cost_array
    data_dict["Sendungen"] = deliveries_array
    data_dict["avg_Gewicht_pro_Sendung"] = avg_weight_array
    data_dict["avg_Sendungen_pro_Woche"] = avg_sendungen_woche_array
    data_dict["avg_Frachtkosten_pro_Sendung"] = avg_frachtkosten_sendung_array

    df_costumer = pd.DataFrame(data=data_dict)
    df_costumer.to_csv(
        path_or_buf=speicherpfad,
        encoding="latin_1", sep=";", decimal=".")
    return df_costumer

def auswertung_lower_upper_bound_nach_Kunden(df_auswertung_nach_kunden,lower_bounds,upper_bounds,filterkriterium,speicherpfad, einheit =""):
    df_auswertung_nach_kunden = df_auswertung_nach_kunden
    data_dict = {}

    kat_array = []
    weight_array = []
    cost_array = []
    weight_array_percent = []
    cost_array_percent = []
    costumer_array = []
    costumer_array_percent = []
    deliveries_array = []
    deliveries_array_percent = []

    df_borders = pd.DataFrame(data={"lower": lower_bounds, "upper": upper_bounds})

    for index, row in df_borders.iterrows():
        df_auswertung_nach_kunden_filtered = df_auswertung_nach_kunden[
            (df_auswertung_nach_kunden[filterkriterium] > row["lower"]) & (
                        df_auswertung_nach_kunden[filterkriterium] <= row["upper"])]

        kat_array.append("<=" + str(row["upper"]) + einheit)

        weight_array.append(df_auswertung_nach_kunden_filtered["Gewicht"].sum())
        cost_array.append(df_auswertung_nach_kunden_filtered["Frachtkosten"].sum())
        costumer_array.append(df_auswertung_nach_kunden_filtered["ID_Empfänger"].drop_duplicates().count())
        deliveries_array.append(df_auswertung_nach_kunden_filtered["Sendungen"].sum())

        weight_array_percent.append(df_auswertung_nach_kunden_filtered["Gewicht"].sum() / df_auswertung_nach_kunden["Gewicht"].sum())
        cost_array_percent.append(df_auswertung_nach_kunden_filtered["Frachtkosten"].sum() / df_auswertung_nach_kunden["Frachtkosten"].sum())
        costumer_array_percent.append(df_auswertung_nach_kunden_filtered["ID_Empfänger"].drop_duplicates().count() / df_auswertung_nach_kunden[
            "ID_Empfänger"].drop_duplicates().count())
        deliveries_array_percent.append(df_auswertung_nach_kunden_filtered["Sendungen"].sum() / df_auswertung_nach_kunden["Sendungen"].sum())

    data_dict["Kategorisierung"] = kat_array
    data_dict["Gewicht"] = weight_array
    data_dict["Frachtkosten"] = cost_array
    data_dict["Empfänger"] = costumer_array
    data_dict["Sendungen"] = deliveries_array
    data_dict["Gewicht_Prozent"] = weight_array_percent
    data_dict["Frachtkosten_Prozent"] = cost_array_percent
    data_dict["Empfänger_Prozent"] = costumer_array_percent
    data_dict["Sendungen_Prozent"] = deliveries_array_percent

    df_analyse_kat = pd.DataFrame(data=data_dict)
    df_analyse_kat["Gewicht_Prozent_cumsum"] = df_analyse_kat["Gewicht_Prozent"].cumsum()
    df_analyse_kat["Frachtkosten_Prozent_cumsum"] = df_analyse_kat["Frachtkosten_Prozent"].cumsum()
    df_analyse_kat["Empfänger_Prozent_cumsum"] = df_analyse_kat["Empfänger_Prozent"].cumsum()
    df_analyse_kat["Sendungen_Prozent_cumsum"] = df_analyse_kat["Sendungen_Prozent"].cumsum()

    df_analyse_kat.to_csv(
        path_or_buf=speicherpfad,
        encoding="latin_1", sep=";", decimal=".")

    return df_analyse_kat

def auswertung_lower_upper_bound_nach_Sendungen(df_auswertung_nach_kunden,lower_bounds,upper_bounds,filterkriterium,speicherpfad, einheit ="", filter_array = None):
    if (filter_array != None):
        df_auswertung_nach_kunden =  df_auswertung_nach_kunden[df_auswertung_nach_kunden["Kategorisierung"].isin(filter_array)]
    data_dict = {}

    kat_array = []
    weight_array = []
    cost_array = []
    weight_array_percent = []
    cost_array_percent = []
    costumer_array = []
    costumer_array_percent = []
    deliveries_array = []
    deliveries_array_percent = []

    df_borders = pd.DataFrame(data={"lower": lower_bounds, "upper": upper_bounds})

    for index, row in df_borders.iterrows():
        df_auswertung_nach_kunden_filtered = df_auswertung_nach_kunden[
            (df_auswertung_nach_kunden[filterkriterium] > row["lower"]) & (
                        df_auswertung_nach_kunden[filterkriterium] <= row["upper"])]

        kat_array.append("<=" + str(row["upper"]) + einheit)

        weight_array.append(df_auswertung_nach_kunden_filtered["Gewicht"].sum())
        cost_array.append(df_auswertung_nach_kunden_filtered["Frachtkosten"].sum())
        costumer_array.append(df_auswertung_nach_kunden_filtered["ID_Empfänger"].drop_duplicates().count())
        deliveries_array.append(df_auswertung_nach_kunden_filtered["ID_Sendung"].sum())

        weight_array_percent.append(df_auswertung_nach_kunden_filtered["Gewicht"].sum() / df_auswertung_nach_kunden["Gewicht"].sum())
        cost_array_percent.append(df_auswertung_nach_kunden_filtered["Frachtkosten"].sum() / df_auswertung_nach_kunden["Frachtkosten"].sum())
        costumer_array_percent.append(df_auswertung_nach_kunden_filtered["ID_Empfänger"].drop_duplicates().count() / df_auswertung_nach_kunden[
            "ID_Empfänger"].drop_duplicates().count())
        deliveries_array_percent.append(df_auswertung_nach_kunden_filtered["ID_Sendung"].sum() / df_auswertung_nach_kunden["ID_Sendung"].sum())

    data_dict["Kategorisierung"] = kat_array
    data_dict["Gewicht"] = weight_array
    data_dict["Frachtkosten"] = cost_array
    data_dict["Empfänger"] = costumer_array
    data_dict["Sendungen"] = deliveries_array
    data_dict["Gewicht_Prozent"] = weight_array_percent
    data_dict["Frachtkosten_Prozent"] = cost_array_percent
    data_dict["Empfänger_Prozent"] = costumer_array_percent
    data_dict["Sendungen_Prozent"] = deliveries_array_percent

    df_analyse_kat = pd.DataFrame(data=data_dict)
    df_analyse_kat["Gewicht_Prozent_cumsum"] = df_analyse_kat["Gewicht_Prozent"].cumsum()
    df_analyse_kat["Frachtkosten_Prozent_cumsum"] = df_analyse_kat["Frachtkosten_Prozent"].cumsum()
    df_analyse_kat["Empfänger_Prozent_cumsum"] = df_analyse_kat["Empfänger_Prozent"].cumsum()
    df_analyse_kat["Sendungen_Prozent_cumsum"] = df_analyse_kat["Sendungen_Prozent"].cumsum()

    df_analyse_kat.to_csv(
        path_or_buf=speicherpfad,
        encoding="latin_1", sep=";", decimal=".")

    return df_analyse_kat

def auswertung_kundenkat(df_touren_kat,order_kat, speicherpfad, kat_col = "Kategorisierung", ID_col ="ID_Empfänger"):
    data_dict ={
        "Kategorisierung": order_kat
    }
    weight_array = []
    cost_array = []
    weight_array_percent = []
    cost_array_percent = []
    costumer_array = []
    costumer_array_percent = []
    deliveries_array = []
    deliveries_array_percent = []

    for kat in order_kat:
        df_touren_kat_filtered = df_touren_kat[df_touren_kat[kat_col] == kat]

        weight_array.append(df_touren_kat_filtered["Gewicht"].sum())
        cost_array.append(df_touren_kat_filtered["Frachtkosten"].sum())
        costumer_array.append(df_touren_kat_filtered[ID_col].drop_duplicates().count())
        deliveries_array.append(df_touren_kat_filtered["ID_Sendung"].count())

        weight_array_percent.append(df_touren_kat_filtered["Gewicht"].sum() / df_touren_kat["Gewicht"].sum())
        cost_array_percent.append(df_touren_kat_filtered["Frachtkosten"].sum() / df_touren_kat["Frachtkosten"].sum())
        costumer_array_percent.append(df_touren_kat_filtered[ID_col].drop_duplicates().count() / df_touren_kat[ID_col].drop_duplicates().count())
        deliveries_array_percent.append(df_touren_kat_filtered["ID_Sendung"].count() / df_touren_kat["ID_Sendung"].count())

    data_dict["Gewicht"] = weight_array
    data_dict["Frachtkosten"] = cost_array
    data_dict["Empfänger"] = costumer_array
    data_dict["Sendungen"] = deliveries_array
    data_dict["Gewicht_Prozent"] = weight_array_percent
    data_dict["Frachtkosten_Prozent"] = cost_array_percent
    data_dict["Empfänger_Prozent"] = costumer_array_percent
    data_dict["Sendungen_Prozent"] = deliveries_array_percent

    df_analyse_kat = pd.DataFrame(data=data_dict)
    df_analyse_kat["Gewicht_Prozent_cumsum"] = df_analyse_kat["Gewicht_Prozent"].cumsum()
    df_analyse_kat["Frachtkosten_Prozent_cumsum"] = df_analyse_kat["Frachtkosten_Prozent"].cumsum()
    df_analyse_kat["Empfänger_Prozent_cumsum"] = df_analyse_kat["Empfänger_Prozent"].cumsum()
    df_analyse_kat["Sendungen_Prozent_cumsum"] = df_analyse_kat["Sendungen_Prozent"].cumsum()

    df_analyse_kat.to_csv(path_or_buf=speicherpfad, encoding="latin_1", sep=";", decimal=".")
    return df_analyse_kat

def auswertung_kundenkat_tabelle(df_kunden, speicherpfad,order_kat, minimum):
    gesamt_gewicht = df_kunden["Gewicht"].sum()
    gesamt_kosten = df_kunden["Frachtkosten"].sum()
    anzahl_kunden = df_kunden["ID_Empfänger"].count()
    anzahl_sendungen = df_kunden["Sendungen"].sum()

    kat_array = order_kat
    kunden_array = []
    gew_array = []
    send_array = []
    kosten_array =[]

    for kat in order_kat:
        gew_array.append((df_kunden[(df_kunden["Kategorisierung"]== kat) & (df_kunden["avg_Sendungen_pro_Woche"]>minimum)]["Gewicht"].sum())/gesamt_gewicht*100)
        kunden_array.append((df_kunden[
                              (df_kunden["Kategorisierung"] == kat) & (df_kunden["avg_Sendungen_pro_Woche"] > minimum)][
                              "ID_Empfänger"].count()) / anzahl_kunden * 100)
        send_array.append((df_kunden[
                              (df_kunden["Kategorisierung"] == kat) & (df_kunden["avg_Sendungen_pro_Woche"] > minimum)][
                              "Sendungen"].sum()) / anzahl_sendungen * 100)
        kosten_array.append((df_kunden[
                              (df_kunden["Kategorisierung"] == kat) & (df_kunden["avg_Sendungen_pro_Woche"] > minimum)][
                              "Frachtkosten"].sum()) / gesamt_kosten * 100)


    df_frequente_kunden = pd.DataFrame(data={"Kundenkategorisierung" : kat_array, "Kundenanteil": kunden_array, "Sendungsanteil": send_array, "Kostenanteil": kosten_array,"Gewichtsanteil":gew_array})
    df_frequente_kunden = df_frequente_kunden.append({"Kundenkategorisierung" : "Alle Kategorien", "Kundenanteil" : df_frequente_kunden["Kundenanteil"].sum(), "Sendungsanteil" : df_frequente_kunden["Sendungsanteil"].sum(), "Kostenanteil" : df_frequente_kunden["Kostenanteil"].sum(), "Gewichtsanteil": df_frequente_kunden["Gewichtsanteil"].sum()},ignore_index=True)

    df_frequente_kunden = df_frequente_kunden.round(2)
    df_frequente_kunden = df_frequente_kunden.astype(str) + "%"

    df_frequente_kunden.to_latex(speicherpfad,index= False)




