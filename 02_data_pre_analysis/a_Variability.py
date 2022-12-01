import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import holidays as hd
from mpl_toolkits.mplot3d import Axes3D

def auswertung_nach_KW(df_touren):
    df_gewicht = pd.DataFrame(columns=df_touren["ID_Empfänger"].unique(),
                              index=df_touren["Kalenderwoche"].drop_duplicates())
    df_frequenz = pd.DataFrame(columns=df_touren["ID_Empfänger"].unique(),
                               index=df_touren["Kalenderwoche"].drop_duplicates())

    for col in df_gewicht.columns.values:
        df_filtered_col = df_touren[df_touren["ID_Empfänger"] == col]  # filtern nach ID
        for row in df_gewicht.index.values:
            df_filtered_row = df_filtered_col[df_filtered_col["Kalenderwoche"] == row]  # filtern nach KW
            df_gewicht.loc[row, col] = df_filtered_row["Gewicht"].sum()  # Summe Frachtgewicht
            df_frequenz.loc[row, col] = df_filtered_row["Gewicht"].shape[0]  # Anzahl Sendungen

    df_frequenz = df_frequenz.astype(float)
    df_gewicht = df_gewicht.astype(float)

    df_frequenz.to_csv(
        r"../00_Resources/pre_Analysis/Variabilitätsauswertung/frequenz_pro_woche.csv",
        encoding="latin_1", sep=";")
    df_gewicht.to_csv(
        r"../00_Resources/pre_Analysis/Variabilitätsauswertung/gewicht_pro_woche.csv",
        encoding="latin_1", sep=";")

    return df_frequenz, df_gewicht

def variabilitätsauswertung(df_frequenz, df_gewicht):
    df_auswertung = pd.DataFrame(
        columns=["avg_Gewicht", "avg_Frequenz", "std_Gewicht", "std_Frequenz", "variability_Gewicht",
                 "variability_Frequenz"], index=df_touren["ID_Empfänger"].unique())

    for col in df_gewicht.columns:
        df_auswertung.loc[col, "avg_Gewicht"] = df_gewicht[col].mean()
        df_auswertung.loc[col, "avg_Frequenz"] = df_frequenz[col].mean()

        df_auswertung.loc[col, "std_Gewicht"] = df_gewicht[col].std()
        df_auswertung.loc[col, "std_Frequenz"] = df_frequenz[col].std()

        df_auswertung.loc[col, "variability_Gewicht"] = df_auswertung.loc[col, "std_Gewicht"] / df_auswertung.loc[
            col, "avg_Gewicht"]
        df_auswertung.loc[col, "variability_Frequenz"] = df_auswertung.loc[col, "std_Frequenz"] / df_auswertung.loc[
            col, "avg_Frequenz"]

    kosten_array = []
    sendungen_array = []
    gewicht_array = []
    for index, row in df_auswertung.iterrows():
        kosten_array.append(df_touren_all[df_touren_all["ID_Empfänger"] == index]["Frachtkosten"].sum())
        sendungen_array.append(df_touren_all[df_touren_all["ID_Empfänger"] == index]["Frachtkosten"].count())
        gewicht_array.append(df_touren_all[df_touren_all["ID_Empfänger"] == index]["Gewicht"].sum())

    df_auswertung["Frachtkosten"] = kosten_array
    df_auswertung["Sendungen"] = sendungen_array
    df_auswertung["Gewicht"] = gewicht_array

    df_auswertung["Profilkunde"] = True

    df_auswertung.to_csv(
        r"../00_Resources/pre_Analysis/Variabilitätsauswertung/Variablitätsauswertung.csv",
        encoding="latin_1", sep=";", index_label="ID_Empfänger")

    return df_auswertung

def anteile_nach_varklassen(df):
    lower_bounds = [0, 0.75, 1.33]
    upper_bounds = [0.75, 1.33, 20]
    lower_gew = []
    upper_gew = []
    lower_freq = []
    upper_freq = []

    for index in range(len(lower_bounds)):
        for times in range(len(lower_bounds)):
            lower_gew.append(lower_bounds[index])
            upper_gew.append(upper_bounds[index])

    for times in range(len(lower_bounds)):
        for index in range(len(lower_bounds)):
            lower_freq.append(lower_bounds[index])
            upper_freq.append(upper_bounds[index])

    df_borders = pd.DataFrame(
        data={"lower_gew": lower_gew, "upper_gew": upper_gew, "lower_freq": lower_freq, "upper_freq": upper_freq})

    df_auswertung_filter_frequent = df_auswertung[df_auswertung["avg_Frequenz"] >= 1].reset_index()

    summe_frachtkosten = df_touren_all["Frachtkosten"].sum()
    anzahl_kunden_frequent = df_auswertung_filter_frequent["avg_Frequenz"].count()
    anzahl_sendungen = df_touren_all["Frachtkosten"].count()
    summe_gewicht = df_touren_all["Gewicht"].sum()

    print(anzahl_kunden_frequent)

    data_kundenanzahl = []
    data_frachtkosten = []
    data_sendungen = []
    data_gewicht = []
    for index, row in df_borders.iterrows():
        data_kundenanzahl.append(df_auswertung_filter_frequent.loc[
                                     (df_auswertung_filter_frequent["variability_Gewicht"] >= row["lower_gew"]) & (
                                             df_auswertung_filter_frequent["variability_Gewicht"] < row[
                                         "upper_gew"])
                                     & (df_auswertung_filter_frequent["variability_Frequenz"] >= row["lower_freq"]) & (
                                             df_auswertung_filter_frequent["variability_Frequenz"] < row[
                                         "upper_freq"])].shape[0] / anzahl_kunden_frequent)
        data_frachtkosten.append(df_auswertung_filter_frequent.loc[
                                     (df_auswertung_filter_frequent["variability_Gewicht"] >= row["lower_gew"]) & (
                                             df_auswertung_filter_frequent["variability_Gewicht"] < row[
                                         "upper_gew"])
                                     & (df_auswertung_filter_frequent["variability_Frequenz"] >= row["lower_freq"]) & (
                                             df_auswertung_filter_frequent["variability_Frequenz"] < row[
                                         "upper_freq"])]["Frachtkosten"].sum() / summe_frachtkosten)
        data_sendungen.append(df_auswertung_filter_frequent.loc[
                                  (df_auswertung_filter_frequent["variability_Gewicht"] >= row["lower_gew"]) & (
                                          df_auswertung_filter_frequent["variability_Gewicht"] < row[
                                      "upper_gew"])
                                  & (df_auswertung_filter_frequent["variability_Frequenz"] >= row["lower_freq"]) & (
                                          df_auswertung_filter_frequent["variability_Frequenz"] < row[
                                      "upper_freq"])]["Sendungen"].sum() / anzahl_sendungen)
        data_gewicht.append(df_auswertung_filter_frequent.loc[
                                (df_auswertung_filter_frequent["variability_Gewicht"] >= row["lower_gew"]) & (
                                        df_auswertung_filter_frequent["variability_Gewicht"] < row[
                                    "upper_gew"])
                                & (df_auswertung_filter_frequent["variability_Frequenz"] >= row["lower_freq"]) & (
                                        df_auswertung_filter_frequent["variability_Frequenz"] < row[
                                    "upper_freq"])]["Gewicht"].sum() / summe_gewicht)

    df_borders["Anteile_Kunden"] = data_kundenanzahl
    df_borders["Anteile_Frachtkosten"] = data_frachtkosten
    df_borders["Anteile_Sendungen"] = data_sendungen
    df_borders["Anteile_Gewicht"] = data_gewicht

    df_borders.to_csv(
        r"../00_Resources/pre_Analysis/Variabilitätsauswertung/Variabiltätsauswertung_Anteile.csv",
        encoding="latin_1", sep=";")

    return df_borders, data_kundenanzahl

def diagramm_3d_barplot(dz):
    fig = plt.figure()
    ax1 = fig.add_subplot(111, projection='3d')

    data = dz
    print(data)

    xpos = [2, 2, 2, 4, 4, 4, 6, 6, 6]
    ypos = [2, 4, 6, 2, 4, 6, 2, 4, 6]
    #colors = ["lightgrey", "lightgrey", "darkgrey", "lightgrey", "lightgrey", "grey", "grey", "grey", "grey"]
    colors = []

    """
    for i in range(len(dz)-1,0,-1):
        print(i)
        if data[i] == 0.0:
            xpos.pop(i)
            ypos.pop(i)
            colors.pop(i)
            data.pop(i)

    #data = filter(lambda x: x != 0, data)
    print(xpos)
    print(ypos)
    print(data)
    """

    for i in data:
        if i == 0:
            colors.append("#11223300")
        elif i<= 0.1:
            colors.append("lightgrey")
        elif i<= 0.2:
            colors.append("darkgrey")
        else:
            colors.append("grey")

    num_elements = len(xpos)
    zpos = np.zeros(len(xpos))
    dx = np.ones(len(xpos))
    dy = np.ones(len(xpos))

    ax1.set(xticks=[2.5, 4.5, 6.5], xticklabels=["$\leq$0.75", "$\leq$1.33", ">1.33"], xlabel="VarK Gewicht")
    ax1.set(yticks=[2.5, 4.5, 6.5], yticklabels=["$\leq$0.75", "$\leq$1.33", ">1.33"], ylabel="VarK Frequenz", zlabel= "")
    ax1.set(zticks=[0.1,0.2,0.3,0.4,0.5], zticklabels=["10%","20%","30%","40%","50%"], zlabel= "Anteil Kunden")

    ax1.bar3d(xpos, ypos, zpos, dx, dy, data,
              color=colors)
    #fig.tight_layout()
    plt.savefig(r"../00_Resources/pre_Analysis/Variabilitätsauswertung/Variabilitätsklassen.pdf", dpi=2000)

    #plt.show()

if __name__ == '__main__':
    state = "SL"
    years = 2020

    df_touren_all = pd.read_csv(r"../00_Resources/Grunddaten/Datensatz_TK_fertig.csv",
                            encoding="latin_1", sep=";")

    df_ID_list = pd.read_csv(r"../00_Resources/Grunddaten/ID_liste.csv",
                            encoding="latin_1", sep=";")

    df_touren_all["Beladedatum"] = pd.to_datetime(df_touren_all["Beladedatum"], dayfirst=True)
    df_touren_all["Kalenderwoche"] = df_touren_all["Beladedatum"].dt.week

    if state == None or years == None:
        for date in hd.DEU(state="SL", years=2020): #Wochen mit Feiertagen aussortieren
            df_touren = df_touren_all[df_touren_all["Kalenderwoche"] != date.isocalendar()[1]]

    df_frequenz, df_gewicht = auswertung_nach_KW(df_touren) #Auswertung nach KWs erstellen

    df_auswertung = variabilitätsauswertung(df_frequenz, df_gewicht)

    df_borders, data_kundenanzahl = anteile_nach_varklassen(df_auswertung)

    diagramm_3d_barplot(data_kundenanzahl)
