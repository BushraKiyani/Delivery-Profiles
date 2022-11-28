import plotly.graph_objects as go
import pandas as pd
import numpy as np

def diagramm_data(df):
    data_array= []
    source = []
    target = []
    kat_array = ["ZZZ", "BLAU", "GRAU", "GELB", "GRÜN"]

    for kat in ["ZZZ", "BLAU", "GRAU", "GELB", "GRÜN"]:
        for kat_to in ["ZZZ", "BLAU", "GRAU", "GELB", "GRÜN"]:
            df_filtered = df[(df["Kategorisierung"] == kat_to) & (df["alte_Kategorisierung"] == kat)]
            source.append(kat_array.index(kat))
            target.append(kat_array.index(kat_to))
            data_array.append(df_filtered["Frachtkosten"].sum())
    print(data_array)
    print(source)
    print(target)
    return data_array, source, target

def create_diagram(data_array, source, target):
    color = ["red", "blue", "grey", "yellow", "green", "red", "blue", "grey", "yellow", "green"]
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=["ZZZ", "BLAU", "GRAU", "GELB", "GRÜN", "ZZZ", "BLAU", "GRAU", "GELB", "GRÜN"],
            color=["red", "blue", "grey", "yellow", "green","red", "blue", "grey", "yellow", "green"]
        ),
        link=dict(
            source=source,  # indices correspond to labels, eg A1, A2, A1, B1, ...
            target=list(np.asarray(target) + 5),
            value=data_array,
            color= ["rgba(255, 0, 0, 0.4)", "red","red","red","red",'blue','rgba(31, 119, 180,0.5)',"blue","blue","blue","grey","grey","rgba(128,128,128,0.5)","grey","grey","yellow","yellow","yellow","rgba(240, 255, 0, 0.5)","yellow","green","green","green","green","rgb(60, 179, 113,0.5)",]
        ))])

    fig.update_layout(title_text="Veränderung der Frachtkosten pro Kategorie", font_size=10)
    fig.write_html(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Diagramme\Frachtkostenveränderung_durch_neue_ID.html")
    fig.show()

def table_data(df):

    df_grouped_old_count = df.groupby(["alte_Kategorisierung"]).count().reset_index().set_index("alte_Kategorisierung") # .loc["ID_Empfänger","ID_Sendung"]
    df_grouped_new_count = df.groupby(["Kategorisierung"]).count().reset_index().set_index("Kategorisierung")
    df_grouped_old_sum = df.groupby(["alte_Kategorisierung"]).sum().reset_index().set_index(
        "alte_Kategorisierung")  # .loc["ID_Empfänger","ID_Sendung"]
    df_grouped_new_sum = df.groupby(["Kategorisierung"]).sum().reset_index().set_index("Kategorisierung")

    kunden_new = df.drop_duplicates("ID_Empfänger").groupby(["Kategorisierung"]).count().reset_index().set_index("Kategorisierung")
    kunden_old = df.drop_duplicates("alte_ID_Empfänger").groupby(["alte_Kategorisierung"]).count().reset_index().set_index("alte_Kategorisierung")

    kunden_array =((kunden_new["ID_Empfänger"]/kunden_new["ID_Empfänger"].sum())-(kunden_old["alte_ID_Empfänger"]/kunden_old["alte_ID_Empfänger"].sum()))*100
    sendungs_array = ((df_grouped_new_count["ID_Sendung"]) - df_grouped_old_count["ID_Sendung"]) / df_grouped_old_count["ID_Sendung"].sum()*100
    kosten_array = ((df_grouped_new_sum["Frachtkosten"]) - df_grouped_old_sum["Frachtkosten"]) / df_grouped_old_sum["Frachtkosten"].sum()*100
    gewicht_array = ((df_grouped_new_sum["Gewicht"]) - df_grouped_old_sum["Gewicht"]) / df_grouped_old_sum[
        "Gewicht"].sum() * 100

    df_compare = pd.DataFrame(index=["ZZZ", "BLAU", "GRAU", "GELB", "GRÜN"], data={"Kundenanteil":kunden_array,
                                                                                    "Sendungsanteil": sendungs_array,
                                                                                   "Frachtkostenanteil": kosten_array,
                                                                                   "Frachtgewichtanteil": gewicht_array})
    df_compare = df_compare.round(2)
    df_compare = df_compare.astype(str) + '%'
    df_compare.to_latex(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Diagramme\Diagrammdaten\ID_Änderung_Auswirkung.txt")

if __name__ == "__main__":
    label = ["ZZZ", "BLAU", "GRAU", "GELB", "GRÜN", "ZZZ", "BLAU", "GRAU", "GELB", "GRÜN"]
    df_rohdaten = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Datensatz_TK_fertig.csv",
                              encoding="latin-1", sep=";")

    data_array, source, target = diagramm_data(df_rohdaten)
    create_diagram(data_array, source, target)

    table_data(df_rohdaten)


