import pandas as pd

def transform_tarifmatrix(df_tarifmatrix_wide):

    df_tarif_matrix_melted = pd.melt(df_tarifmatrix_wide, id_vars="Gewicht", value_vars=df_tarifmatrix_wide.columns[1:],
                                     var_name="Distanz", value_name="Kosten")
    df_tarif_matrix_melted = df_tarif_matrix_melted.astype("float")
    df_tarif_matrix_melted.to_csv(path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Transportpreismatrix_TK_long.csv", index=False, sep=";",encoding="latin1", )
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
    df_touren = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Datensatz_TK_erweitert.csv", encoding="latin_1", sep=";", decimal=".")
    df_tarifmatrix_wide = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Transportpreismatrix_TK.csv", encoding="latin_1", sep=";", decimal=".", dtype= float)
    df_tarifmatrix_long = transform_tarifmatrix(df_tarifmatrix_wide)
    df_touren = assign_costs(df_tarifmatrix_long, df_touren)

    print(df_touren["Frachtkosten"])