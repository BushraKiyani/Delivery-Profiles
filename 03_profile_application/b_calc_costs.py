import pandas as pd
import datetime as dt
from c_multiple_Knapsack import *

tarifart = "grundpreis + tonne"  # "grundpreis + tonne", "matrix"
preis_basis = 23.28
preis_tonne = 35.31

PAT = {
        5:
            [[1, 1, 1, 1, 1]],
        4:
            [[0, 1, 1, 1, 1],
             [1, 0, 1, 1, 1],
             [1, 1, 0, 1, 1],
             [1, 1, 1, 0, 1],
             [1, 1, 1, 1, 0]],

        3: [[0, 1, 0, 1, 1],
            [1, 0, 1, 0, 1],
            [1, 1, 0, 1, 0],
            [0, 1, 1, 0, 1],
            [1, 0, 1, 1, 0],
            ],

        2: [[1, 0, 1, 0, 0],
            [0, 1, 0, 1, 0],
            [0, 0, 1, 0, 1],
            [1, 0, 0, 1, 0],
            [0, 1, 0, 0, 1]],

        1: [[1, 0, 0, 0, 0],
            [0, 1, 0, 0, 0],
            [0, 0, 1, 0, 0],
            [0, 0, 0, 1, 0],
            [0, 0, 0, 0, 1]],
    }

def datumsliste(df_sendungen_ID):
    start = pd.to_datetime("01.01.2022")
    end = pd.to_datetime("31.12.2022")

    delta = end - start

    day_array= []
    weekday_array = []

    for i in range(delta.days + 1):
        day = pd.to_datetime(start + dt.timedelta(days=i))
        day_array.append(day)
        weekday_array.append(day.dayofweek)

    df_dates = pd.DataFrame(data={"Datum":day_array,
                                  "Wochentag": weekday_array})
    df_dates = df_dates.loc[~df_dates["Wochentag"].isin([5,6])]
    df_dates = df_dates.set_index("Datum", drop = False)
    #print(df_dates.head())
    #print(df_dates.tail())
    return df_dates

def add_to_data_dict(data_result_pattern,df_sendungen_ID_date, weekday , date, gewicht, ID_send, avg_delay):
    data_result_pattern["ID_Empfänger"].append(df_sendungen_ID_date["ID_Empfänger"].values[0])
    data_result_pattern["ID_Sendung"].append(ID_send)
    data_result_pattern["Beladedatum"].append(date)
    data_result_pattern["Gewicht"].append(gewicht)
    data_result_pattern["Distanz"].append(df_sendungen_ID_date["Distanz"].values[0])
    data_result_pattern["Wochentag"].append(weekday)
    data_result_pattern["Delay"].append(avg_delay)
    return data_result_pattern

def frachtkosten_berechnen(df_tarifmatrix_long, gewicht, distanz):

    if tarifart == "matrix":
        tarifmatrix_long_filtered = df_tarifmatrix_long[(df_tarifmatrix_long["Distanz"] <= distanz) & (df_tarifmatrix_long["Gewicht_kg"] <= gewicht)]
        return tarifmatrix_long_filtered.iloc[-1, -1]
    elif tarifart == "grundpreis + tonne":
        return preis_basis + gewicht * preis_tonne/1000

def cal_avg_delay(df_send, shippingdate):
    sum_delay = 0
    num_send = 0

    for index, row in df_send.iterrows():
        #print(shippingdate - row["Beladedatum"])
        sum_delay += (shippingdate - row["Beladedatum"]).days
        num_send += 1

    return sum_delay/num_send

def profilanwendung(speicherpfad_speziell):
    send_id_list =[]

    df_profile = pd.read_csv(
        r"../00_Resources/profile_results/Profilzuweisung/" + speicherpfad_speziell + ".csv",
        encoding="latin-1",
        sep=";")
    df_profile = df_profile.set_index("ID_Empfänger", drop=False)

    df_sendungen = pd.read_csv(
        r"../00_Resources/Grunddaten/Datensatz_TK_fertig.csv", encoding="latin-1",
        sep=";",decimal=",", dtype={"Gewicht": float, "Distanz": float, "Frachtkosten": float} )
    df_sendungen = df_sendungen.set_index("ID_Empfänger", drop=False)

    send_list = list(df_sendungen["ID_Sendung"].values)
    #print(send_list)
    gesamtgewicht = df_sendungen["Gewicht"].sum()


    df_sendungen["Beladedatum"] = pd.to_datetime(df_sendungen["Beladedatum"], dayfirst=True)
    df_sendungen["Wochentag"] = df_sendungen["Beladedatum"].dt.dayofweek
    df_profile["ID_Empfänger"] = df_profile["ID_Empfänger"].astype(int)

    df_sendungen_not_filter = df_sendungen.loc[(~df_sendungen["ID_Empfänger"].isin(df_profile["ID_Empfänger"])) | (df_sendungen["ID_Empfänger"].isin(df_profile["ID_Empfänger"]) & (df_sendungen["Wochentag"] == 5))]
    df_sendungen_not_filter = df_sendungen_not_filter[
        ["ID_Empfänger", "ID_Sendung", "Beladedatum", "Gewicht", "Distanz", "Frachtkosten", "Wochentag"]]

    for send in df_sendungen_not_filter["ID_Sendung"].values:
        #print(send)
        send_list.remove(send)

    #print("Gewicht voher= ", df_sendungen["Gewicht"].sum())
    df_sendungen = df_sendungen.loc[df_sendungen["ID_Empfänger"].isin(df_profile["ID_Empfänger"]) & (df_sendungen["Wochentag"] != 5)]
    #print("Summe Gewicht = ", df_sendungen["Gewicht"].sum() + df_sendungen_not_filter["Gewicht"].sum())
    #print("Gewicht Profil vorher:",df_sendungen["Gewicht"].sum())

    df_dates = datumsliste(df_sendungen)

    data_result_pattern = {
                            "ID_Empfänger": [],
                            "ID_Sendung": [],
                            "Beladedatum": [] ,
                            "Gewicht": [] ,
                            "Distanz": [] ,
                            "Wochentag": [],
                            "Delay": [],}

    for ID in df_sendungen["ID_Empfänger"].unique():
        #print(ID)
        df_sendungen_ID = df_sendungen.loc[df_sendungen["ID_Empfänger"] == ID]
        pattern = PAT[df_profile.loc[ID, "Frequenz"]][df_profile.loc[ID, "Pattern"]]

        df_sendungen_ID_date = pd.DataFrame(data= {"Gewicht": [],
                                                   "Beladedatum": [],
                                                   })

        for index, row in df_dates[::-1].iterrows():
            state = pattern[row["Wochentag"]]
            #print( df_sendungen_ID.loc[df_sendungen_ID["Beladedatum"] == index])
            if df_sendungen_ID.loc[df_sendungen_ID["Beladedatum"] == row["Datum"]].empty == False: #Alle Sendungen hinzufürgen nach dem Liefertag
                df_sendungen_ID_date = df_sendungen_ID_date.append(df_sendungen_ID[df_sendungen_ID["Beladedatum"] == row["Datum"]])
                #print(df_sendungen_ID_date.head())
                for i in df_sendungen_ID[df_sendungen_ID["Beladedatum"] == row["Datum"]]["ID_Sendung"].values: # itterieren über alle Sendungen an dem Tag und aus Liste streichen
                    send_id_list.append(int(i))
                    #print(i)
                    #print(send_list)
                    send_list.remove(i)

            if (state == 1) & (df_sendungen_ID_date.shape[0] != 0) & (df_sendungen_ID_date["Gewicht"].sum() <= 25000): #Summe unter 25000
                avg_delay = calc_avg_delay(df_sendungen_ID_date, row["Datum"])
                data_result_pattern = add_to_data_dict(data_result_pattern,df_sendungen_ID_date, weekday = row["Wochentag"], date = row["Datum"], gewicht = df_sendungen_ID_date["Gewicht"].sum(), ID_send= list(df_sendungen_ID_date["ID_Sendung"]), avg_delay = avg_delay)
                df_sendungen_ID_date = pd.DataFrame(data={"Gewicht": [],
                                                        "Beladedatum": [],
                                                        })

            elif (state == 1) & (df_sendungen_ID_date.shape[0] != 0) & (df_sendungen_ID_date["Gewicht"].sum() > 25000): #Summe über 25000
                df_sendungen_ID_date = df_sendungen_ID_date.reset_index(drop=True)

                df_touren_filter_ID_date_underweight = df_sendungen_ID_date[df_sendungen_ID_date["Gewicht"] <= 25000]
                df_touren_filter_ID_date_underweight = df_touren_filter_ID_date_underweight.reset_index(drop=True)
                capacities = [25000 for i in range(int(df_touren_filter_ID_date_underweight["Gewicht"].sum() / 25000))]
                capacities = [25000] if len(capacities) == 0 else capacities

                send_aufteilung, dropped_items = multiple_knappsack(values=list(df_touren_filter_ID_date_underweight["Gewicht"]),weights=list(df_touren_filter_ID_date_underweight["Gewicht"]), capacities=capacities)
                #print(df_sendungen_ID_date)
                for bin in send_aufteilung:
                    gewicht = 0
                    send_id = []
                    send_dates = []
                    verspätung = 0
                    for i in bin:
                        gewicht += df_touren_filter_ID_date_underweight.loc[i, "Gewicht"]
                        send_id.append(df_touren_filter_ID_date_underweight.loc[i, "ID_Sendung"])
                        send_dates.append(df_touren_filter_ID_date_underweight.loc[i, "Beladedatum"])


                    avg_delay = calc_avg_delay(df_touren_filter_ID_date_underweight, row["Datum"])
                    data_result_pattern = add_to_data_dict(data_result_pattern, df_touren_filter_ID_date_underweight, weekday = row["Wochentag"], date = row["Datum"], gewicht= gewicht, ID_send= send_id, avg_delay =avg_delay)

                if len(dropped_items) != 0:
                    gewicht = 0
                    send_id = []
                    send_dates = []
                    verspätung = 0
                    for i in dropped_items:
                        gewicht += df_touren_filter_ID_date_underweight.loc[i, "Gewicht"]
                        send_id.append(df_touren_filter_ID_date_underweight.loc[i, "ID_Sendung"])
                        send_dates.append(df_touren_filter_ID_date_underweight.loc[i, "Beladedatum"])

                    avg_delay = calc_avg_delay(df_touren_filter_ID_date_underweight, row["Datum"])

                    data_result_pattern = add_to_data_dict(data_result_pattern,
                                                               df_touren_filter_ID_date_underweight,
                                                               weekday=row["Wochentag"], date=row["Datum"],
                                                               gewicht=gewicht, ID_send=send_id, avg_delay = avg_delay)

                df_touren_filter_ID_date_overweight = df_sendungen_ID_date[df_sendungen_ID_date["Gewicht"] > 25000]

                for index_w, row_w in df_touren_filter_ID_date_overweight.iterrows():
                    avg_delay = 0
                    data_result_pattern = add_to_data_dict(data_result_pattern, df_touren_filter_ID_date_overweight, weekday = row_w["Wochentag"], date = row_w["Beladedatum"], gewicht= row_w["Gewicht"], ID_send= row_w["ID_Empfänger"], avg_delay=avg_delay)
                df_sendungen_ID_date = pd.DataFrame(data={"Gewicht": [],
                                                        "Beladedatum": [],
                                                        })

    df_result_pattern = pd.DataFrame(data=data_result_pattern)

    df_tarifmatrix_long = None
    if tarifart == "matrix":
        df_tarifmatrix_long = pd.read_csv(
            r"../00_Resources/Grunddaten/Transportpreismatrix_TK_long.csv", encoding="latin_1",
            sep=";")

    df_result_pattern["Frachtkosten"] = df_result_pattern.apply(lambda row_l: frachtkosten_berechnen(df_tarifmatrix_long, row_l["Gewicht"], row_l["Distanz"]),axis=1)

    df_result_pattern = df_result_pattern.astype({"ID_Empfänger": int, "Distanz": float, "Gewicht": float, "Frachtkosten": float})
    df_result_pattern.to_csv(
        path_or_buf=r"../00_Resources/profile_results/Ergebnisse/Pattern_results_data_only_" + speicherpfad_speziell + ".csv",
        encoding="latin_1", sep=";", decimal=".")

    df_result_pattern.to_csv(
        path_or_buf=r"../00_Resources/profile_results/Ergebnisse/Pattern_results_data_only_" + speicherpfad_speziell + "_EU" + ".csv",
        encoding="latin_1", sep=";", decimal=",")

    df_result = pd.concat([df_result_pattern, df_sendungen_not_filter], ignore_index=True)
    df_result = df_result.astype({"ID_Empfänger": int, "Distanz": float, "Gewicht": float, "Frachtkosten": float})
    df_result.to_csv(
        path_or_buf=r"../00_Resources/profile_results/Ergebnisse/Pattern_results_data_" + speicherpfad_speziell +".csv",
        encoding="latin_1", sep=";", decimal=".")

    df_result.to_csv(
        path_or_buf=r"../00_Resources/profile_results/Ergebnisse/Pattern_results_data_" + speicherpfad_speziell + "_EU" +".csv",
        encoding="latin_1", sep=";", decimal=",")

    print("Ergebnis", df_result["Frachtkosten"].sum())
    print("Gesamtgewicht", df_result["Gewicht"].sum())
    print("Gewicht fehlt:", df_result["Gewicht"].sum()-gesamtgewicht)
    print("Gewicht Profil nachher:", df_result_pattern["Gewicht"].sum())

    return df_result["Frachtkosten"].sum()

###################################################################################################
def calc_avg_delay(df_send, shippingdate):
    sum_delay = 0
    num_send = 0

    for index, row in df_send.iterrows():
        #print(shippingdate - row["Beladedatum"])
        sum_delay += (shippingdate - row["Beladedatum"]).days
        num_send += 1

    return sum_delay / num_send

def add_to_data_list(data_list, df_sendungen_ID_date, weekday, date, gewicht, ID_send, avg_delay):
    data_list.append([
        df_sendungen_ID_date["ID_Empfänger"].values[0],
        ID_send,
        date,
        gewicht,
        df_sendungen_ID_date["Euc_Distance"].values[0],
        weekday,
        avg_delay
    ])
    return data_list
def datumsliste1(df, date_column):
    # Convert the column to datetime to ensure it's a valid date
    df.loc[:, date_column] = pd.to_datetime(df[date_column])

    # Define the start and end dates based on the min and max dates in the column
    start = df[date_column].min() - pd.DateOffset(weeks=1)
    end = df[date_column].max() + pd.DateOffset(weeks=1)

    delta = end - start

    day_array = []
    weekday_array = []

    for i in range(delta.days + 1):
        day = pd.to_datetime(start + pd.Timedelta(days=i))
        day_array.append(day)
        weekday_array.append(day.dayofweek)

    df_dates = pd.DataFrame(data={"Datum": day_array, "Wochentag": weekday_array})
    df_dates = df_dates.loc[~df_dates["Wochentag"].isin([5,6])]
    df_dates = df_dates.set_index("Datum", drop=False)

    return df_dates
def profile_application(df_added_freightcost,df_profile):
    df_profile = df_profile.set_index("ID_Empfänger", drop=False)
    df_added_freightcost = df_added_freightcost.set_index("ID_Empfänger", drop=False)
    send_list = list(df_added_freightcost["ID_Sendung"].values)
    gesamtgewicht = df_added_freightcost["Gewicht"].sum()
    df_added_freightcost["Beladedatum"] = pd.to_datetime(df_added_freightcost["Beladedatum"])
    df_added_freightcost["Wochentag"] = df_added_freightcost["Beladedatum"].dt.dayofweek
    df_profile["ID_Empfänger"] = df_profile["ID_Empfänger"].astype(int)
    df_shipments_not_filter = df_added_freightcost.loc[(~df_added_freightcost["ID_Empfänger"].isin(df_profile["ID_Empfänger"])) | (df_added_freightcost["ID_Empfänger"].isin(df_profile["ID_Empfänger"]) & (df_added_freightcost["Wochentag"] == 5))]
    df_shipments_not_filter = df_shipments_not_filter[
        ["ID_Empfänger", "ID_Sendung", "Beladedatum", "Gewicht", "Euc_Distance", "Frachtkosten", "Wochentag"]]
    # Convert the "ID_Sendung" column to a set
    ids_to_remove = set(df_shipments_not_filter["ID_Sendung"])
    # Remove elements from send_list using set difference
    send_list = list(set(send_list) - ids_to_remove)
    df_shipments_profile = df_added_freightcost.loc[df_added_freightcost["ID_Empfänger"].isin(df_profile["ID_Empfänger"]) & (df_added_freightcost["Wochentag"] != 5)]
    df_dates = datumsliste1(df_shipments_profile, 'Beladedatum')
    data_result_pattern = []
    send_id_list = []
    send_list_copy = send_list[:]  # Create a copy of send_list

    for ID in df_shipments_profile["ID_Empfänger"].unique():
        df_sendungen_ID = df_shipments_profile.loc[df_shipments_profile["ID_Empfänger"] == ID]
        pattern = PAT[df_profile.loc[ID, "Frequenz"]][df_profile.loc[ID, "Pattern"]]
        df_sendungen_ID_date = pd.DataFrame(data={"Gewicht": [], "Beladedatum": []})

        for index, row in df_dates[::-1].iterrows():
            state = pattern[row["Wochentag"]]
            if not df_sendungen_ID.loc[df_sendungen_ID["Beladedatum"] == row["Datum"]].empty:
                df_sendungen_ID_date = pd.concat([df_sendungen_ID_date, df_sendungen_ID[df_sendungen_ID["Beladedatum"] == row["Datum"]]])
                for i in df_sendungen_ID[df_sendungen_ID["Beladedatum"] == row["Datum"]]["ID_Sendung"].values:
                    send_id_list.append(int(i))
                    send_list_copy.remove(i)  # Use send_list_copy here
            if (state == 1) & (df_sendungen_ID_date.shape[0] != 0) & (df_sendungen_ID_date["Gewicht"].sum() <= 25000):
                avg_delay = calc_avg_delay(df_sendungen_ID_date, row["Datum"])
                data_result_pattern = add_to_data_list(data_result_pattern, df_sendungen_ID_date, weekday=row["Wochentag"], date=row["Datum"], gewicht=df_sendungen_ID_date["Gewicht"].sum(), ID_send=list(df_sendungen_ID_date["ID_Sendung"]), avg_delay=avg_delay)
                df_sendungen_ID_date = pd.DataFrame(data={"Gewicht": [],
                                                            "Beladedatum": [],
                                                            })

    # Create the DataFrame from the list of lists
    df_result_pattern = pd.DataFrame(data_result_pattern, columns=["ID_Empfänger", "ID_Sendung", "Beladedatum", "Gewicht", "Distance", "Wochentag", "Delay"])
    df_result_pattern["ID_Empfänger"] = df_result_pattern["ID_Empfänger"].astype(int)
    df_result_pattern["ID_Sendung"] = df_result_pattern["ID_Sendung"].apply(lambda x: [int(i) for i in x])
    print("Patterns have have been added.")
    return df_result_pattern


if __name__ == '__main__':
    speicherpfad_speziell= "['ZZZ', 'GRAU', 'BLAU', 'GELB', 'GRÜN']var_gewicht1.33_var_frequenz1.33_mindest_frequenz1"
    frachtkosten = profilanwendung(speicherpfad_speziell)