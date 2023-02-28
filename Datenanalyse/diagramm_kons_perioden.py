import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd

def create_diagramm():
    data = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Konsolidierungsperioden_Diagrammdaten.csv",
                                      encoding="latin_1", sep=";")
    print(data)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize = (10,4))

    bar_dem = sns.barplot(x="Tag", y="Nachfrage", data=data, color='grey', ax=ax1)
    bar_dem.set_xticklabels(["Mon.", "Tue.", "Wed.", "Thu.", "Fri.", "Mon.", "Tue.", "Wed.", "Thu.", "Fri."])
    bar_dem.set_yticks([5,10,15,20,25])
    bar_dem.set_xlabel(None)
    bar_dem.set_ylabel("Demand")


    bar_lot_2 = sns.barplot(x="Tag", y="Transportlos", data=data, color='lightgrey', ax=ax2)
    bar_lot_1 = sns.barplot(x="Tag", y="Erhalt", data=data, color='grey', ax=ax2)
    bar_lot_3 = sns.barplot(x="Tag", y="Übertrag", data=data, color="red", ax=ax2)
    #bar_lot_3 = sns.barplot(x="Tag", y="Übertrag", data=data, linewidth=2.5, facecolor=(1, 1, 1, 0), edgecolor=[(1,1,1,0),".2",(1,1,1,0),".2",".2",(1,1,1,0),".2",(1,1,1,0),".2",".2",], ax=ax2)

    bar_lot_3.set_xticklabels(["Mon.", "Tue.", "Wed.", "Thu.", "Fri.", "Mon.", "Tue.", "Wed.", "Thu.", "Fri."])
    bar_lot_3.set_yticks([5, 10, 15, 20, 25])
    bar_lot_3.set_xticks([0, 1,2,3,4,5,6,7,8,9])
    bar_lot_3.set_ylabel("Transport lot")
    bar_lot_3.set_xlabel(None)

    print(ax1.patches[0].get_width())
    bar_lot_3.annotate("",
            xy=(1 -0.35, 15), xycoords='data',
            xytext=(0,5-0.05), textcoords='data',
            arrowprops=dict(arrowstyle="-|>",
                            connectionstyle="angle", lw=2),
            )
    bar_lot_3.annotate("",
            xy=(3 -0.35, 8), xycoords='data',
            xytext=(2, 5-0.05), textcoords='data',
            arrowprops=dict(arrowstyle="-|>",
                            connectionstyle="angle", lw=2),
            )
    bar_lot_3.annotate("",
            xy=(5 -0.35, 20), xycoords='data',
            xytext=(4, 13-0.05), textcoords='data',
            arrowprops=dict(arrowstyle="-|>",
                            connectionstyle="angle", lw=2),
            )
    bar_lot_3.annotate("",
            xy=(7 - 0.35, 4), xycoords='data',
            xytext=(6, 4-0.05), textcoords='data',
            arrowprops=dict(arrowstyle="-|>",
                            connectionstyle="angle", lw=2),
            )
    bar_lot_3.annotate("",
            xy=(9 -0.35, 6), xycoords='data',
            xytext=(8, 4-0.05), textcoords='data',
            arrowprops=dict(arrowstyle="-|>",
                            connectionstyle="angle", lw=2),
            )

    fig.tight_layout()

    fig.savefig(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Belieferungsprofile\Versandmengenänderung durch Konsolidierungsperioden.pdf",
        dpi=2000)

    #plt.show()

if __name__ == '__main__':
    create_diagramm()
