import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datenanlyse_datenauswertung import *
from datenanalyse_Multiplot import *
order_kat = ["ZZZ", "BLAU", "GRAU", "GELB", "GRÜN"]
csv_endung = ".csv"
pdf_endung = ".pdf"

gewichtsgrenzen_unten= [0, 500,  1000, 2000, 6500, 10000]
gewichtsgrenzen_oben = [500, 1000, 2000, 6500, 10000, 25000]


def analyseAllKat(df_touren,diagrammdaten_grundpfad, diagramme_grundpfad, zeitraum):

    # Kundenkategorien
    speicherpfad_daten = diagrammdaten_grundpfad + "\Analyse_Kundenkategorien" + csv_endung
    speicherpfad_diagramm = diagramme_grundpfad + "\Kundenkategorien" + pdf_endung
    title = "Kundenkategorien" +zeitraum

    df_Kundenkategorien = auswertung_kundenkat(df_touren, order_kat, speicherpfad_daten)
    multiplot4x2(df_Kundenkategorien, speicherpfad_diagramm,title)

    speicherpfad_daten = diagrammdaten_grundpfad + "\Analyse_alte_Kundenkategorien" + csv_endung
    speicherpfad_diagramm = diagramme_grundpfad + r"\alte_Kundenkategorien" + pdf_endung
    title = "alte_Kundenkategorien" + zeitraum
    df_Kundenkategorien = auswertung_kundenkat(df_touren, order_kat, speicherpfad_daten, kat_col= "alte_Kategorisierung", ID_col= "alte_ID_Empfänger")
    multiplot4x2(df_Kundenkategorien, speicherpfad_diagramm, title)


    # Gewichtkategorien Sendungen
    lower_bounds = gewichtsgrenzen_unten
    upper_bounds = gewichtsgrenzen_oben

    speicherpfad_daten = diagrammdaten_grundpfad + "\Analyse_GewKat_Sendungen" + csv_endung
    speicherpfad_diagramm = diagramme_grundpfad + "\GewKat_Sendungen" + pdf_endung
    title = "Gewichtkategorien pro Sendung" +zeitraum

    df_GewKat_Kunden = auswertung_lower_upper_bound_nach_Sendungen(df_touren, lower_bounds, upper_bounds, "Gewicht",
                                                                   speicherpfad_daten, "kg")
    multiplot3x2(df_GewKat_Kunden, speicherpfad_diagramm, title)

    # df_AuswertungNachKunden alle
    speicherpfad_daten = diagrammdaten_grundpfad + "\df_AuswertungNachKunden" + csv_endung
    df_AuswertungNachKunden = auswertung_nach_kunden(df_touren, speicherpfad_daten)

    # Gewichtkategorien Kunden
    lower_bounds = gewichtsgrenzen_unten
    upper_bounds =  gewichtsgrenzen_oben
    title = "Gewichtkategorien pro Kunde" + zeitraum

    speicherpfad_daten = diagrammdaten_grundpfad + "\Analyse_GewKat_Kunden" + csv_endung
    speicherpfad_diagramm = diagramme_grundpfad + "\GewKat_Kunden" + pdf_endung
    daten = auswertung_lower_upper_bound_nach_Kunden(df_AuswertungNachKunden, lower_bounds, upper_bounds,
                                                     "avg_Gewicht_pro_Sendung", speicherpfad_daten, "kg")
    multiplot4x2(daten, speicherpfad_diagramm,title)

    # Frequenzkategorien Kunden
    lower_bounds = [0, 0.125, 0.25, 0.5, 1, 2, 3, 4, 5]
    upper_bounds = [0.125, 0.25, 0.5, 1, 2, 3, 4, 5, 6]
    title = "Frequenzkategorien pro Kunde" + zeitraum

    speicherpfad_daten = diagrammdaten_grundpfad + "\Analyse_FreqKat_Kunden" + csv_endung
    speicherpfad_diagramm = diagramme_grundpfad + "\FreqKat_Kunden" + pdf_endung
    daten = auswertung_lower_upper_bound_nach_Kunden(df_AuswertungNachKunden, lower_bounds, upper_bounds,
                                                     "avg_Sendungen_pro_Woche", speicherpfad_daten, "")
    multiplot4x2(daten, speicherpfad_diagramm, title)

    speicherpfad = diagrammdaten_grundpfad + "\Analyse_FrequenteKundenAnteile" +".txt"
    auswertung_kundenkat_tabelle(df_AuswertungNachKunden, speicherpfad, order_kat, minimum = 1)

def analyseFilteredKat(df_touren,filter_array, diagrammdaten_grundpfad, diagramme_grundpfad, zeitraum):
    # Gewichtkategorien Sendungen
    lower_bounds = gewichtsgrenzen_unten
    upper_bounds = gewichtsgrenzen_oben

    speicherpfad_daten = diagrammdaten_grundpfad + "\Analyse_GewKat_Sendungen"+ str(filter_array) + csv_endung
    speicherpfad_diagramm = diagramme_grundpfad + "\GewKat_Sendungen"+ str(filter_array) + pdf_endung
    title = "Gewichtkategorien pro Sendung" +zeitraum+ " "+ str(filter_array)

    df_GewKat_Sendung = auswertung_lower_upper_bound_nach_Sendungen(df_touren, lower_bounds, upper_bounds, "Gewicht",
                                                                   speicherpfad_daten, "kg", filter_array)
    multiplot3x2(df_GewKat_Sendung, speicherpfad_diagramm, title)


    # df_AuswertungNachKunden
    speicherpfad_daten = diagrammdaten_grundpfad + "\df_AuswertungNachKunden" + str(filter_array) + csv_endung
    df_AuswertungNachKunden = auswertung_nach_kunden(df_touren, speicherpfad_daten, filter_array)

    # Gewichtkategorien Kunden
    lower_bounds = gewichtsgrenzen_unten
    upper_bounds = gewichtsgrenzen_oben

    speicherpfad_daten = diagrammdaten_grundpfad + "\Analyse_GewKat_Kunden" + str(filter_array) + csv_endung
    speicherpfad_diagramm = diagramme_grundpfad + "\GewKat_Kunden" + str(filter_array) + pdf_endung
    title = "Gewichtskategorien pro Kunde" + zeitraum + " "+ str(filter_array)

    daten = auswertung_lower_upper_bound_nach_Kunden(df_AuswertungNachKunden, lower_bounds, upper_bounds,
                                                     "avg_Gewicht_pro_Sendung", speicherpfad_daten, "kg")
    multiplot4x2(daten, speicherpfad_diagramm,title)

    # Frequenzkategorien Kunden
    lower_bounds = [0, 0.125, 0.25, 0.5, 1, 2, 3, 4, 5]
    upper_bounds = [0.125, 0.25, 0.5, 1, 2, 3, 4, 5, 6]

    speicherpfad_daten = diagrammdaten_grundpfad + "\Analyse_FreqKat_Kunden" + str(filter_array) + csv_endung
    speicherpfad_diagramm = diagramme_grundpfad + "\FreqKat_Kunden" + str(filter_array) + pdf_endung
    title = "Frequenzkategorien pro Kunde" + zeitraum + " "+ str(filter_array)

    daten = auswertung_lower_upper_bound_nach_Kunden(df_AuswertungNachKunden, lower_bounds, upper_bounds,
                                                     "avg_Sendungen_pro_Woche", speicherpfad_daten, "")
    multiplot4x2(daten, speicherpfad_diagramm,title)

if __name__ == '__main__':
    version = "\Version_2"

    df_touren = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" +version+ "\Datensatz_TK_fertig.csv",
                            encoding="latin_1", sep=";")
    df_touren["Beladedatum"] = pd.to_datetime(df_touren["Beladedatum"], dayfirst=True)
    print(df_touren.dtypes)


    """Auswertung gesamtes Jahr"""
    diagrammdaten_grundpfad = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" +version+ "\Diagramme\Diagrammdaten"
    diagramme_grundpfad = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" +version+ "\Diagramme"
    zeitraum = " (Gesamtes Jahr)"

    analyseAllKat(df_touren,diagrammdaten_grundpfad, diagramme_grundpfad, zeitraum)

    filter_array = ["ZZZ"]
    analyseFilteredKat(df_touren, filter_array, diagrammdaten_grundpfad, diagramme_grundpfad, zeitraum)

    filter_array = ["GRAU"]
    analyseFilteredKat(df_touren, filter_array, diagrammdaten_grundpfad, diagramme_grundpfad, zeitraum)

    filter_array = ["ZZZ","GRAU"]
    analyseFilteredKat(df_touren, filter_array, diagrammdaten_grundpfad, diagramme_grundpfad, zeitraum)

    filter_array = ["BLAU"]
    analyseFilteredKat(df_touren, filter_array, diagrammdaten_grundpfad, diagramme_grundpfad, zeitraum)

    filter_array = ["ZZZ", "GRAU", "BLAU"]
    analyseFilteredKat(df_touren, filter_array, diagrammdaten_grundpfad, diagramme_grundpfad, zeitraum)

    filter_array = ["GELB"]
    analyseFilteredKat(df_touren, filter_array, diagrammdaten_grundpfad, diagramme_grundpfad, zeitraum)

    filter_array = ["GRÜN"]
    analyseFilteredKat(df_touren, filter_array, diagrammdaten_grundpfad, diagramme_grundpfad, zeitraum)



    """Auswertung für Februar"""
    diagrammdaten_grundpfad = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" +version+ "\Diagramme\Februar\Diagrammdaten"
    diagramme_grundpfad = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" +version+ "\Diagramme\Februar"
    zeitraum = " (Februar)"

    df_touren= df_touren[(df_touren["Beladedatum"]>= '2020-02-01') & (df_touren["Beladedatum"]<= '2020.02.29')]

    analyseAllKat(df_touren, diagrammdaten_grundpfad, diagramme_grundpfad,zeitraum)

    filter_array = ["ZZZ"]
    analyseFilteredKat(df_touren, filter_array, diagrammdaten_grundpfad, diagramme_grundpfad,zeitraum)

    filter_array = ["GRAU"]
    analyseFilteredKat(df_touren, filter_array, diagrammdaten_grundpfad, diagramme_grundpfad, zeitraum)

    filter_array = ["ZZZ", "GRAU"]
    analyseFilteredKat(df_touren, filter_array, diagrammdaten_grundpfad, diagramme_grundpfad, zeitraum)

    filter_array = ["ZZZ", "GRAU", "BLAU"]
    analyseFilteredKat(df_touren, filter_array, diagrammdaten_grundpfad, diagramme_grundpfad, zeitraum)