import pandas as pd
from datetime import datetime, timedelta, date
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from e_knappsack_MR import *

def convertIDs(df_pattern, sequ_array):
    sequ_array_ext = []
    df_pattern = df_pattern.set_index("InternID")
    for i in sequ_array[:-1]:
        sequ_array_ext.append(df_pattern.loc[i, "ExternID"])
    sequ_array_ext.append(0)
    return sequ_array_ext

def changeDates(df_basedata_MR, df_pattern): #set all dates to pattern days
    df_basedata_MR = df_basedata_MR.sort_values(by= "Beladedatum")


    for index, row in df_basedata_MR[::-1].iterrows():
            for i in range(8):

                    try:
                        if df_pattern.loc[row["ID_Empfänger"],"Pattern"][row["Beladedatum"].dayofweek] == 0:
                            row["Beladedatum"] = row["Beladedatum"] - timedelta(days=1)
                        else:

                            #print(row["Beladedatum"].dayofweek)
                            df_basedata_MR.loc[index, "Beladedatum"] = row["Beladedatum"]
                            break
                    except IndexError:
                        row["Beladedatum"] = row["Beladedatum"] - timedelta(days=1)

    df_basedata_MR["Wochentag"]= df_basedata_MR["Beladedatum"].dt.dayofweek
    df_basedata_MR["Kalenderwoche"] = df_basedata_MR["Beladedatum"].dt.week
    #print(df_basedata_MR)
    return df_basedata_MR

def simple_MR(df_basedata_MR_filter, max_cap, MR_price, KW, tag, MR_ID):
    df_basedata_MR_filter = df_basedata_MR_filter.sort_values("Gewicht")
    #print(df_basedata_MR_filter)

    date = datetime.strptime("{} {} {}".format(tag+1, KW , 2022), "%w %W %Y")

    data_MR_tour = {"Beladedatum": '{d.day}.{d.month}.{d.year}'.format(d=date),
                    "Wochentag": date.weekday(),
                    "Monat" : date.month,
                     "Kalenderwoche": KW,
                     "ID_Empfänger": [[]],
                     "Gewicht": 0,
                     "Frachtkosten": MR_price,
                     "ID_Sendung":[[]],
                    "MR_ID": MR_ID,
                    "Frachtkosten_AF": df_basedata_MR_filter["Frachtkosten"].sum(),
                     }

    if df_basedata_MR_filter.empty == False:
        for index, row in df_basedata_MR_filter.iterrows():
            if data_MR_tour["Gewicht"] + row["Gewicht"]<= max_cap:
                if not row["ID_Empfänger"] in data_MR_tour["ID_Empfänger"][0]:
                    data_MR_tour["ID_Empfänger"][0].append(row["ID_Empfänger"])
                data_MR_tour["Gewicht"] += row["Gewicht"]
                data_MR_tour["ID_Sendung"][0].append(row["ID_Sendung"])
                df_basedata_MR_filter = df_basedata_MR_filter.drop(index)

        df_MR = pd.DataFrame(data=data_MR_tour)
        df_basedata_MR_filter = df_basedata_MR_filter.append(df_MR, ignore_index=True)
        df_basedata_MR_filter["MR_ID"] = MR_ID
        df_basedata_MR_filter["Frachtkosten_AF"] = df_basedata_MR_filter["Frachtkosten"]
        #print(df_basedata_MR_filter)
        return df_basedata_MR_filter

    else:
        df_MR = pd.DataFrame(data=data_MR_tour)
        df_basedata_MR_filter = df_basedata_MR_filter.append(df_MR, ignore_index=True)
        #print(df_basedata_MR_filter)
        return df_basedata_MR_filter

def knappsack_MR(df_basedata_MR_filter, max_cap, MR_price, KW, tag, MR_ID):
    df_basedata_MR_filter = df_basedata_MR_filter.sort_values("Gewicht")
    df_basedata_MR_filter = df_basedata_MR_filter.reset_index(drop=True)
    df_basedata_MR_filter = df_basedata_MR_filter.astype({"Gewicht" : float,
                                                          "Frachtkosten" : float})
    # print(df_basedata_MR_filter)

    date = datetime.strptime("{} {} {}".format(tag+1, KW, 2022), "%w %W %Y")

    data_MR_tour = {"Beladedatum": '{d.day}.{d.month}.{d.year}'.format(d=date),
                    "Wochentag": date.weekday(),
                    "Monat": date.month,
                    "Kalenderwoche": KW,
                    "ID_Empfänger": [[]],
                    "Gewicht": 0,
                    "Frachtkosten": MR_price,
                    "ID_Sendung": [[]],
                    "MR_ID": MR_ID,
                    "Frachtkosten_AF": df_basedata_MR_filter["Frachtkosten"].sum(),
                    }

    if df_basedata_MR_filter.empty == False:

        packed_items, dropped_items = knappsack(values = df_basedata_MR_filter["Frachtkosten"].values, weights = [df_basedata_MR_filter["Gewicht"].tolist()],capacities=[max_cap])

        for index, row in df_basedata_MR_filter.iterrows():
            if (index in packed_items): #(data_MR_tour["Gewicht"] + row["Gewicht"] <= max_cap) &
                if not row["ID_Empfänger"] in data_MR_tour["ID_Empfänger"][0]:
                    data_MR_tour["ID_Empfänger"][0].append(row["ID_Empfänger"])
                data_MR_tour["Gewicht"] += row["Gewicht"]
                data_MR_tour["ID_Sendung"][0].append(row["ID_Sendung"])
                df_basedata_MR_filter = df_basedata_MR_filter.drop(index)
            else:
                continue

        df_MR = pd.DataFrame(data=data_MR_tour)
        df_basedata_MR_filter["Frachtkosten_AF"] = df_basedata_MR_filter["Frachtkosten"]
        df_basedata_MR_filter = df_basedata_MR_filter.append(df_MR, ignore_index=True)
        df_basedata_MR_filter["MR_ID"] = MR_ID
        # print(df_basedata_MR_filter)
        return df_basedata_MR_filter

    else:
        df_MR = pd.DataFrame(data=data_MR_tour)
        df_basedata_MR_filter = df_basedata_MR_filter.append(df_MR, ignore_index=True)
        # print(df_basedata_MR_filter)
        return df_basedata_MR_filter

def calcMilkrun(df_basedata_MR, df_milkruns, df_pattern, df_basedata_no_MR, no_MR_weeks,MR_Knappsack):

    data_MR = {"MR_ID": [],
               "Kalenderwoche": [],
               "Wochentag": [],
               "Monat": [],
               "Fahrzeugtyp": [],
               "Fahrzeugkapazität": [],
               "Frachtgewicht":[],
               "Auslastung": [],
               "SequenzExt":[],
               "SequenzInt": []}

    df_MR_collected = pd.DataFrame(columns=["Beladedatum", "Wochentag", "Kalenderwoche", "ID_Empfänger", "Gewicht", "Frachtkosten","ID_Sendung", "MR_ID"])

    min_KW = df_basedata_MR["Beladedatum"].min().isocalendar()[1]
    max_KW = df_basedata_MR["Beladedatum"].max().isocalendar()[1]
    for KW in range(min_KW,max_KW+1):#range(df_basedata_MR["Kalenderwoche"].min(), df_basedata_MR["Kalenderwoche"].max()+1):

        for tag in range(0,4+1):
                df_milkruns_filter = df_milkruns.loc[df_milkruns["Wochentag"] == tag]

                for index, row in df_milkruns_filter.iterrows():
                    df_basedata_MR_filter = df_basedata_MR.loc[(df_basedata_MR["ID_Empfänger"].isin(row["Sequenz_extID"])) & (df_basedata_MR["Kalenderwoche"]== KW) & (df_basedata_MR["Wochentag"]== tag)]

                    if KW not in no_MR_weeks:
                        data_MR["MR_ID"].append(row["MR_ID"])
                        data_MR["Kalenderwoche"].append(KW)
                        data_MR["Wochentag"].append(tag)
                        data_MR["Monat"].append(date.month)
                        data_MR["Fahrzeugtyp"].append(row["Fahrzeugtyp"])
                        data_MR["Fahrzeugkapazität"].append(row["Kapazität"])
                        data_MR["Frachtgewicht"].append(df_basedata_MR_filter["Gewicht"].sum())
                        data_MR["Auslastung"].append(float(df_basedata_MR_filter["Gewicht"].sum())/float(row["Kapazität"]))
                        data_MR["SequenzExt"].append(row["Sequenz_extID"])
                        data_MR["SequenzInt"].append(row["Sequenz"])
                        df_data_MR = pd.DataFrame(data=data_MR)

                        if MR_Knappsack == True:
                            df_basedata_MR_applied = knappsack_MR(df_basedata_MR_filter, int(row["Kapazität"]),
                                                                  row["Tourkosten"], KW, tag, row["MR_ID"])
                        else:
                            df_basedata_MR_applied = simple_MR(df_basedata_MR_filter, row["Kapazität"], row["Tourkosten"],KW, tag, row["MR_ID"])
                        df_MR_collected = df_MR_collected.append(df_basedata_MR_applied, ignore_index=True)

                    else:
                        df_MR_collected = df_MR_collected.append(df_basedata_MR_filter, ignore_index=True)
                        #print(df_MR_collected)
                else:
                    continue

    df_MR_collected.to_csv(
                r"../00_Resources/Instances/Results/shipments_only_MR/df_only_MR_Sendungsdaten_"+instanzname+""+"_außer_KW"+str(no_MR_weeks)+"Knappsack_"+str(MR_Knappsack)+".csv",
                encoding="latin_1", sep=";", index=False)
    df_MR_collected = df_MR_collected.drop("MR_ID", axis=1)
    df_MR_collected = df_MR_collected.drop("Frachtkosten_AF", axis=1)

    df_MR_complete = pd.concat([df_MR_collected, df_basedata_no_MR])

    df_data_MR.to_csv(
                r"../00_Resources/Instances/Results/MR_capacity_usage/df_MR_Auslastung_"+instanzname+""+"_außer_KW"+str(no_MR_weeks)+"Knappsack_"+str(MR_Knappsack)+".csv",
                encoding="latin_1", sep=";", index=False)
    df_data_MR.to_csv(
                r"../00_Resources/Instances/Results/MR_capacity_usage/df_MR_Auslastung_"+instanzname+""+"_außer_KW"+str(no_MR_weeks)+"Knappsack_"+str(MR_Knappsack)+"_EU"+".csv",
                encoding="latin_1", sep=";", index=False, decimal=",")

    df_MR_complete.to_csv(
                r"../00_Resources/Instances/Results/shipments_all_customers/df_MR_Sendungsdaten_"+instanzname+""+"_außer_KW"+str(no_MR_weeks)+"Knappsack_"+str(MR_Knappsack)+".csv",
                encoding="latin_1", sep=";", index=False)
    df_MR_complete.to_csv(
                r"../00_Resources/Instances/Results/shipments_all_customers/df_MR_Sendungsdaten_"+instanzname+""+"_außer_KW"+str(no_MR_weeks)+"Knappsack_"+str(MR_Knappsack)+"_EU"+".csv",
                encoding="latin_1", sep=";", index=False, decimal=",")

    return df_MR_complete, df_data_MR, df_MR_collected

def diagrammdaten(df_data_MR, df_MR_complete, df_basedata, no_MR_weeks, MR_Knappsack):
    ###Ersparnis pro Woche Daten
    df_data_MR_KW = df_data_MR[["Kalenderwoche", "Auslastung"]].groupby("Kalenderwoche").mean()
    df_MR_complete_KW = df_MR_complete[["Kalenderwoche", "Frachtkosten"]].groupby("Kalenderwoche").sum()
    df_basedata_KW = df_basedata[["Kalenderwoche", "Frachtkosten"]].groupby("Kalenderwoche").sum()
    df_costs_compare_KW = df_MR_complete_KW.merge(df_basedata_KW, how="left", on='Kalenderwoche',
                                                  suffixes=("_MR", "_no_MR")).fillna(0)
    df_costs_compare_KW["MR_Ersparnis"] = df_costs_compare_KW["Frachtkosten_MR"] - df_costs_compare_KW[
        "Frachtkosten_no_MR"]
    df_costs_compare_KW["MR_Ersparnis_Prozent"] = (
                df_costs_compare_KW["MR_Ersparnis"] / df_costs_compare_KW["Frachtkosten_no_MR"]).round(4)
    df_costs_compare_KW = df_costs_compare_KW.join(df_data_MR_KW, on="Kalenderwoche", rsuffix=("mean_"))
    df_costs_compare_KW["MR_Ersparnis_Prozent_%"] = df_costs_compare_KW["MR_Ersparnis_Prozent"] * 100
    print(df_costs_compare_KW)
    df_costs_compare_KW.to_csv(
        r"../00_Resources/Instances/Results/MR_savings/df_MR_Einsparungen_" + instanzname + "" + "_außer_KW" + str(
            no_MR_weeks) + "Knappsack_" + str(MR_Knappsack) + ".csv",
        encoding="latin_1", sep=";", index=True)

def zusammenfassung(instanzname, no_MR_weeks, MR_Knappsack, df_AFNodes, df_pattern, df_data_MR_and_not_MR, df_MR_collected, df_milkruns, df_Var):
    data_zus = {"Instanzname": [instanzname],
                "no_MR_Wochen": [no_MR_weeks],
                "BaB":[MR_Knappsack],
                "AF_Nodes" : [list(df_AFNodes["ExternID"].values)],
                "Anzahl_AF_Nodes" : [len(list(df_AFNodes["ExternID"].values))],
                "MR_Nodes" : [list(df_pattern["ExternID"].values)],
                "Anzahl_MR_Nodes" : [len(list(df_pattern["ExternID"].values))],
                "Anzahl_MR_Tours" : [df_milkruns.shape[0]],
                "MR_Kosten_Woche": [df_milkruns["Tourkosten"].sum()],
                "MR_Nodes_Kosten_vorher": [df_Var[df_Var["ID_Empfänger"].isin(df_pattern["ExternID"].values)]["Frachtkosten"].sum()],
                "MR_Nodes_Kosten_nacher":[df_MR_collected["Frachtkosten"].sum()],
                "Alle_Nodes_voher" : [df_Var["Frachtkosten"].sum()],
                "Alle_Nodes_nachher": [df_data_MR_and_not_MR["Frachtkosten"].sum()],
                "Einsparung_alle": [1- (df_data_MR_and_not_MR["Frachtkosten"].sum() / df_Var["Frachtkosten"].sum())],
                "Einsparung_MR_Nodes": [1- (df_MR_collected["Frachtkosten"].sum()/ df_Var[df_Var["ID_Empfänger"].isin(df_pattern["ExternID"].values)]["Frachtkosten"].sum())],
    }
    df_zus = pd.DataFrame(data=data_zus)
    df_zus.to_csv(
        r"../00_Resources/Instances/Results/MR_summary/df_MR_Zusammenfassung_" + instanzname + "" + "_außer_KW" + str(
            no_MR_weeks) + "Knappsack_" + str(MR_Knappsack) + ".csv",
        encoding="latin_1", sep=";", index=False)


if __name__ == '__main__':
    no_MR_weeks = []
    instanzname = "1-1.33-1.33-SZ15Multi1.5Veh_cap13-600-1800"
    MR_Knappsack = True

    df_basedata = pd.read_csv(r"../00_Resources/Grunddaten/Datensatz_TK_fertig.csv", encoding="latin-1", sep=";",decimal=",") # ACHTUNG DECIMAL
    df_basedata["Beladedatum"] = pd.to_datetime(df_basedata["Beladedatum"], dayfirst=True)
    #df_basedata =  df_basedata.set_index("ID_Empfänger", drop= False)
    df_basedata["Wochentag"] = df_basedata["Beladedatum"].dt.dayofweek
    df_basedata["Kalenderwoche"] = df_basedata["Beladedatum"].dt.week
    df_basedata["Monat"] = df_basedata["Beladedatum"].dt.month
    df_basedata = df_basedata[["Beladedatum", "Wochentag", "Kalenderwoche","Monat", "ID_Empfänger", "Gewicht", "Frachtkosten","ID_Sendung"]]

    df_pattern = pd.read_csv(r"../00_Resources/Instances/Results/pattern/df_patterns_Instanz"+instanzname+".csv", encoding="latin-1", sep=";", dtype={"Montag": int,
                                                                                                                                                      "Dienstag": int,
                                                                                                                                                      "Mittwoch": int,
                                                                                                                                                      "Donnerstag": int,
                                                                                                                                                      "Freitag": int,})
    df_pattern["Pattern"] = df_pattern[['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag']].values.tolist()
    df_pattern = df_pattern.set_index("ExternID", drop=False)
    print(df_pattern)

    df_basedata_MR = df_basedata.loc[
        df_basedata["ID_Empfänger"].isin(df_pattern["ExternID"]) & (df_basedata["Wochentag"] != 5)]

    df_basedata_no_MR = df_basedata.loc[
        ~df_basedata["ID_Empfänger"].isin(df_pattern["ExternID"]) | (df_basedata["Wochentag"] == 5)]


    df_milkruns = pd.read_csv(r"../00_Resources/Instances/Results/tours/df_tours_Instanz"+instanzname+".csv", encoding="latin-1", sep=";",converters={'Sequenz': eval})
    df_milkruns["Sequenz_extID"] = df_milkruns.apply(lambda row : convertIDs(df_pattern,row["Sequenz"]), axis = 1)
    df_milkruns.to_csv(r"../00_Resources/Instances/Results/tours/df_tours_Instanz"+instanzname+".csv",encoding="latin_1", sep=";", index=False)

    df_AFNodes = pd.read_csv(r"../00_Resources/Instances/Results/AFnodes/df_AFNodes_Instanz"+instanzname+".csv", encoding="latin-1", sep=";")
    print(df_AFNodes)

    df_Var =  pd.read_csv(r"../00_Resources/pre_Analysis/Variabilitätsauswertung/Variabilitätsauswertung.csv", encoding="latin-1", sep=";")
    print(df_Var)

    df_basedata_MR = changeDates(df_basedata_MR, df_pattern) #Lieferdaten auf MR-Daten setzen

    df_basedata_MR.to_csv(
                r"../00_Resources/Instances/Results/MR_shifted_shipments/df_basedata_MR_"+instanzname+""+"_außer_KW"+str(no_MR_weeks)+"Knappsack_"+str(MR_Knappsack)+".csv",
                encoding="latin_1", sep=";")

    df_data_MR_and_not_MR, df_data_MR, df_MR_collected = calcMilkrun(df_basedata_MR, df_milkruns, df_pattern, df_basedata_no_MR, no_MR_weeks, MR_Knappsack)

    diagrammdaten(df_data_MR, df_data_MR_and_not_MR, df_basedata, no_MR_weeks, MR_Knappsack)

    zusammenfassung(instanzname, no_MR_weeks, MR_Knappsack, df_AFNodes, df_pattern, df_data_MR_and_not_MR, df_MR_collected, df_milkruns, df_Var)






