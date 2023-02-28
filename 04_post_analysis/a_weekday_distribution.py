import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os

import datetime

hue_order= ["ZZZ", "BLAU", "GRAU", "GELB", "GRÜN"]
colors = {"ZZZ": "red", "BLAU": "blue", "GRAU": "grey", "GELB": "yellow", "GRÜN": "green"}



def creatDiagrammGewichtWeekdays(df, df_pattern, path_filter):
    df = df[(df["Wochentag"] != 5)]
    df_pattern = df_pattern[(df_pattern["Wochentag"] != 5)]

    df = df.groupby(["Wochentag"]).sum().reset_index()
    df_pattern = df_pattern.groupby(["Wochentag"]).sum().reset_index()

    gewicht_anteil_array = []
    for index, row in df.iterrows():
        gewicht_anteil_array.append(row["Gewicht"]/ df["Gewicht"].sum())
    df["Gewicht_Prozent"] = gewicht_anteil_array
    #print(gewicht_anteil_array)

    gewicht_anteil_array_pattern =[]
    for index, row in df_pattern.iterrows():
        gewicht_anteil_array_pattern.append(row["Gewicht"]/ df_pattern["Gewicht"].sum())
    df_pattern["Gewicht_Prozent_pattern"] = gewicht_anteil_array_pattern
    #print(gewicht_anteil_array_pattern)

    labels = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag'] #, "Samstag"
    x = np.arange(len(labels))
    width = 0.35

    figure, axes = plt.subplots(figsize=(10, 5))

    plot1 = axes.bar(x - width/1.9, gewicht_anteil_array, width, label = "ohne Belieferungsprofilen", color= "grey")
    plot2 = axes.bar(x + width / 1.9, gewicht_anteil_array_pattern, width, label="mit Belieferungsprofilen", color= "lightgrey")

    axes.set(ylabel = "Frachtgewichtsanteil", xlabel= "Wochentage")
    axes.set_xticks(np.arange(len(x)))
    axes.set_xticklabels(labels)
    axes.set_yticklabels(["0"+"%","5"+"%","10"+"%","15"+"%","20"+"%","25"+"%"])
    axes.legend()

    def autolabel(rects):
        """
        Attach a text label above each bar displaying its height
        """
        for rect in rects:
            height = rect.get_height()
            axes.text(rect.get_x() + rect.get_width() / 2., 1.01 * height,
                    '%s' % str(round(height*100,1))+"%",
                    ha='center', va='bottom')

    autolabel(plot1)
    autolabel(plot2)
    figure.tight_layout()

    plt.savefig(f"../00_Resources/post_Analysis/{path_filter}/FrachtgewichtanteilProWochentag.pdf", dpi=2000)
    #plt.show()
    plt.clf()

def creatDiagrammSendungWeekdays(df, df_pattern, path_filter):
    df = df[(df["Wochentag"] != 5)]
    df_pattern = df_pattern[(df_pattern["Wochentag"] != 5)]

    df = df.groupby(["Wochentag"]).count().reset_index()
    df_pattern = df_pattern.groupby(["Wochentag"]).count().reset_index()

    gewicht_anteil_array = []
    for index, row in df.iterrows():
        gewicht_anteil_array.append(row["Gewicht"]/ df["Gewicht"].sum())
    df["Gewicht_Prozent"] = gewicht_anteil_array
    #print(gewicht_anteil_array)

    gewicht_anteil_array_pattern =[]
    for index, row in df_pattern.iterrows():
        gewicht_anteil_array_pattern.append(row["Gewicht"]/ df_pattern["Gewicht"].sum())
    df_pattern["Gewicht_Prozent_pattern"] = gewicht_anteil_array_pattern
    #print(gewicht_anteil_array_pattern)

    labels = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag'] #, "Samstag"
    x = np.arange(len(labels))
    width = 0.35

    figure, axes = plt.subplots(figsize=(10, 5))

    plot1 = axes.bar(x - width/1.9, gewicht_anteil_array, width, label = "ohne Belieferungsprofilen", color= "grey")
    plot2 = axes.bar(x + width / 1.9, gewicht_anteil_array_pattern, width, label="mit Belieferungsprofilen", color= "lightgrey")

    axes.set(ylabel = "Sendungssanteil", xlabel= "Wochentage")
    axes.set_xticks(np.arange(len(x)))
    axes.set_xticklabels(labels)
    axes.set_yticklabels(["0"+"%","5"+"%","10"+"%","15"+"%","20"+"%","25"+"%"])
    axes.legend()

    def autolabel(rects):
        """
        Attach a text label above each bar displaying its height
        """
        for rect in rects:
            height = rect.get_height()
            axes.text(rect.get_x() + rect.get_width() / 2., 1.01 * height,
                    '%s' % str(round(height*100,1))+"%",
                    ha='center', va='bottom')

    autolabel(plot1)
    autolabel(plot2)
    figure.tight_layout()

    plt.savefig(f"../00_Resources/post_Analysis/{path_filter}/SendungsanteilProWochentag.pdf", dpi=2000)
    #plt.show()
    plt.clf()

def creatDiagrammGewichtWeekdaysPattern_only(df, df_pattern, path_filter):
    df = df[(df["ID_Empfänger"].isin(df_pattern["ID_Empfänger"].values)) & (df["Wochentag"] != 5)]

    df = df.groupby(["Wochentag"]).sum().reset_index()
    df_pattern = df_pattern.groupby(["Wochentag"]).sum().reset_index()

    gewicht_anteil_array = []
    for index, row in df.iterrows():
        gewicht_anteil_array.append(row["Gewicht"]/ df["Gewicht"].sum())
    df["Gewicht_Prozent"] = gewicht_anteil_array
    #print(gewicht_anteil_array)

    gewicht_anteil_array_pattern =[]
    for index, row in df_pattern.iterrows():
        gewicht_anteil_array_pattern.append(row["Gewicht"]/ df_pattern["Gewicht"].sum())
    df_pattern["Gewicht_Prozent_pattern"] = gewicht_anteil_array_pattern
    #print(gewicht_anteil_array_pattern)

    labels = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag']
    x = np.arange(len(labels))
    width = 0.35

    figure, axes = plt.subplots(figsize=(10, 5))

    plot1 = axes.bar(x - width / 1.9, gewicht_anteil_array, width, label = "ohne Belieferungsprofilen", color= "grey")
    plot2 = axes.bar(x + width / 1.9, gewicht_anteil_array_pattern, width, label="mit Belieferungsprofilen", color= "lightgrey")

    axes.set(ylabel = "Frachtgewichtsanteil", xlabel= "Wochentage")
    axes.set_xticks(np.arange(len(x)))
    axes.set_xticklabels(labels)
    axes.set_yticklabels(["0"+"%","5"+"%","10"+"%","15"+"%","20"+"%","25"+"%"])
    axes.legend()

    def autolabel(rects):
        """
        Attach a text label above each bar displaying its height
        """
        for rect in rects:
            height = rect.get_height()
            axes.text(rect.get_x() + rect.get_width() / 2., 1.01 * height,
                    '%s' % str(round(height*100,1))+"%",
                    ha='center', va='bottom')

    autolabel(plot1)
    autolabel(plot2)
    figure.tight_layout()

    plt.savefig(f"../00_Resources/post_Analysis/{path_filter}/FrachtgewichtanteilProWochentagPatternOnly.pdf", dpi=2000)
    #plt.show()
    plt.clf()

def creatDiagrammSendungenWeekdaysPattern_only(df, df_pattern, path_filter):
    df = df[(df["ID_Empfänger"].isin(df_pattern["ID_Empfänger"].values)) & (df["Wochentag"] != 5)]

    df = df.groupby(["Wochentag"]).count().reset_index()
    df_pattern = df_pattern.groupby(["Wochentag"]).count().reset_index()
    print(df)
    print(df_pattern)

    gewicht_anteil_array = []
    for index, row in df.iterrows():
        gewicht_anteil_array.append(row["Gewicht"]/ df["Gewicht"].sum())
    df["Gewicht_Prozent"] = gewicht_anteil_array
    print(gewicht_anteil_array)

    gewicht_anteil_array_pattern =[]
    for index, row in df_pattern.iterrows():
        gewicht_anteil_array_pattern.append(row["Gewicht"]/ df_pattern["Gewicht"].sum())
    df_pattern["Gewicht_Prozent_pattern"] = gewicht_anteil_array_pattern
    print(gewicht_anteil_array_pattern)

    labels = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag']
    x = np.arange(len(labels))
    width = 0.35

    figure, axes = plt.subplots(figsize=(10, 5))

    plot1 = axes.bar(x - width / 1.9, gewicht_anteil_array, width, label = "ohne Belieferungsprofilen", color= "grey")
    plot2 = axes.bar(x + width / 1.9, gewicht_anteil_array_pattern, width, label="mit Belieferungsprofilen", color= "lightgrey")

    axes.set(ylabel = "Sendungsanteil", xlabel= "Wochentage")
    axes.set_xticks(np.arange(len(x)))
    axes.set_xticklabels(labels)
    axes.set_yticklabels(["0"+"%","5"+"%","10"+"%","15"+"%","20"+"%","25"+"%"])
    axes.legend()

    def autolabel(rects):
        """
        Attach a text label above each bar displaying its height
        """
        for rect in rects:
            height = rect.get_height()
            axes.text(rect.get_x() + rect.get_width() / 2., 1.01 * height,
                    '%s' % str(round(height*100,1))+"%",
                    ha='center', va='bottom')

    autolabel(plot1)
    autolabel(plot2)
    figure.tight_layout()

    plt.savefig(f"../00_Resources/post_Analysis/{path_filter}/SendungsanteilProWochentagPatternOnly.pdf", dpi=2000)
    #plt.show()
    plt.clf()


if __name__ == '__main__':
    var_gewicht = 1.33
    var_frequenz = 1.33
    mindest_frequenz = 0.5

    df_touren = pd.read_csv(r"../00_Resources/Grunddaten/Datensatz_TK_fertig.csv",
                                      encoding="latin_1", sep=";",decimal=",", dtype={"Gewicht": float, "Distanz": float, "Frachtkosten": float})
    df_touren["Beladedatum"] = pd.to_datetime(df_touren["Beladedatum"],dayfirst = True)
    df_touren["Kalenderwoche"] = df_touren["Beladedatum"].dt.week
    df_touren["Wochentag"] = df_touren["Beladedatum"].dt.dayofweek
    df_touren["Monat"] = df_touren["Beladedatum"].dt.month

    df_touren = df_touren[["ID_Empfänger","Beladedatum", "Kalenderwoche","Wochentag", "Monat", "Gewicht", "Frachtkosten"]]
    #print(df_touren)

    df_pattern_133 = pd.read_csv(f"../00_Resources/profile_results/Ergebnisse/Pattern_results_data_var_gewicht{var_gewicht}_var_frequenz{var_frequenz}_mindest_frequenz{mindest_frequenz}.csv",
                                      encoding="latin_1", sep=";")
    df_pattern_133_only = pd.read_csv(f"../00_Resources/profile_results/Ergebnisse/Pattern_results_data_only_var_gewicht{var_gewicht}_var_frequenz{var_frequenz}_mindest_frequenz{mindest_frequenz}.csv",
                                      encoding="latin_1", sep=";")
    path_filter = f"var_gewicht{var_gewicht}_var_frequenz{var_frequenz}_mindest_frequenz{mindest_frequenz}"

    dir = f"../00_Resources/post_Analysis/{path_filter}"
    if not os.path.exists(path=dir):
        os.makedirs(dir)

    creatDiagrammGewichtWeekdays(df_touren, df_pattern_133, path_filter)
    creatDiagrammGewichtWeekdaysPattern_only(df_touren, df_pattern_133_only, path_filter)

    creatDiagrammSendungWeekdays(df_touren, df_pattern_133, path_filter)
    creatDiagrammSendungenWeekdaysPattern_only(df_touren, df_pattern_133_only, path_filter)