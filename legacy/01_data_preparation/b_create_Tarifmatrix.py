import pandas as pd

def transform_tarifmatrix(df_tarifmatrix_wide):

    df_tarif_matrix_melted = pd.melt(df_tarifmatrix_wide, id_vars="Weight_kg", value_vars=df_tarifmatrix_wide.columns[1:],
                                     var_name="Euc_Distance", value_name="Kosten")
    df_tarif_matrix_melted = df_tarif_matrix_melted.astype("float")
    return df_tarif_matrix_melted

def Freight_Cost_berechnen(df_tarifmatrix_long, Weight, distanz, tariff_type, price_basis, price_per_ton ):
    if tariff_type == "matrix":
        tarifmatrix_long_filtered = df_tarifmatrix_long[
            (df_tarifmatrix_long["Euc_Distance"] <= distanz) &
            (df_tarifmatrix_long["Weight_kg"] <= Weight)
        ]
        return tarifmatrix_long_filtered.iloc[-1, -1]
    elif tariff_type == "grundpreis + tonne":
        return price_basis + Weight * price_per_ton/1000


def add_cost(df_touren_distanzen,transport_preis,df_freightcost_path, columnname, tariff_type,  price_basis, price_per_ton):
    df_touren_distanzen[['Euc_Distance','Weight']] = df_touren_distanzen[['Euc_Distance','Weight']].astype(float)
    df_tarifmatrix_long = transform_tarifmatrix(transport_preis)
    df_touren_distanzen[columnname] = df_touren_distanzen.apply(lambda row: Freight_Cost_berechnen(df_tarifmatrix_long, row["Weight"], row["Euc_Distance"], tariff_type, price_basis, price_per_ton),
    axis=1)
    #df_touren_distanzen.to_csv(path_or_buf= df_freightcost_path, sep=";",encoding="latin1", decimal=".")
    print(f"Freight costs have been added and file is saved in: {df_freightcost_path}")
    return df_touren_distanzen
