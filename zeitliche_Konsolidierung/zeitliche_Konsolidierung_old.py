import pandas as pd
import datetime as dt
import numpy as np


order_kat = ["sehr gering", "gering", "mittel", "hoch"]
order_fahrzeug = ["K","M", "G"]

pd.options.mode.chained_assignment = None  # default='warn'


def calc_HS_for_arrays(t_array, w_array, df_touren, df_tarifmatrix_long, pfad_df_zeitKons, kat_filter = None):


    def konsolidierung(t,w,df_touren, df_tarifmatrix_long, max_weight = 25000):
        w_grenze = w
        t_grenze = t
        print(kat_filter)

        def add_date(df_sendungen_ID):
            df_sendungen_ID["Beladedatum"] = pd.to_datetime(df_sendungen_ID["Beladedatum"], dayfirst=True)

            start = min(df_sendungen_ID["Beladedatum"])
            end = pd.to_datetime("25.12.2020")
            delta = end - start

            day_array = []
            weekday_array = []

            for i in range(delta.days + 1):
                day = pd.to_datetime(start + dt.timedelta(days=i))
                day_array.append(day)
                weekday_array.append(day.dayofweek)

            df_dates = pd.DataFrame(data={"Datum": day_array,
                                          "Wochentag": weekday_array})

            df_dates = df_dates.loc[~df_dates["Wochentag"].isin([5, 6])].reset_index(drop=True)

            df_dates["Periode"] = df_dates.index.values

            df_dates = df_dates.set_index("Datum", drop=False)

            period_array = []
            for index, row in df_sendungen_ID.iterrows():
                period_array.append(df_dates.loc[row["Beladedatum"],"Periode"])

            df_sendungen_ID["Periode"] = period_array

            return df_sendungen_ID

        df_touren["Beladedatum"] = pd.to_datetime(df_touren["Beladedatum"], dayfirst=True)
        df_touren["Wochentag"] = df_touren["Beladedatum"].dt.dayofweek

        df_touren_not_filter = df_touren[~df_touren['Kategorisierung'].isin(kat_filter) | (df_touren['Kategorisierung'].isin(kat_filter) & (df_touren['Wochentag']==5))]  # not in list
        df_touren_not_filter = df_touren_not_filter[["ID_Empfänger", "ID_Sendung", "Gewicht", "Distanz", "Frachtkosten", "Periode"]]

        df_touren = df_touren[(df_touren['Kategorisierung'].isin(kat_filter)) & (df_touren['Wochentag']!=5)]  # in list

        df_touren = add_date(df_touren)

        print(df_touren["Gewicht"].sum() + df_touren_not_filter["Gewicht"].sum())

        result_ID_Empfänger_array = []
        result_ID_Sendung_array = []
        result_Gewicht_array = []
        result_Distanz_array = []
        result_Periode_array = []
        result_Konsolidierung_array =[]
        result_avg_Verspätung = []

        for ID in df_touren["ID_Empfänger"].unique():
            df_touren_ID = df_touren[df_touren["ID_Empfänger"] == ID].reset_index()

            ID_Empfänger_array = []
            ID_Sendung_array = []
            Gewicht_array = []
            Distanz_array = []
            Periode_array = []

            for index, row in df_touren_ID.iterrows():

                if len(ID_Sendung_array) == 0:  # erstes Element: kein Element in df_Sendung
                    ID_Empfänger_array.append(row["ID_Empfänger"])
                    ID_Sendung_array.append(row["ID_Sendung"])
                    Gewicht_array.append(row["Gewicht"])
                    Distanz_array.append(row["Distanz"])
                    Periode_array.append(row["Periode"])

                    if index == df_touren_ID.index.max() or sum(Gewicht_array) >= w_grenze:
                        result_ID_Empfänger_array.append(ID_Empfänger_array[0])
                        result_ID_Sendung_array.append(ID_Sendung_array[0])
                        result_Gewicht_array.append(sum(Gewicht_array))
                        result_Distanz_array.append(Distanz_array[0])
                        result_Periode_array.append(Periode_array[-1])
                        result_Konsolidierung_array.append(len(Periode_array))
                        result_avg_Verspätung.append((len(Periode_array)*Periode_array[-1] -sum(Periode_array))/len(Periode_array))

                        ID_Empfänger_array = []
                        ID_Sendung_array = []
                        Gewicht_array = []
                        Distanz_array = []
                        Periode_array = []
                    continue
                if min(Periode_array) + t_grenze - 1 >= row["Periode"]:  # Zeitgrenze eingehalten
                    if (sum(Gewicht_array) + row["Gewicht"]) <= max_weight:
                        ID_Empfänger_array.append(row["ID_Empfänger"])
                        ID_Sendung_array.append(row["ID_Sendung"])
                        Gewicht_array.append(row["Gewicht"])
                        Distanz_array.append(row["Distanz"])
                        Periode_array.append(row["Periode"])
                        if sum(Gewicht_array) >= w_grenze:
                            result_ID_Empfänger_array.append(ID_Empfänger_array[0])
                            result_ID_Sendung_array.append(ID_Sendung_array[0])
                            result_Gewicht_array.append(sum(Gewicht_array))
                            result_Distanz_array.append(Distanz_array[0])
                            result_Periode_array.append(Periode_array[-1])
                            result_Konsolidierung_array.append(len(Periode_array))
                            result_avg_Verspätung.append(
                                (len(Periode_array) * Periode_array[-1] - sum(Periode_array)) / len(Periode_array))
                            ID_Empfänger_array = []
                            ID_Sendung_array = []
                            Gewicht_array = []
                            Distanz_array = []
                            Periode_array = []

                        elif index == df_touren_ID.index.max():
                            result_ID_Empfänger_array.append(ID_Empfänger_array[0])
                            result_ID_Sendung_array.append(ID_Sendung_array[0])
                            result_Gewicht_array.append(sum(Gewicht_array))
                            result_Distanz_array.append(Distanz_array[0])
                            result_Periode_array.append(row["Periode"]+t_grenze-1)
                            result_Konsolidierung_array.append(len(Periode_array))
                            result_avg_Verspätung.append(
                                (len(Periode_array) * (row["Periode"]+t_grenze-1) - sum(Periode_array)) / len(Periode_array))
                            ID_Empfänger_array = []
                            ID_Sendung_array = []
                            Gewicht_array = []
                            Distanz_array = []
                            Periode_array = []
                        continue
                    else:
                        result_ID_Empfänger_array.append(ID_Empfänger_array[0])
                        result_ID_Sendung_array.append(ID_Sendung_array[0])
                        result_Gewicht_array.append(sum(Gewicht_array))
                        result_Distanz_array.append(Distanz_array[0])
                        result_Periode_array.append(row["Periode"])
                        result_Konsolidierung_array.append(len(Periode_array))
                        result_avg_Verspätung.append(
                            (len(Periode_array) * row["Periode"] - sum(Periode_array)) / len(Periode_array))
                        ID_Empfänger_array = []
                        ID_Sendung_array = []
                        Gewicht_array = []
                        Distanz_array = []
                        Periode_array = []
                        ID_Empfänger_array.append(row["ID_Empfänger"])
                        ID_Sendung_array.append(row["ID_Sendung"])
                        Gewicht_array.append(row["Gewicht"])
                        Distanz_array.append(row["Distanz"])
                        Periode_array.append(row["Periode"])
                        if index == df_touren_ID.index.max() or sum(Gewicht_array) >= w_grenze:
                            result_ID_Empfänger_array.append(ID_Empfänger_array[0])
                            result_ID_Sendung_array.append(ID_Sendung_array[0])
                            result_Gewicht_array.append(sum(Gewicht_array))
                            result_Distanz_array.append(Distanz_array[0])
                            result_Periode_array.append(Periode_array[-1])
                            result_Konsolidierung_array.append(len(Periode_array))
                            result_avg_Verspätung.append(
                                (len(Periode_array) * Periode_array[-1] - sum(Periode_array)) / len(Periode_array))
                            ID_Empfänger_array = []
                            ID_Sendung_array = []
                            Gewicht_array = []
                            Distanz_array = []
                            Periode_array = []
                        continue
                else:  # Sendung überschreitet Zeitgrenze
                    result_ID_Empfänger_array.append(ID_Empfänger_array[0])
                    result_ID_Sendung_array.append(ID_Sendung_array[0])
                    result_Gewicht_array.append(sum(Gewicht_array))
                    result_Distanz_array.append(Distanz_array[0])
                    result_Periode_array.append(Periode_array[0]+t_grenze-1)
                    result_Konsolidierung_array.append(len(Periode_array))
                    result_avg_Verspätung.append(
                        (len(Periode_array) * (Periode_array[0]+t_grenze-1) - sum(Periode_array)) / len(Periode_array))
                    ID_Empfänger_array = []
                    ID_Sendung_array = []
                    Gewicht_array = []
                    Distanz_array = []
                    Periode_array = []
                    ID_Empfänger_array.append(row["ID_Empfänger"])
                    ID_Sendung_array.append(row["ID_Sendung"])
                    Gewicht_array.append(row["Gewicht"])
                    Distanz_array.append(row["Distanz"])
                    Periode_array.append(row["Periode"])
                    if index == df_touren_ID.index.max() or sum(Gewicht_array) >= w_grenze:
                        result_ID_Empfänger_array.append(ID_Empfänger_array[0])
                        result_ID_Sendung_array.append(ID_Sendung_array[0])
                        result_Gewicht_array.append(sum(Gewicht_array))
                        result_Distanz_array.append(Distanz_array[0])
                        result_Periode_array.append(Periode_array[-1])
                        result_Konsolidierung_array.append(len(Periode_array))
                        result_avg_Verspätung.append(
                            (len(Periode_array) * Periode_array[-1] - sum(Periode_array)) / len(Periode_array))

                        ID_Empfänger_array = []
                        ID_Sendung_array = []
                        Gewicht_array = []
                        Distanz_array = []
                        Periode_array = []

        result_frachtkosten_array = []
        for i in range(len(result_Gewicht_array)): #Frachtkosten hinzufügen
            gewicht = result_Gewicht_array[i]
            distanz = result_Distanz_array[i]
            tarifmatrix_long_filtered = df_tarifmatrix_long[
                (df_tarifmatrix_long["Distanz"] <= distanz) & (
                        df_tarifmatrix_long["Gewicht"] <= gewicht)]
            result_frachtkosten_array.append(tarifmatrix_long_filtered.iloc[-1, -1])

        data_df_HS_result = {"ID_Empfänger": result_ID_Empfänger_array, "ID_Sendung": result_ID_Sendung_array,
                             "Gewicht": result_Gewicht_array, "Distanz": result_Distanz_array, "Frachtkosten" : result_frachtkosten_array,
                             "Periode": result_Periode_array, "Anzahl_Konsolidierter_Ladungen": result_Konsolidierung_array, "avg_Verspätung": result_avg_Verspätung}
        df_HS_result = pd.DataFrame(data=data_df_HS_result)

        if kat_filter != None:
            df_HS_result = pd.concat([df_touren_not_filter, df_HS_result])
        return df_HS_result

    data_HS_frachtkosten = []
    data_HS_gewicht = []
    data_HS_t = []
    data_HS_w = []
    data_HS_distanz = []
    data_HS_verspätung = []

    for t in t_array:
        for w in w_array:
            data_HS = konsolidierung(t, w, df_touren, df_tarifmatrix_long)
            data_HS.to_csv(path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources"+ version +"\Zeitliche_Konsolidierung_Ergebnisse\Ergebnisdaten\HS_results_data_"+str(t)+"_"+str(w) + str(kat_filter) +".csv", encoding="latin_1", sep=";", decimal=".")
            data_HS_t.append(t)
            data_HS_w.append(w)
            data_HS_frachtkosten.append(data_HS["Frachtkosten"].sum())
            data_HS_gewicht.append(data_HS["Gewicht"].sum())
            data_HS_distanz.append(data_HS["Distanz"].sum())
            data_HS_verspätung.append(data_HS["avg_Verspätung"].sum()/data_HS["avg_Verspätung"].count())
            print(t, w, "Ready")

    for i, num in enumerate(data_HS_w):
        if num == 999999999999999999999:
            data_HS_w[i] = "unbegrenzt"

    frachtkosten_vorher = sum(df_touren["Frachtkosten"])
    frachtkosten_vorher_Kategorie = sum(df_touren[df_touren['Kategorisierung'].isin(kat_filter)]["Frachtkosten"])
    print("frachtkosten_vorher ",frachtkosten_vorher)
    print("frachtkosten_vorher_Kategorie ", frachtkosten_vorher_Kategorie)

    data_HS_ersparnis =[]
    data_HS_ersparnis_kategorie = []
    for j, frachtkosten in enumerate(data_HS_frachtkosten):
        data_HS_ersparnis.append((frachtkosten_vorher - data_HS_frachtkosten[j]) /frachtkosten_vorher)
        data_HS_ersparnis_kategorie.append((frachtkosten_vorher - data_HS_frachtkosten[j]) / frachtkosten_vorher_Kategorie)
        print((frachtkosten_vorher - data_HS_frachtkosten[j]) / frachtkosten_vorher_Kategorie)


    d = {"Konsolidierungsperioden": data_HS_t, "Gewichtsgenze": data_HS_w, "Distanz": data_HS_distanz,
         "Gewicht": data_HS_gewicht, "Frachtkosten": data_HS_frachtkosten,"Ersparnis": data_HS_ersparnis,"avg_Verspätung": data_HS_verspätung, "Ersparnis_Kategorie": data_HS_ersparnis_kategorie}
    df_HS = pd.DataFrame(data=d)

    df_HS.to_csv(path_or_buf=pfad_df_zeitKons, encoding="latin_1", sep=";", decimal=".")
    return df_HS

if __name__ == "__main__":
    version = "\Version_2"
    df_touren = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources"+ version +"\Datensatz_TK_fertig.csv", encoding="latin_1", sep=";")
    pd.to_datetime(df_touren["Beladedatum"], dayfirst = True)
    df_touren = df_touren.sort_values("Periode")

    df_tarifmatrix_long = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Transportpreismatrix_TK_long.csv", encoding="latin_1", sep=";")

    kat_filter = ["ZZZ","GRAU", "BLAU", "GELB", "GRÜN"] #alle Kategorien
    pfad_df_zeitKons = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources"+ version +"\Zeitliche_Konsolidierung_Ergebnisse\HS_results_" + str(kat_filter) +".csv"
    df_HS_results = calc_HS_for_arrays([2],[999999999999999999999], df_touren, df_tarifmatrix_long, pfad_df_zeitKons, kat_filter)

    data_overview_ersparnis = {"Konsolidierungsperioden": df_HS_results["Konsolidierungsperioden"],"Gewichtsgenze": df_HS_results["Gewichtsgenze"]}
    data_overview_ersparnis[str(kat_filter)] = df_HS_results["Ersparnis"]
    data_overview_avg_verspätung = {"Konsolidierungsperioden": df_HS_results["Konsolidierungsperioden"],"Gewichtsgenze": df_HS_results["Gewichtsgenze"]}
    data_overview_avg_verspätung[str(kat_filter)] = df_HS_results["avg_Verspätung"]
    data_overview_ersparnis_kategorie = {"Konsolidierungsperioden": df_HS_results["Konsolidierungsperioden"], "Gewichtsgenze": df_HS_results["Gewichtsgenze"]}
    data_overview_ersparnis_kategorie[str(kat_filter)] = df_HS_results["Ersparnis_Kategorie"]


    r"""
    kat_filter = ["ZZZ"]
    pfad_df_zeitKons = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources"+ version +"\Zeitliche_Konsolidierung_Ergebnisse\HS_results_" + str(kat_filter) + ".csv"
    df_HS_results = calc_HS_for_arrays([1, 2, 3, 4, 5], [999999999999999999999], df_touren,df_tarifmatrix_long, pfad_df_zeitKons, kat_filter)
    data_overview_ersparnis[str(kat_filter)] = df_HS_results["Ersparnis"]
    data_overview_avg_verspätung[str(kat_filter)] = df_HS_results["avg_Verspätung"]
    data_overview_ersparnis_kategorie[str(kat_filter)] = df_HS_results["Ersparnis_Kategorie"]

    kat_filter = ["GRAU"]
    pfad_df_zeitKons = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" + version + "\Zeitliche_Konsolidierung_Ergebnisse\HS_results_" + str(
        kat_filter) + ".csv"
    df_HS_results = calc_HS_for_arrays([1, 2, 3, 4, 5], [999999999999999999999], df_touren,
                                       df_tarifmatrix_long, pfad_df_zeitKons, kat_filter)
    data_overview_ersparnis[str(kat_filter)] = df_HS_results["Ersparnis"]
    data_overview_avg_verspätung[str(kat_filter)] = df_HS_results["avg_Verspätung"]
    data_overview_ersparnis_kategorie[str(kat_filter)] = df_HS_results["Ersparnis_Kategorie"]

    kat_filter = ["BLAU"]
    pfad_df_zeitKons = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" + version + "\Zeitliche_Konsolidierung_Ergebnisse\HS_results_" + str(
        kat_filter) + ".csv"
    df_HS_results = calc_HS_for_arrays([1, 2, 3, 4, 5], [999999999999999999999], df_touren,
                                       df_tarifmatrix_long, pfad_df_zeitKons, kat_filter)
    data_overview_ersparnis[str(kat_filter)] = df_HS_results["Ersparnis"]
    data_overview_avg_verspätung[str(kat_filter)] = df_HS_results["avg_Verspätung"]
    data_overview_ersparnis_kategorie[str(kat_filter)] = df_HS_results["Ersparnis_Kategorie"]

    kat_filter = ["GELB"]
    pfad_df_zeitKons = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" + version + "\Zeitliche_Konsolidierung_Ergebnisse\HS_results_" + str(
        kat_filter) + ".csv"
    df_HS_results = calc_HS_for_arrays([1, 2, 3, 4, 5], [999999999999999999999], df_touren,
                                       df_tarifmatrix_long, pfad_df_zeitKons, kat_filter)
    data_overview_ersparnis[str(kat_filter)] = df_HS_results["Ersparnis"]
    data_overview_avg_verspätung[str(kat_filter)] = df_HS_results["avg_Verspätung"]
    data_overview_ersparnis_kategorie[str(kat_filter)] = df_HS_results["Ersparnis_Kategorie"]

    kat_filter = ["GRÜN"]
    pfad_df_zeitKons = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" + version + "\Zeitliche_Konsolidierung_Ergebnisse\HS_results_" + str(
        kat_filter) + ".csv"
    df_HS_results = calc_HS_for_arrays([1, 2, 3, 4, 5], [999999999999999999999], df_touren,
                                       df_tarifmatrix_long, pfad_df_zeitKons, kat_filter)
    data_overview_ersparnis[str(kat_filter)] = df_HS_results["Ersparnis"]
    data_overview_avg_verspätung[str(kat_filter)] = df_HS_results["avg_Verspätung"]
    data_overview_ersparnis_kategorie[str(kat_filter)] = df_HS_results["Ersparnis_Kategorie"]

    kat_filter = ["ZZZ", "GRAU"]
    pfad_df_zeitKons = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" + version + "\Zeitliche_Konsolidierung_Ergebnisse\HS_results_" + str(
        kat_filter) + ".csv"
    df_HS_results = calc_HS_for_arrays([1, 2, 3, 4, 5], [999999999999999999999], df_touren,
                                       df_tarifmatrix_long, pfad_df_zeitKons, kat_filter)
    data_overview_ersparnis[str(kat_filter)] = df_HS_results["Ersparnis"]
    data_overview_avg_verspätung[str(kat_filter)] = df_HS_results["avg_Verspätung"]
    data_overview_ersparnis_kategorie[str(kat_filter)] = df_HS_results["Ersparnis_Kategorie"]

    kat_filter = ["ZZZ", "GRAU", "BLAU"]
    pfad_df_zeitKons = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" + version + "\Zeitliche_Konsolidierung_Ergebnisse\HS_results_" + str(
        kat_filter) + ".csv"
    df_HS_results = calc_HS_for_arrays([1, 2, 3, 4, 5], [999999999999999999999], df_touren,
                                       df_tarifmatrix_long, pfad_df_zeitKons, kat_filter)
    data_overview_ersparnis[str(kat_filter)] = df_HS_results["Ersparnis"]
    data_overview_avg_verspätung[str(kat_filter)] = df_HS_results["avg_Verspätung"]
    data_overview_ersparnis_kategorie[str(kat_filter)] = df_HS_results["Ersparnis_Kategorie"]
    """

    data_overview_ersparnis = pd.DataFrame(data = data_overview_ersparnis)
    data_overview_ersparnis.to_csv(path_or_buf= r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources"+ version +"\Zeitliche_Konsolidierung_Ergebnisse\overview_Ersparnisse.csv", encoding="latin_1", sep=";", decimal=".")

    data_overview_avg_verspätung = pd.DataFrame(data=data_overview_avg_verspätung)
    data_overview_avg_verspätung.to_csv(
        path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" + version + "\Zeitliche_Konsolidierung_Ergebnisse\overview_avg_Verspätung.csv",
        encoding="latin_1", sep=";", decimal=".")

    data_overview_ersparnis_kategorie = pd.DataFrame(data=data_overview_ersparnis_kategorie)
    data_overview_ersparnis_kategorie.to_csv(
        path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" + version + "\Zeitliche_Konsolidierung_Ergebnisse\data_overview_ersparnis_kategorie.csv",
        encoding="latin_1", sep=";", decimal=".")

