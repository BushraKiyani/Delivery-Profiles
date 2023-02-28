import pandas as pd

def transform_tarifmatrix(df_tarifmatrix_wide):

    df_tarif_matrix_melted = pd.melt(df_tarifmatrix_wide, id_vars="Gewicht_kg", value_vars=df_tarifmatrix_wide.columns[1:],
                                     var_name="Distanz", value_name="Kosten")
    df_tarif_matrix_melted = df_tarif_matrix_melted.astype("float")
    return df_tarif_matrix_melted

def assign_costs(df_tarifmatrix_long, df_touren):
    frachtkosten_array = []
    for index, row in df_touren.iterrows():
        print(df_tarifmatrix_long)
        df_tarifmatrix_long_filtered = df_tarifmatrix_long[(df_tarifmatrix_long["Distanz"] <= row["Distanz"]) & (df_tarifmatrix_long["Gewicht"] <= row["Gewicht"])]
        print(df_tarifmatrix_long_filtered)
        frachtkosten_array.append(df_tarifmatrix_long_filtered.iloc[-1, -1])
    df_touren["Frachtkosten"] = frachtkosten_array
    return df_touren

if __name__ == "__main__":
    df_tarifmatrix_wide = pd.read_csv(r"../00_Resources/Grunddaten/Transportpreismatrix_TK.csv", encoding="latin_1", sep=";", decimal=".", dtype= float)
    df_tarifmatrix_long = transform_tarifmatrix(df_tarifmatrix_wide)
    df_tarifmatrix_long.to_csv(
        path_or_buf=r"../00_Resources/Grunddaten/Transportpreismatrix_TK_long.csv",
        index=False, sep=";", encoding="latin1", )
