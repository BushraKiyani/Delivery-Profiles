import pandas as pd

def add_distance(df_touren_koordinaten,dist_matrix,columnname):
    distance_array = []
    for index, row in df_touren_koordinaten.iterrows():
        try:
            distance_array.append(dist_matrix.loc[row["Recipient_ID"], row["Stadt_Absender"]])
        except KeyError:
            distance_array.append(dist_matrix.loc[str(row["Recipient_ID"]), row["Stadt_Absender"]])
    df_touren_koordinaten[columnname] = distance_array
    return df_touren_koordinaten

def add_freightcosts(df_touren_distanzen, tarifmatrix_long, columnname):
    Freight_Cost_array = []
    for index, row in df_touren_distanzen.iterrows():
        tarifmatrix_long_filtered = tarifmatrix_long[
            (tarifmatrix_long["Distanz"] <= row["Distanz"]) & (
                        tarifmatrix_long["Weight_kg"] <= row["Weight"])]
        Freight_Cost_array.append(tarifmatrix_long_filtered.iloc[-1, -1])
    df_touren_distanzen[columnname] = Freight_Cost_array

    #df_touren_distanzen.to_csv(path_or_buf="Resources/TestData_TK_aufbereitet.csv", sep=";",encoding="latin1", decimal=".")
    return df_touren_distanzen


if __name__ == "__main__":
    df_touren_koordinaten = pd.read_csv(
        r"../00_Resources/Basic_Data/Datasatz_TK_bereinigt.csv", encoding="latin-1",
        sep=";", thousands=",", dtype={"Weight": float})

    dist_matrix_eukl = pd.read_csv(
        r"../00_Resources/Basic_Data/distance_matrix_eukl.csv",
        encoding="latin-1", sep=";", index_col="Recipient_ID")

    df_touren_koordinaten_dist_eukl = add_distance(df_touren_koordinaten,dist_matrix_eukl, "Distanz")

    df_Tarifmatrix_long = pd.read_csv(r"../00_Resources/Basic_Data/Transportpreismatrix_TK_long.csv", encoding="latin-1", sep=";", dtype={"Weight_kg": float, "Distanz":float})
    df_touren_koordinaten_Freight_Cost = add_freightcosts(df_touren_koordinaten_dist_eukl,df_Tarifmatrix_long, "Freight_Cost")
    df_touren_koordinaten_Freight_Cost.to_csv(
        path_or_buf=r"../00_Resources/Basic_Data/Datasatz_TK_fertig.csv", sep=";",
        encoding="latin1", decimal=".")