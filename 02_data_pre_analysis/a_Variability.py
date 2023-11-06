import pandas as pd

########################################################################################

def evaluation_after_KW1(df, df_frequency_path, df_weight_path):

    df["Weight"] = pd.to_numeric(df["Weight"], errors="coerce")
    df_weight = df.groupby(["Calendar_Week", "Recipient_ID"])["Weight"].sum().unstack()
    df_Frequency = df.groupby(["Calendar_Week", "Recipient_ID"])["Weight"].count().unstack()
# add 0 where df_Weight and df_Frequency have NaN values
    df_Frequency = df_Frequency.fillna(0)
    df_weight = df_weight.fillna(0)

    df_Frequency = df_Frequency.astype(float)
    df_weight = df_weight.astype(float)

    df_Frequency.to_csv(
        df_frequency_path,
        encoding="latin_1", sep=";")
    df_weight.to_csv(
       df_weight_path,
        encoding="latin_1", sep=";")
    print(f"Frequencies and weights have been calculated and saved in: {df_frequency_path} and {df_weight_path}")

    return df_Frequency, df_weight
def variability_evaluation(df_Frequency, df_weight, df_touren, variability_path, variability_path_EU):
    df_touren["Freight_Cost"] = pd.to_numeric(df_touren["Freight_Cost"], errors="coerce")
    df_auswertung = pd.DataFrame()

    df_auswertung["Recipient_ID"] = df_touren["Recipient_ID"].unique()
    df_auswertung.set_index("Recipient_ID", inplace=True)

    df_auswertung["avg_Weight"] = df_weight.mean()
    df_auswertung["AVG_Frequency"] = df_Frequency.mean()

    df_auswertung["std_Weight"] = df_weight.std()
    df_auswertung["STD_Frequency"] = df_Frequency.std()

    df_auswertung["Variability_Weight"] = df_auswertung["std_Weight"] / df_auswertung["avg_Weight"]
    df_auswertung["Variability_Frequency"] = df_auswertung["STD_Frequency"] / df_auswertung["AVG_Frequency"]

    df_auswertung["Freight_Cost"] = df_touren.groupby("Recipient_ID")["Freight_Cost"].sum()
    df_auswertung["Shipments"] = df_touren.groupby("Recipient_ID")["Freight_Cost"].count()
    df_auswertung["Weight"] = df_touren.groupby("Recipient_ID")["Weight"].sum()

    #df_auswertung["ProfilRecipient"] = True

    df_auswertung = df_auswertung.astype({'avg_Weight': 'float64',
                                          'AVG_Frequency': 'float64',
                                          'std_Weight': 'float64',
                                          'STD_Frequency': 'float64',
                                          'Variability_Weight': 'float64',
                                          'Variability_Frequency': 'float64',
                                          'Freight_Cost': 'float',
                                          'Shipments': 'int',
                                          'Weight': 'float'
                                          })
    df_auswertung.reset_index(inplace=True)

    df_auswertung.to_csv(variability_path,
                         encoding="latin_1", sep=";", index_label="Recipient_ID")
    df_auswertung.to_csv(variability_path_EU,
                         encoding="latin_1", sep=";", index_label="Recipient_ID", decimal=',')
    print(f"Variablity analysis has been done and results are saved in: {variability_path} and European version: {variability_path_EU}")

    return df_auswertung


