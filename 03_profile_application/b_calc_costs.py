import pandas as pd
import datetime as dt

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
def profile_application(df_added_freightcost,df_profile,df_assigned_profile_path, df_result_path, df_shipments_profile_path):
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
    df_shipments_profile.to_csv(
        path_or_buf= df_shipments_profile_path, encoding="latin_1", sep=";", decimal=".")
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
    df_result_pattern = pd.DataFrame(data_result_pattern, columns=["ID_Empfänger", "ID_Sendung", "Beladedatum", "Gewicht", "Euc_Distance", "Wochentag", "Delay"])
    df_result_pattern["ID_Empfänger"] = df_result_pattern["ID_Empfänger"].astype(int)
    df_result_pattern["ID_Sendung"] = df_result_pattern["ID_Sendung"].apply(lambda x: [int(i) for i in x])
    df_result_pattern.to_csv(
        path_or_buf=df_assigned_profile_path,sep=";", encoding="latin1", decimal=".", index=False)

    df_result = pd.concat([df_result_pattern, df_shipments_not_filter], ignore_index=True)
    df_result = df_result.astype({"ID_Empfänger": int, "Euc_Distance": float, "Gewicht": float, "Frachtkosten": float})
    df_result.to_csv(
        path_or_buf= df_result_path, encoding="latin_1", sep=";", decimal=".")

    print(f"Patterns have have been added and saved in: {df_assigned_profile_path} and in: {df_result_path}")
    return df_result_pattern

