import pandas as pd

########################################################################################

def evaluation_after_KW1(df, df_frequency_path, df_weight_path):

    df["Gewicht"] = pd.to_numeric(df["Gewicht"], errors="coerce")
    df_weight = df.groupby(["Kalenderwoche", "ID_Empfänger"])["Gewicht"].sum().unstack()
    df_frequenz = df.groupby(["Kalenderwoche", "ID_Empfänger"])["Gewicht"].count().unstack()
# add 0 where df_gewicht and df_frequenz have NaN values
    df_frequenz = df_frequenz.fillna(0)
    df_weight = df_weight.fillna(0)

    df_frequenz = df_frequenz.astype(float)
    df_weight = df_weight.astype(float)

    df_frequenz.to_csv(
        df_frequency_path,
        encoding="latin_1", sep=";")
    df_weight.to_csv(
       df_weight_path,
        encoding="latin_1", sep=";")
    print(f"Frequencies and weights have been calculated and saved in: {df_frequency_path} and {df_weight_path}")

    return df_frequenz, df_weight
def variability_evaluation(df_frequenz, df_weight, df_touren, variability_path, variability_path_EU):
    df_touren["Frachtkosten"] = pd.to_numeric(df_touren["Frachtkosten"], errors="coerce")
    df_auswertung = pd.DataFrame()

    df_auswertung["ID_Empfänger"] = df_touren["ID_Empfänger"].unique()
    df_auswertung.set_index("ID_Empfänger", inplace=True)

    df_auswertung["avg_Gewicht"] = df_weight.mean()
    df_auswertung["avg_Frequenz"] = df_frequenz.mean()

    df_auswertung["std_Gewicht"] = df_weight.std()
    df_auswertung["std_Frequenz"] = df_frequenz.std()

    df_auswertung["variability_Gewicht"] = df_auswertung["std_Gewicht"] / df_auswertung["avg_Gewicht"]
    df_auswertung["variability_Frequenz"] = df_auswertung["std_Frequenz"] / df_auswertung["avg_Frequenz"]

    df_auswertung["Frachtkosten"] = df_touren.groupby("ID_Empfänger")["Frachtkosten"].sum()
    df_auswertung["Sendungen"] = df_touren.groupby("ID_Empfänger")["Frachtkosten"].count()
    df_auswertung["Gewicht"] = df_touren.groupby("ID_Empfänger")["Gewicht"].sum()

    #df_auswertung["Profilkunde"] = True

    df_auswertung = df_auswertung.astype({'avg_Gewicht': 'float64',
                                          'avg_Frequenz': 'float64',
                                          'std_Gewicht': 'float64',
                                          'std_Frequenz': 'float64',
                                          'variability_Gewicht': 'float64',
                                          'variability_Frequenz': 'float64',
                                          'Frachtkosten': 'float',
                                          'Sendungen': 'int',
                                          'Gewicht': 'float'
                                          })
    df_auswertung.reset_index(inplace=True)

    df_auswertung.to_csv(variability_path,
                         encoding="latin_1", sep=";", index_label="ID_Empfänger")
    df_auswertung.to_csv(variability_path_EU,
                         encoding="latin_1", sep=";", index_label="ID_Empfänger", decimal=',')
    print(f"Variablity analysis has been done and results are saved in: {variability_path} and European version: {variability_path_EU}")

    return df_auswertung


