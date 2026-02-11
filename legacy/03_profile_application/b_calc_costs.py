import pandas as pd
import datetime as dt
from config import *

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
        #print(shippingdate - row["Loading_Date"])
        sum_delay += (shippingdate - row["Loading_Date"]).days
        num_send += 1

    return sum_delay / num_send

def add_to_data_list(data_list, df_Shipments_ID_date, weekday, date, Weight, ID_send, avg_delay):
    data_list.append([
        df_Shipments_ID_date["Recipient_ID"].values[0],
        ID_send,
        date,
        Weight,
        df_Shipments_ID_date["Euc_Distance"].values[0],
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

    df_dates = pd.DataFrame(data={"Datum": day_array, "Weekday": weekday_array})
    df_dates = df_dates.loc[~df_dates["Weekday"].isin([5,6])]
    df_dates = df_dates.set_index("Datum", drop=False)

    return df_dates
def profile_application(df_added_freightcost, df_profile, df_assigned_profile_path, df_result_path, df_shipments_profile_path, df_clustered_shipments_profile_path, df_clustered_assigned_profile_path, df_clustered_result_path, clustered="No"):
    df_profile = df_profile.set_index("Recipient_ID", drop=False)
    df_added_freightcost = df_added_freightcost.set_index("Recipient_ID", drop=False)
    send_list = list(df_added_freightcost["Shipment_ID"].values)
    gesamtWeight = df_added_freightcost["Weight"].sum()
    df_added_freightcost["Loading_Date"] = pd.to_datetime(df_added_freightcost["Loading_Date"])
    df_added_freightcost["Weekday"] = df_added_freightcost["Loading_Date"].dt.dayofweek
    df_profile["Recipient_ID"] = df_profile["Recipient_ID"].astype(int)
    df_shipments_not_filter = df_added_freightcost.loc[(~df_added_freightcost["Recipient_ID"].isin(df_profile["Recipient_ID"])) | (df_added_freightcost["Recipient_ID"].isin(df_profile["Recipient_ID"]) & (df_added_freightcost["Weekday"] == 5))]
    df_shipments_not_filter = df_shipments_not_filter[
        ["Recipient_ID", "Shipment_ID", "Loading_Date", "Weight", "Euc_Distance", "Freight_Cost", "Weekday"]]
    # Convert the "Shipment_ID" column to a set
    ids_to_remove = set(df_shipments_not_filter["Shipment_ID"])
    # Remove elements from send_list using set difference
    send_list = list(set(send_list) - ids_to_remove)
    df_shipments_profile = df_added_freightcost.loc[df_added_freightcost["Recipient_ID"].isin(df_profile["Recipient_ID"]) & (df_added_freightcost["Weekday"] != 5)]
    df_dates = datumsliste1(df_shipments_profile, 'Loading_Date')
    data_result_pattern = []
    send_id_list = []
    send_list_copy = send_list[:]  # Create a copy of send_list

    for ID in df_shipments_profile["Recipient_ID"].unique():
        df_Shipments_ID = df_shipments_profile.loc[df_shipments_profile["Recipient_ID"] == ID]
        pattern = PAT[df_profile.loc[ID, "Frequency"]][df_profile.loc[ID, "Pattern"]]
        df_Shipments_ID_date = pd.DataFrame(data={"Weight": [], "Loading_Date": []})

        for index, row in df_dates[::-1].iterrows():
            state = pattern[row["Weekday"]]
            if not df_Shipments_ID.loc[df_Shipments_ID["Loading_Date"] == row["Datum"]].empty:
                df_Shipments_ID_date = pd.concat([df_Shipments_ID_date, df_Shipments_ID[df_Shipments_ID["Loading_Date"] == row["Datum"]]])
                for i in df_Shipments_ID[df_Shipments_ID["Loading_Date"] == row["Datum"]]["Shipment_ID"].values:
                    send_id_list.append(int(i))
                    send_list_copy.remove(i)  # Use send_list_copy here
            if (state == 1) & (df_Shipments_ID_date.shape[0] != 0) & (df_Shipments_ID_date["Weight"].sum() <= 25000):
                avg_delay = calc_avg_delay(df_Shipments_ID_date, row["Datum"])
                data_result_pattern = add_to_data_list(data_result_pattern, df_Shipments_ID_date, weekday=row["Weekday"], date=row["Datum"], Weight=df_Shipments_ID_date["Weight"].sum(), ID_send=list(df_Shipments_ID_date["Shipment_ID"]), avg_delay=avg_delay)
                df_Shipments_ID_date = pd.DataFrame(data={"Weight": [],
                                                            "Loading_Date": [],
                                                            })

    # Create the DataFrame from the list of lists
    df_result_pattern = pd.DataFrame(data_result_pattern, columns=["Recipient_ID", "Shipment_ID", "Loading_Date", "Weight", "Euc_Distance", "Weekday", "Delay"])
    df_result_pattern["Recipient_ID"] = df_result_pattern["Recipient_ID"].astype(int)
    df_result_pattern["Shipment_ID"] = df_result_pattern["Shipment_ID"].apply(lambda x: [int(i) for i in x])

    df_result = pd.concat([df_result_pattern, df_shipments_not_filter], ignore_index=True)
    df_result = df_result.astype({"Recipient_ID": int, "Euc_Distance": float, "Weight": float, "Freight_Cost": float})
    df_added_freightcost.to_csv(path_or_buf= df_freightcost_path, sep=";", encoding="latin1", decimal=".",
                                index=False)
    print(f"Weekdays are added and file is saved in: {df_freightcost_path}")

    if clustered == "Yes":
        df_result_pattern.to_csv(df_clustered_assigned_profile_path, sep=";", encoding="latin1", decimal=".",
                                 index=False)
        df_result.to_csv(df_clustered_result_path, encoding="latin_1", sep=";", decimal=".")
        df_shipments_profile.to_csv(df_clustered_shipments_profile_path, encoding="latin_1", sep=";", decimal=".")
        print(f"Clustered Patterns have been added and saved in: {df_clustered_assigned_profile_path}, {df_clustered_result_path} and in: {df_clustered_shipments_profile_path}")
    else:
        df_result_pattern.to_csv(df_assigned_profile_path, sep=";", encoding="latin1", decimal=".", index=False)
        df_result.to_csv(df_result_path, encoding="latin_1", sep=";", decimal=".")
        df_shipments_profile.to_csv(df_shipments_profile_path, encoding="latin_1", sep=";", decimal=".")
        print(f"Patterns have been added and saved in: {df_shipments_profile_path}, {df_assigned_profile_path} and in: {df_result_path}")

    return df_result_pattern

