import pandas as pd

def add_distance(df_touren_koordinaten,dist_matrix,columnname):
    distance_array = []
    for index, row in df_touren_koordinaten.iterrows():
        try:
            distance_array.append(dist_matrix.loc[row["ID_Empfänger"], row["Stadt_Absender"]])
        except KeyError:
            distance_array.append(dist_matrix.loc[str(row["ID_Empfänger"]), row["Stadt_Absender"]])
    df_touren_koordinaten[columnname] = distance_array
    return df_touren_koordinaten

def add_freightcosts(df_touren_distanzen, tarifmatrix_long, columnname):
    frachtkosten_array = []
    for index, row in df_touren_distanzen.iterrows():
        tarifmatrix_long_filtered = tarifmatrix_long[
            (tarifmatrix_long["Distanz"] <= row["Distanz"]) & (
                        tarifmatrix_long["Gewicht"] <= row["Gewicht"])]
        frachtkosten_array.append(tarifmatrix_long_filtered.iloc[-1, -1])
    df_touren_distanzen[columnname] = frachtkosten_array

    #df_touren_distanzen.to_csv(path_or_buf="Resources/Testdaten_TK_aufbereitet.csv", sep=";",encoding="latin1", decimal=".")
    return df_touren_distanzen


if __name__ == "__main__":
    df_touren_koordinaten = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Datensatz_TK_bereinigt.csv", encoding="latin-1",
        sep=";", thousands=",", dtype={"Gewicht": float})

    dist_matrix_eukl = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\distance_matrix_eukl.csv",
        encoding="latin-1", sep=";", index_col="ID_Empfänger")

    df_touren_koordinaten_dist_eukl = add_distance(df_touren_koordinaten,dist_matrix_eukl, "Distanz")

    df_Tarifmatrix_long = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Transportpreismatrix_TK_long.csv", encoding="latin-1", sep=";", dtype={"Gewicht": float, "Distanz":float})
    df_touren_koordinaten_frachtkosten = add_freightcosts(df_touren_koordinaten_dist_eukl,df_Tarifmatrix_long, "Frachtkosten")
    df_touren_koordinaten_frachtkosten.to_csv(
        path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Datensatz_TK_fertig.csv", sep=";",
        encoding="latin1", decimal=".")