import pandas as pd

def EinsparungenBerechnen(file, ID_list, df_sendungen):
    result_data = pd.read_csv(
        file,
        encoding="latin-1",
        sep=";")

    result_data["Kategorisierung"] = result_data.apply(lambda row: ID_list.loc[row["ID_Empfänger"], "Kategorisierung"],axis=1)

    print(result_data.head())
    def calc(kat):
        return (df_sendungen[df_sendungen["Kategorisierung"] == kat]["Frachtkosten"].sum() - result_data[result_data["Kategorisierung"] == kat]["Frachtkosten"].sum()) / df_sendungen["Frachtkosten"].sum()

    red_dict = {"ZZZ" : calc("ZZZ"), "GRAU": calc("GRAU"), "BLAU": calc("BLAU"), "GELB": calc("GELB"), "GRÜN": calc("GRÜN")}
    print(red_dict)
    return red_dict


if __name__ == '__main__':
    filelist = [r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Belieferungsprofile\Ergebnisse\Pattern_results_data_['ZZZ', 'GRAU', 'BLAU', 'GELB', 'GRÜN']var_gewicht0.75_var_frequenz0.75_mindest_frequenz1.csv",
                r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Belieferungsprofile\Ergebnisse\Pattern_results_data_['ZZZ', 'GRAU', 'BLAU', 'GELB', 'GRÜN']var_gewicht1.33_var_frequenz1.33_mindest_frequenz1.csv",
                r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Belieferungsprofile\Ergebnisse\Pattern_results_data_['ZZZ', 'GRAU', 'BLAU', 'GELB', 'GRÜN']var_gewicht100_var_frequenz100_mindest_frequenz1.csv"]
    ID_list = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\ID_liste.csv",
        encoding="latin-1",
        sep=";", index_col="ID_Empfänger")

    df_sendungen = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Datensatz_TK_fertig.csv",
        encoding="latin-1",
        sep=";")

    df_results = pd.DataFrame()
    for i in filelist:
        res = EinsparungenBerechnen(i, ID_list,df_sendungen)
        df_results = df_results.append(res, ignore_index=True)

    print(df_results)
    df_results.to_csv(
        path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Belieferungsprofile\overview_Einsarungen_pro_Kat.csv",
        encoding="latin_1", sep=";", decimal=".")