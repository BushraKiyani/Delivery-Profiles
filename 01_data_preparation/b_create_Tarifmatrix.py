import pandas as pd

def transform_tarifmatrix(df_tarifmatrix_wide):

    df_tarif_matrix_melted = pd.melt(df_tarifmatrix_wide, id_vars="Gewicht_kg", value_vars=df_tarifmatrix_wide.columns[1:],
                                     var_name="Euc_Distance", value_name="Kosten")
    df_tarif_matrix_melted = df_tarif_matrix_melted.astype("float")
    return df_tarif_matrix_melted

def frachtkosten_berechnen(df_tarifmatrix_long, gewicht, distanz, tarifart, preis_basis, preis_tonne ):
    if tarifart == "matrix":
        tarifmatrix_long_filtered = df_tarifmatrix_long[
            (df_tarifmatrix_long["Euc_Distance"] <= distanz) &
            (df_tarifmatrix_long["Gewicht_kg"] <= gewicht)
        ]
        return tarifmatrix_long_filtered.iloc[-1, -1]
    elif tarifart == "grundpreis + tonne":
        return preis_basis + gewicht * preis_tonne/1000


def add_cost(df_touren_distanzen,transport_preis,df_freightcost_path, columnname, tarifart,  preis_basis, preis_tonne):
    df_touren_distanzen[['Euc_Distance','Gewicht']] = df_touren_distanzen[['Euc_Distance','Gewicht']].astype(float)
    df_tarifmatrix_long = transform_tarifmatrix(transport_preis)
    df_touren_distanzen[columnname] = df_touren_distanzen.apply(lambda row: frachtkosten_berechnen(df_tarifmatrix_long, row["Gewicht"], row["Euc_Distance"], tarifart, preis_basis, preis_tonne),
    axis=1)
    df_touren_distanzen.to_csv(path_or_buf= df_freightcost_path, sep=";",encoding="latin1", decimal=".")
    print(f"Freight costs have been added and file is saved in: {df_freightcost_path}")
    return df_touren_distanzen
