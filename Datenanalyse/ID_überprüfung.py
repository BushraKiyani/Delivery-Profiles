import pandas as pd

if __name__ == "__main__":
    df_rohdaten = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Datensatz_TK_fertig.csv",
        encoding="latin-1", sep=";")
    df_rohdaten_filter = df_rohdaten[["Transport","alte_ID_Empfänger", "ID_Empfänger"]]

    df_grouped_alt = df_rohdaten_filter.groupby(["Transport", "alte_ID_Empfänger"])["alte_ID_Empfänger"].count().reset_index(
        name="Anzahl")
    df_grouped_alt = df_grouped_alt[df_grouped_alt["Anzahl"] >= 2]
    print(df_grouped_alt["Anzahl"].sum())
    df_grouped_alt = df_grouped_alt.groupby("alte_ID_Empfänger")["Anzahl"].count().reset_index(name= "Häufigkeit")
    df_grouped_alt.to_csv(path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\df_2_Sendungen_gleicher_Tag_alt.csv", index=True, sep=";", encoding="latin1",decimal=".")

    df_grouped_neu = df_rohdaten_filter.groupby(["Transport","ID_Empfänger"])["ID_Empfänger"].count().reset_index(name= "Anzahl")
    df_grouped_neu = df_grouped_neu[df_grouped_neu["Anzahl"]>=2]
    print(df_grouped_neu["Anzahl"].sum())
    df_grouped_neu = df_grouped_neu.groupby("ID_Empfänger")["Anzahl"].count().reset_index(name= "Häufigkeit")
    df_grouped_neu.to_csv(path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\df_2_Sendungen_gleicher_Tag_neu.csv", index=True, sep=";", encoding="latin1",decimal=".")
    print(df_grouped_neu)

    df_ID_liste = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\ID_liste.csv",
        encoding="latin-1", sep=";")
