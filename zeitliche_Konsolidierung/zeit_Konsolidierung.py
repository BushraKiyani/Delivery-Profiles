import pandas as pd
import datetime
import math
from multiple_Knapsack import *
pd.options.mode.chained_assignment = None  # default='warn'

def add_date(df_sendungen_ID):
    #df_sendungen_ID["Beladedatum"] = pd.to_datetime(df_sendungen_ID["Beladedatum"], dayfirst=True)

    start = min(df_sendungen_ID["Beladedatum"])
    end = pd.to_datetime("25.12.2020")
    delta = end - start

    day_array = []
    weekday_array = []

    for i in range(delta.days + 1):
        day = pd.to_datetime(start + datetime.timedelta(days=i))
        day_array.append(day)
        weekday_array.append(day.dayofweek)

    df_dates = pd.DataFrame(data={"Datum": day_array,
                                  "Wochentag": weekday_array})

    df_dates = df_dates.loc[~df_dates["Wochentag"].isin([5, 6])].reset_index(drop=True)

    df_dates["Periode"] = df_dates.index.values

    df_dates = df_dates.set_index("Datum", drop=False)

    period_array = []
    for index, row in df_sendungen_ID.iterrows():
        period_array.append(df_dates.loc[row["Beladedatum"], "Periode"])

    df_sendungen_ID["Periode"] = period_array

    return df_sendungen_ID, df_dates

def add_to_dict(data_dict, row, gewicht, ID_send,durchschn_Versp, anzahl):
    data_dict["ID_Empfänger"].append(row["ID_Empfänger"])
    data_dict["ID_Sendung"].append(ID_send)
    data_dict["Gewicht"].append(gewicht)
    data_dict["Distanz"].append(row["Distanz"])
    data_dict["Frachtkosten"].append(row["Frachtkosten"])
    data_dict["Beladedatum"].append(row["Beladedatum"])
    data_dict["Periode"].append(row["Periode"])
    data_dict["Wochentag"].append(row["Wochentag"])
    data_dict["Kategorisierung"].append(row["Kategorisierung"])
    data_dict["durchschn_Verspätung"].append(durchschn_Versp)
    data_dict["Anzahl_Sendungen"].append(anzahl)
    return data_dict

def frachtkosten_berechnen(df_tarifmatrix_long, gewicht, distanz):
    tarifmatrix_long_filtered = df_tarifmatrix_long[(df_tarifmatrix_long["Distanz"] <= distanz) & (df_tarifmatrix_long["Gewicht"] <= gewicht)]
    return tarifmatrix_long_filtered.iloc[-1, -1]

def calc_Sendung(per, df_touren_filter, df_tarifmatrix_long, df_dates):
    data_dict = {"ID_Empfänger": [], "ID_Sendung": [], "Gewicht": [],
                                "Distanz": [], "Frachtkosten": [],
                                "Beladedatum": [],"durchschn_Verspätung": [], "Anzahl_Sendungen": [], "Periode": [],
                                "Wochentag": [], "Kategorisierung": [],}

    for ID in df_touren_filter["ID_Empfänger"].unique():
        #print("ID" ,ID)
        df_touren_filter_ID = df_touren_filter[df_touren_filter["ID_Empfänger"] == ID]

        df_touren_filter_ID_index = list(df_touren_filter_ID["ID_Sendung"])
        #print(df_touren_filter_ID_index)

        for index, row in df_touren_filter_ID.iterrows():

            if row["ID_Sendung"] in df_touren_filter_ID_index:

                start_date = row["Beladedatum"]

                start_periode = df_dates.loc[str(start_date).split(" ")[0],"Periode"]
                end_periode = start_periode + per


                df_touren_filter_ID_date = df_touren_filter_ID[(df_touren_filter_ID["Periode"]>= start_periode) & (df_touren_filter_ID["Periode"]< end_periode)]

                df_touren_filter_ID_date["Verspätung"] = df_touren_filter_ID_date["Periode"].apply(lambda x: start_periode +per - x -1)




                if df_touren_filter_ID_date["Gewicht"].sum() >25000:
                    """
                    ### Gleichmäßige Aufteilung
                    LKW_anzahl = math.ceil(df_touren_filter_ID_date["Gewicht"].sum() /25000)
                    for i in range(LKW_anzahl):
                        print(i)
                        data_dict = add_to_dict(data_dict=data_dict, row=row,
                                                gewicht=df_touren_filter_ID_date["Gewicht"].sum() /LKW_anzahl,
                                                ID_send=list(df_touren_filter_ID_date["ID_Sendung"]),
                                                durchschn_Versp=df_touren_filter_ID_date["Verspätung"].mean(),
                                                anzahl=df_touren_filter_ID_date.shape[0])
                    """

                    ### MKP Zuordnung
                    print(df_touren_filter_ID_date)
                    df_touren_filter_ID_date_underweight = df_touren_filter_ID_date[df_touren_filter_ID_date["Gewicht"] <= 25000]
                    df_touren_filter_ID_date_underweight = df_touren_filter_ID_date_underweight.reset_index(drop=True)
                    print(df_touren_filter_ID_date_underweight)
                    print(list(df_touren_filter_ID_date_underweight["Frachtkosten"]))
                    print(list(df_touren_filter_ID_date_underweight["Gewicht"]))

                    capacities = [25000 for i in range(int(df_touren_filter_ID_date_underweight["Gewicht"].sum()/25000))]
                    capacities = [25000] if len(capacities) == 0 else capacities
                    print(capacities)

                    if df_touren_filter_ID_date_underweight.empty == False:
                        send_aufteilung, dropped_items = multiple_knappsack(values=list(df_touren_filter_ID_date_underweight["Gewicht"]),weights=list(df_touren_filter_ID_date_underweight["Gewicht"]), capacities=capacities)

                        for bin in send_aufteilung:
                            gewicht = 0
                            send_id = []
                            verspätung =0
                            for i in bin:
                                gewicht += df_touren_filter_ID_date_underweight.loc[i,"Gewicht"]
                                send_id.append(df_touren_filter_ID_date_underweight.loc[i,"ID_Sendung"])
                                verspätung += df_touren_filter_ID_date_underweight.loc[i,"Verspätung"]

                            data_dict = add_to_dict(data_dict=data_dict,row=row, gewicht = gewicht, ID_send= send_id, durchschn_Versp= verspätung/ len(bin), anzahl = len(bin))

                        if len(dropped_items)!=0:
                            gewicht = 0
                            send_id = []
                            verspätung = 0
                            for i in dropped_items:
                                gewicht += df_touren_filter_ID_date_underweight.loc[i, "Gewicht"]
                                send_id.append(df_touren_filter_ID_date_underweight.loc[i, "ID_Sendung"])
                                verspätung += df_touren_filter_ID_date_underweight.loc[i, "Verspätung"]

                            data_dict = add_to_dict(data_dict=data_dict, row=row, gewicht=gewicht, ID_send=send_id,durchschn_Versp=float(verspätung/ len(dropped_items)), anzahl=len(dropped_items))

                    df_touren_filter_ID_date_overweight = df_touren_filter_ID_date[df_touren_filter_ID_date["Gewicht"] > 25000]
                    for index_w, row_w in df_touren_filter_ID_date_overweight.iterrows():
                        data_dict = add_to_dict(data_dict=data_dict, row=row, gewicht=row_w["Gewicht"], ID_send=row_w["ID_Sendung"], durchschn_Versp= row_w["Verspätung"], anzahl = 1)

                else:
                    data_dict = add_to_dict(data_dict=data_dict,row=row, gewicht = df_touren_filter_ID_date["Gewicht"].sum(), ID_send= list(df_touren_filter_ID_date["ID_Sendung"]), durchschn_Versp= df_touren_filter_ID_date["Verspätung"].mean(), anzahl =df_touren_filter_ID_date.shape[0])

                for i_d, row_d in df_touren_filter_ID_date.iterrows():
                    df_touren_filter_ID_index.remove(row_d["ID_Sendung"])

            else:
                continue


    df_konsoldiert = pd.DataFrame(data=data_dict)
    print("______________")

    df_konsoldiert["Frachtkosten"] = df_konsoldiert.apply(lambda row_l: frachtkosten_berechnen(df_tarifmatrix_long, row_l["Gewicht"], row_l["Distanz"]),axis=1)

    df_konsoldiert.to_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Konsolidierung\kons_only\\"+ str(per)+"\df_kons_only_per"+str(per)+"_kat"+str(kat_filter)+".csv", encoding="latin_1", sep=";")
    return df_konsoldiert


if __name__ == "__main__":

    df_touren = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Datensatz_TK_fertig.csv", encoding="latin_1", sep=";")
    df_touren["Beladedatum"]  = pd.to_datetime(df_touren["Beladedatum"], dayfirst = True)
    df_touren = df_touren.sort_values("Beladedatum")
    df_touren["Wochentag"] = df_touren["Beladedatum"].dt.dayofweek

    df_tarifmatrix_long = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Transportpreismatrix_TK_long.csv", encoding="latin_1", sep=";")

    df_variablitätsauswertung = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Variabiltätsauswertung\Variablitaetsauswertung.csv", encoding="latin_1", sep=";")
    df_touren = pd.merge(df_touren, df_variablitätsauswertung[["ID_Empfänger","variability_Gewicht", "variability_Frequenz" ]], how="left", on= "ID_Empfänger")
    print(df_touren.head(10))
    perioden = [1,2,3,4,5]
    var_filter = 1.33
    kategorien = [ ["ZZZ", "GRAU", "BLAU", "GELB", "GRÜN"]] #,

    data_einsparungen = {
        "Kundenkategorien": [],
        "Konsolidierungsperioden":[],
        "Ersparnisse abs": [],
        "Ersparnisse in %":[],
    }
    data_verspätung ={
        "Kundenkategorien": [],
        "Konsolidierungsperioden": [],
        "Durchschn. Verspätung":[]
    }

    for per in perioden:
        print("Perioden: ",per)
        for kat_filter in kategorien:
            print("Kategorie: ", kat_filter)
            df_touren_not_filter = df_touren[~df_touren['Kategorisierung'].isin(kat_filter) | (df_touren['Kategorisierung'].isin(kat_filter) & (df_touren['Wochentag'] == 5)) | (df_touren['Kategorisierung'].isin(kat_filter) & (df_touren["variability_Gewicht"] > 1.33)) | (df_touren['Kategorisierung'].isin(kat_filter) & (df_touren["variability_Frequenz"] > 1.33))]  # not in list
            df_touren_not_filter = df_touren_not_filter[["ID_Empfänger", "ID_Sendung", "Gewicht", "Distanz", "Frachtkosten", "Beladedatum", "Periode", "Wochentag", "Kategorisierung", "variability_Gewicht","variability_Frequenz"]]

            df_touren_filter = df_touren[(df_touren['Kategorisierung'].isin(kat_filter)) & (df_touren['Wochentag'] != 5)]
            print(df_touren_filter.info())
            df_touren_filter = df_touren_filter[(df_touren_filter["variability_Gewicht"]<= 1.33) & (df_touren_filter["variability_Frequenz"]<= 1.33)]
            df_touren_filter = df_touren_filter[["ID_Empfänger", "ID_Sendung", "Gewicht", "Distanz", "Frachtkosten","Beladedatum", "Periode", "Wochentag", "Kategorisierung", "variability_Gewicht","variability_Frequenz"]]

            df_touren_filter, df_dates = add_date(df_touren_filter)

            print(df_touren_filter["Gewicht"].sum() + df_touren_not_filter["Gewicht"].sum(), " = ",df_touren["Gewicht"].sum())

            df_konsoldiert = calc_Sendung(per, df_touren_filter, df_tarifmatrix_long,df_dates)

            df_gesamt = pd.concat([df_konsoldiert,df_touren_not_filter])

            df_gesamt.to_csv(
                r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Konsolidierung\kons_all\df_kons_all_per" + str(
                    per) + "_kat" + str(kat_filter) + str(var_filter) + ".csv", encoding="latin_1", sep=";")

            data_einsparungen["Kundenkategorien"].append(kat_filter)
            data_einsparungen["Konsolidierungsperioden"].append(per)
            data_einsparungen["Ersparnisse abs"].append(df_touren["Frachtkosten"].sum() - df_gesamt["Frachtkosten"].sum())
            data_einsparungen["Ersparnisse in %"].append(1-(df_gesamt["Frachtkosten"].sum() / df_touren["Frachtkosten"].sum()))

            data_verspätung["Kundenkategorien"].append(kat_filter)
            data_verspätung["Konsolidierungsperioden"].append(per)

            data_verspätung["Durchschn. Verspätung"].append(df_konsoldiert["durchschn_Verspätung"].mean())

    df_einsparungen = pd.DataFrame(data=data_einsparungen)
    df_einsparungen["Kundenkategorien"] = df_einsparungen["Kundenkategorien"].astype("str")
    df_einsparungen = df_einsparungen.pivot(index="Konsolidierungsperioden",columns= "Kundenkategorien", values="Ersparnisse in %")

    #df_einsparungen["'ZZZ, GRAU'"] = df_einsparungen[["['ZZZ']","['GRAU']"]].sum(axis= 1)
    #df_einsparungen["'ZZZ, GRAU, BLAU'"] = df_einsparungen[["['ZZZ']","['GRAU']","['BLAU']"]].sum(axis= 1)
    #df_einsparungen["Alle"] = df_einsparungen[["['ZZZ']", "['GRAU']", "['BLAU']", "['GELB']", "['GRÜN']"]].sum(axis=1)
    print(df_einsparungen)

    df_verspätung = pd.DataFrame(data = data_verspätung)
    df_verspätung["Kundenkategorien"] = df_verspätung["Kundenkategorien"].astype("str")
    df_verspätung = df_verspätung.pivot(index="Konsolidierungsperioden", columns="Kundenkategorien",
                                            values="Durchschn. Verspätung")
    print(df_verspätung)

    df_einsparungen.to_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Konsolidierung\df_ergebniszusammenfassung" + ".csv", encoding="latin_1", sep=";")

    df_verspätung.to_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Konsolidierung\df_verspätungszusammenfassung" + ".csv",
        encoding="latin_1", sep=";")



