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


def add_freightcosts(df_touren_distanzen, tarifmatrix_long, df_freightcost_path,  columnname):
    df_touren_distanzen[['Real_Distance', 'Duration', 'Euc_Distance','Gewicht']] = df_touren_distanzen[['Real_Distance', 'Duration', 'Euc_Distance','Gewicht']].astype(float)
    frachtkosten_array = []
    for index, row in df_touren_distanzen.iterrows():
        tarifmatrix_long_filtered = tarifmatrix_long[
            (tarifmatrix_long["Distanz"].values <= row["Euc_Distance"]) & (
                        tarifmatrix_long["Gewicht_kg"].values <= row["Gewicht"])]
        frachtkosten_array.append(tarifmatrix_long_filtered.iloc[-1, -1])
    df_touren_distanzen[columnname] = frachtkosten_array

    df_touren_distanzen.to_csv(path_or_buf= df_freightcost_path, sep=";",encoding="latin1", decimal=".")
    print(f"Freight costs have been added and file is saved in: {df_freightcost_path}")
    return df_touren_distanzen
def add_costs(df_touren_distanzen,transport_preis,df_freightcost_path, columnname):
    df_tarifmatrix_long = transform_tarifmatrix(transport_preis)
    df_added_freightcost = add_freightcosts(df_touren_distanzen, df_tarifmatrix_long, df_freightcost_path, columnname)
    return df_added_freightcost

######################### Recalculated Cost ########################

def add_new_freightcosts(df_touren_distanzen, tarifmatrix_long, columnname, new_freightcost_path):
    df_touren_distanzen[['Distance','Gewicht']] = df_touren_distanzen[['Distance','Gewicht']].astype(float)
    frachtkosten_array = []
    for index, row in df_touren_distanzen.iterrows():
        tarifmatrix_long_filtered = tarifmatrix_long[
            (tarifmatrix_long["Distanz"].values <= row["Distance"]) & (
                        tarifmatrix_long["Gewicht_kg"].values <= row["Gewicht"])]
        frachtkosten_array.append(tarifmatrix_long_filtered.iloc[-1, -1])
    df_touren_distanzen[columnname] = frachtkosten_array

    df_touren_distanzen.to_csv(path_or_buf=new_freightcost_path, sep=";",encoding="latin1", decimal=".")
    print(f"Freight costs have been recalculated and file is saved in: {new_freightcost_path}")
    return df_touren_distanzen
def recalulate_costs(df_touren_distanzen,transport_preis,columnname, new_freightcost_path):
    df_tarifmatrix_long = transform_tarifmatrix(transport_preis)
    df_added_freightcost = add_new_freightcosts(df_touren_distanzen, df_tarifmatrix_long, columnname, new_freightcost_path)
    return df_added_freightcost


if __name__ == "__main__":
    df_tarifmatrix_wide = pd.read_csv(r"../00_Resources/Grunddaten/Transportpreismatrix_TK.csv", encoding="latin_1", sep=";", decimal=".", dtype= float)
    df_tarifmatrix_long = transform_tarifmatrix(df_tarifmatrix_wide)
    df_tarifmatrix_long.to_csv(
        path_or_buf=r"../00_Resources/Grunddaten/Transportpreismatrix_TK_long.csv",
        index=False, sep=";", encoding="latin1", )
