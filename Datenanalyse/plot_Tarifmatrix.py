import plotly.graph_objects as go
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

def show_values_on_bars(axs):
    def _show_on_single_plot(ax):
        for p in ax.patches:
            _x = p.get_x() + p.get_width() / 2
            _y = p.get_y() + p.get_height()
            if _y >0:
                value = '{:.4f}'.format(p.get_height())
                ax.text(_x, _y, value, ha="center")

    if isinstance(axs, np.ndarray):
        for idx, ax in np.ndenumerate(axs):
            _show_on_single_plot(ax)
    else:
        _show_on_single_plot(axs)

def plot_tarifmatrix():
    df_tarifmatrix_wide = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Grunddaten\Transportpreismatrix_3dplot_Daten.csv",
        encoding="latin_1",
        sep=";", decimal=".", index_col="Gewicht_kg", dtype="float")

    x, y = pd.to_numeric(df_tarifmatrix_wide.columns.values), pd.to_numeric(df_tarifmatrix_wide.index.values)
    z = df_tarifmatrix_wide.values

    fig = go.Figure(data=[go.Surface(z=z, x=x, y=y,
                                     contours={
                                         "z": {"show": True, "start": 100, "end": 1500, "size": 100, "color": "black"}
                                     },
                                     )
                          ]
                    )

    fig.update_layout(autosize=True,
                      scene=dict(
                          xaxis_title="Distanz in km",
                          yaxis_title="Gewicht in kg",
                          zaxis_title="Kosten in €",
                          zaxis=dict(showticklabels=False)
                      ),
                      margin=dict(t=30, r=0, l=20, b=10),
                      font = dict(
                            size=10,
                        ),
                      )

    camera = dict(
        up=dict(x=0, y=0, z=0.01),
        center=dict(x=-0.25, y=-0.25, z=0),
        eye=dict(x=-1, y=-1, z=3) #(x=-1, y=-1, z=3)
    )
    fig.update_layout(scene_camera=camera)

    fig.write_image(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Diagramme\Tarifmatrix\Tarifmatrixdarstellung.pdf")
    fig.write_html(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Diagramme\Tarifmatrix\Tarifmatrixdarstellung.html")

    fig.show()

def colormap(df_col):
    col_array = []
    for point in df_col:
        if point > 0:
            col_array.append("red")
        else:
            col_array.append("green")
    return col_array

def plot_kg_Kostenmatrix():
    df_tarifmatrix_pro_kg = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Grunddaten\Transportpreismatrix_pro_kg.csv",
        encoding="latin_1",
        sep=";", decimal=".", dtype="float")
    df_tarifmatrix_pro_kg_Veränderung = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Grunddaten\Transportpreismatrix_pro_kg_Veränderung.csv",
        encoding="latin_1",
        sep=";", decimal=".", dtype="float")

    print(df_tarifmatrix_pro_kg.head())
    print(df_tarifmatrix_pro_kg.columns)

    figure, axes = plt.subplots(nrows=3, ncols=2, figsize=(10, 10))
    figure.suptitle("Kosten pro kg für 0,001 km/ 350,001 km/ 1000,001 km ", fontsize=16)

    line1 = sns.lineplot(data=df_tarifmatrix_pro_kg, x="Gewicht_kg", y="0.001", ax=axes[0][0], color="grey")
    line1.set(xlabel="Gewicht in kg", ylabel="Kosten pro kg")
    bar1 = sns.barplot(data=df_tarifmatrix_pro_kg_Veränderung, x="Gewicht_kg", y="0.001", ax=axes[0][1], palette =colormap(df_tarifmatrix_pro_kg_Veränderung["0.001"]))
    bar1.set(xlabel="Gewichtsstufe in kg", ylabel="Kostenänderung pro kg in €", xticks =[0,6,11,21,32,42])
    bar1.set_xticklabels(["50","500","1000","2000","10000","20000"])
    #show_values_on_bars(bar1)

    line3 = sns.lineplot(data=df_tarifmatrix_pro_kg, x="Gewicht_kg", y="350.001", ax=axes[1][0], color = "grey")
    line3.set(xlabel="Gewicht in kg", ylabel="Kosten pro kg")
    bar3 = sns.barplot(data=df_tarifmatrix_pro_kg_Veränderung, x="Gewicht_kg", y="350.001", ax=axes[1][1], palette=colormap(df_tarifmatrix_pro_kg_Veränderung["1000.001"]))
    bar3.set(xlabel="Gewichtsstufe in kg", ylabel="Kostenänderung pro kg in €", xticks =[0,6,11,21,32,42])
    bar3.set_xticklabels(["50","500","1000","2000","10000","20000"])

    line2 = sns.lineplot(data=df_tarifmatrix_pro_kg, x="Gewicht_kg", y="1000.001", ax=axes[2][0], color = "grey")
    line2.set(xlabel="Gewicht in kg", ylabel="Kosten pro kg")
    bar2 = sns.barplot(data=df_tarifmatrix_pro_kg_Veränderung, x="Gewicht_kg", y="1000.001", ax=axes[2][1], palette=colormap(df_tarifmatrix_pro_kg_Veränderung["1000.001"]))
    bar2.set(xlabel="Gewichtsstufe in kg", ylabel="Kostenänderung pro kg in €", xticks =[0,6,11,21,32,42])
    bar2.set_xticklabels(["50","500","1000","2000","10000","20000"])


    figure.tight_layout()
    figure.subplots_adjust(top=0.88)

    plt.savefig(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Diagramme\Tarifmatrix\Auswertung_Kosten_pro_kg.pdf", dpi=2000)
    #plt.show()

def plot_km_Kostenmatrix():
    df_tarifmatrix_pro_km = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Grunddaten\Transportpreismatrix_pro_km.csv",
        encoding="latin_1",
        sep=";", decimal=".", dtype="float", index_col="Gewicht_kg")
    df_tarifmatrix_pro_km_Veränderung = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Grunddaten\Transportpreismatrix_pro_km_Veränderung.csv",
        encoding="latin_1",
        sep=";", decimal=".", dtype="float", index_col="Gewicht_kg")

    df_tarifmatrix_pro_km = df_tarifmatrix_pro_km.T
    df_tarifmatrix_pro_km_Veränderung = df_tarifmatrix_pro_km_Veränderung.T

    df_tarifmatrix_pro_km_Veränderung.columns = df_tarifmatrix_pro_km_Veränderung.columns.astype(str)
    df_tarifmatrix_pro_km.columns = df_tarifmatrix_pro_km.columns.astype(str)

    print(df_tarifmatrix_pro_km)
    print(df_tarifmatrix_pro_km.head())
    print(df_tarifmatrix_pro_km.columns)
    print(df_tarifmatrix_pro_km_Veränderung.index)

    figure, axes = plt.subplots(nrows=3, ncols=2, figsize=(10, 10))
    figure.suptitle("Kosten pro km für 0,001 kg/ 5000,001 kg/ 10000,001 kg", fontsize=16)

    line1 = sns.lineplot(data=df_tarifmatrix_pro_km, x=[int(float(i)) for i in df_tarifmatrix_pro_km.index.values], y="0.001", ax=axes[0][0], color="grey")
    line1.set(xlabel="Distanz in km", ylabel="Kosten pro km")
    bar1 = sns.barplot(data=df_tarifmatrix_pro_km_Veränderung, x= [int(float(i)) for i in df_tarifmatrix_pro_km_Veränderung.index.values], y="0.001", ax=axes[0][1], palette =colormap(df_tarifmatrix_pro_km_Veränderung["0.001"]))
    bar1.set(xlabel="Distanzstufe in km", ylabel="Kostenänderung pro km in €",xticks =[0,4,9,13,17])
    bar1.set_xticklabels(["50","150","300", "600", "1000"])
    #show_values_on_bars(bar1)

    line3 = sns.lineplot(data=df_tarifmatrix_pro_km, x=[int(float(i)) for i in df_tarifmatrix_pro_km.index.values], y="5000.001", ax=axes[1][0], color = "grey")
    line3.set(xlabel="Distanz in km", ylabel="Kosten pro km")
    bar3 = sns.barplot(data=df_tarifmatrix_pro_km_Veränderung, x=[int(float(i)) for i in df_tarifmatrix_pro_km_Veränderung.index.values], y="5000.001", ax=axes[1][1], palette=colormap(df_tarifmatrix_pro_km_Veränderung["5000.001"]))
    bar3.set(xlabel="Distanzstufe in km", ylabel="Kostenänderung pro km in €",xticks =[0,4,9,13,17])
    bar3.set_xticklabels(["50", "150", "300", "600", "1000"])

    line2 = sns.lineplot(data=df_tarifmatrix_pro_km, x=[int(float(i)) for i in df_tarifmatrix_pro_km.index.values], y="10000.001", ax=axes[2][0], color = "grey")
    line2.set(xlabel="Distanz in km", ylabel="Kosten pro km")
    bar2 = sns.barplot(data=df_tarifmatrix_pro_km_Veränderung, x=[int(float(i)) for i in df_tarifmatrix_pro_km_Veränderung.index.values], y="10000.001", ax=axes[2][1], palette=colormap(df_tarifmatrix_pro_km_Veränderung["25000.001"]))
    bar2.set(xlabel="Distanzstufe in km", ylabel="Kostenänderung pro km in €",xticks =[0,4,9,13,17])
    bar2.set_xticklabels(["50", "150", "300", "600", "1000"])


    figure.tight_layout()
    figure.subplots_adjust(top=0.88)

    plt.savefig(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Diagramme\Tarifmatrix\Auswertung_Kosten_pro_km.pdf", dpi=2000)
    #plt.show()

if __name__ == "__main__":
    plot_tarifmatrix()
    #plot_kg_Kostenmatrix()
    #plot_km_Kostenmatrix()
