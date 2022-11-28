import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from curlyBrace import curlyBrace


if __name__ == "__main__":
    version = "\Version_2"
    df = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" + version + "\Zeitliche_Konsolidierung_Ergebnisse\Kosolidierung_Beispieldaten.csv",
        encoding="latin_1", sep=";")



    print(df.head())
    print(df.tail())

    figure, axes = plt.subplots(1,1,figsize=(20, 10))

    #barplot_incoming = sns.barplot(x=df_incoming["Periode"], y=df_incoming["Gewicht"], color="grey", ax=axes)
    #axes.bar(x="Periode", height="Ausgänge", data=df, color="grey", tick_label=df["Periode"],
    #         label="Konsolidierte Versandmenge")
    axes.bar(x= "Periode",height= "Eingänge", data=df, color = "grey", tick_label = df["Periode"], label = "Eingänge zur Konsolidierung")

    #barplot_outgoing = sns.barplot(x=df_outgoings["Periode"], y=df_outgoings["Gewicht"], color="red", ax=axes)
    #axes.step(x= "Periode",y= "Konsolidierte_Menge", data=df, where= "mid",color= "red", label = "Test")
    axes.set_xlabel("Perioden")
    axes.set_ylabel("Frachtgewicht in kg")
    #curlyBrace(fig,
    #figure.tight_layout()
    #axes.set(title = "Visualisierung der zeitlichen Konsolidierung")



    [l.set_visible(False) for (i,l) in enumerate(axes.xaxis.get_ticklabels()) if i % 5 != 0]

    plt.savefig(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources"+version+"\Zeitliche_Konsolidierung_Ergebnisse\Beispiel.pdf",dpi = 2000)
    #plt.show()


