import pandas as pd

if __name__ == "__main__":
    df_sendungen = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Datensatz_TK_bereinigt.csv", encoding="latin-1", sep=";")

    df_zuordnung = df_sendungen[["alte_ID_Empfänger","ID_Empfänger",  "alte_Straße_Empfänger", "Straße_Empfänger", "PLZ_Empfänger","Name_Empfänger"]]
    df_zuordnung = df_zuordnung.drop_duplicates(subset=["ID_Empfänger", "alte_ID_Empfänger", "alte_Straße_Empfänger", "Straße_Empfänger", "PLZ_Empfänger","Name_Empfänger"]).sort_values("ID_Empfänger")

    df_zuordnung.to_csv(path_or_buf=r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\ID_Zuordnung.csv",
                       sep=";", encoding="latin1", decimal=".", index=False)

