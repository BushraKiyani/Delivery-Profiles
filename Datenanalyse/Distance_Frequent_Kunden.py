import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt



def diagramm_Fahrzeit():
    df_distmatrix = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Matrizen\TK_distmatrix_1.33-1.33.csv", encoding="latin-1",
        sep=";")
    df_distmatrix = df_distmatrix.loc[:, ["0"]]
    df_distmatrix = df_distmatrix.drop([0])
    df_distmatrix["Kategorie"] = "Fahrtdistanz"
    print(df_distmatrix)
    df_durmatrix = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Matrizen\TK_durmatrix_1.33-1.33.csv", encoding="latin-1",
        sep=";")
    df_durmatrix = df_durmatrix.loc[:,["0"]]
    df_durmatrix = df_durmatrix.drop([0])
    df_durmatrix["Kategorie"] = "Fahrtdauer"
    print(df_durmatrix.describe())

    df_combined = df_distmatrix.append(df_durmatrix, ignore_index=True)
    print(df_combined)

    palette = ["gray"]

    fig, ax0 = plt.subplots(figsize=(10, 2))
    boxplot = sns.boxplot(data=df_durmatrix,
                          x=df_durmatrix["0"],
                          ax=ax0,
                          palette=palette,
                          showmeans=True,
                          showfliers=True,
                          meanprops={"marker": "o",
                                     "markerfacecolor": "white",
                                     "markeredgecolor": "black",
                                     "markersize": "3"})
    boxplot.set(xlabel="Fahrtdauer [min]", yticks = [])

    fig.tight_layout()
    fig.show()
    fig.savefig(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\Boxplot\Boxplot_Fahrtdauer_Verteilung.pdf")


if __name__ == '__main__':
    diagramm_Fahrzeit()
