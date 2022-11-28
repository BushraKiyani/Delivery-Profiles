import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def create_boxplot(x_col, y_col, order, data, save_path,x_label, y_label, title =None):
    plt.figure(figsize=(10, 4)) #
    ax = sns.boxplot(x=x_col,
                     y=y_col,
                     order=order,
                     data=data,
                     color= "grey",
                     showmeans=True,
                     showfliers= False,
                     meanprops={"marker": "o",
                                "markerfacecolor": "white",
                                "markeredgecolor": "black",
                                "markersize": "7"})
    ax.set(ylabel=y_label)
    ax.set(xlabel=x_label)
    #ax.set(title = title)
    plt.tight_layout()
    plt.savefig(save_path, dpi=2000)

def boxplots_kat_data(kat_col, upper_bounds, group_col):
    data = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" +version+"\Diagramme\Diagrammdaten\df_AuswertungNachKunden.csv", encoding="latin_1", sep=";")
    kat_array=[]
    for index, row in data.iterrows():
        for bound in upper_bounds:
            #print(row[kat_col])
            if row[kat_col] <= bound:
                kat_array.append("<=" + str(bound))
                break
            else:
                continue

    data[group_col] =  kat_array
    return data





if __name__ == '__main__':
    version = "\Version_2"
    order_kat = ["ZZZ", "BLAU", "GRAU", "GELB", "GRÜN"]
    df_touren_sendungen = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" +version+"\Datensatz_TK_fertig.csv", encoding="latin_1", sep=";")

    title = "Sendungsgewicht pro Kundenkategorie"
    savepath = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" +version+ r"\Diagramme\Boxplots\boxplot_KunKatGew_Sendungen.pdf"
    create_boxplot("Kategorisierung","Gewicht",order_kat,df_touren_sendungen, savepath, "Kundenkategorisierung","Gewicht in kg",title)

    title = "Sendungsdistanz pro Kundenkategorie"
    savepath = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" + version + r"\Diagramme\Boxplots\boxplot_KunKatDistanz_Sendungen.pdf"
    create_boxplot("Kategorisierung", "Distanz", order_kat, df_touren_sendungen, savepath,
                   "Kundenkategorisierung", "Distanz in km",title)

    title = "Sendungskosten pro Kundenkategorie"
    savepath = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" +version+ r"\Diagramme\Boxplots\boxplot_KunKatFrachtkosten_Sendungen.pdf"
    create_boxplot("Kategorisierung", "Frachtkosten", order_kat, df_touren_sendungen,savepath, "Kundenkategorisierung", "Frachtkosten in €",title)

    getpath = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" +version+ "\Diagramme\Diagrammdaten\df_AuswertungNachKunden.csv"
    df_touren_Kunden = pd.read_csv(getpath, encoding="latin_1", sep=";")

    title = "Durchschnittliches Sendungsgewicht pro Kunde pro Kundenkategorie"
    savepath = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" +version+ r"\Diagramme\Boxplots\boxplot_KunKatGew_Kunden.pdf"
    create_boxplot("Kategorisierung", "avg_Gewicht_pro_Sendung", order_kat, df_touren_Kunden,
                   savepath,
                   "Kundenkategorisierung", "Gewicht in kg",title)

    title = "Durchschnittliche Sendungsfrachtkosten pro Kunde pro Kundenkategorie"
    savepath = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" +version+ r"\Diagramme\Boxplots\boxplot_KunKatFrachtkosten_Kunden.pdf"
    create_boxplot("Kategorisierung", "avg_Frachtkosten_pro_Sendung", order_kat, df_touren_Kunden,savepath,"Kundenkategorisierung", "Frachtkosten in €",title)

    title = "Durchschnittliche Sendungsfrequenz pro Kunde pro Kundenkategorie"
    savepath = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" + version + r"\Diagramme\Boxplots\boxplot_KunKatSendungsfrequenz_Kunden.pdf"
    create_boxplot("Kategorisierung", "avg_Sendungen_pro_Woche", order_kat, df_touren_Kunden, savepath,
                   "Kundenkategorisierung", "Sendungen pro Woche",title)

    savepath = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources" + version + r"\Diagramme\Boxplots\boxplot_GewKatSendungsfrequenz_Kunden.pdf"
    upper_bounds = [0.125, 0.25, 0.5, 1, 2, 3, 4, 5, 6]
    order_kat = ["<=0.125", "<=0.25", "<=0.5","<=1", "<=2","<=3","<=4","<=5", "<=6"]
    boxplots_data = boxplots_kat_data(kat_col="avg_Sendungen_pro_Woche", upper_bounds= upper_bounds, group_col="Frequenzkategorie")
    create_boxplot("Frequenzkategorie","avg_Gewicht_pro_Sendung",order_kat,boxplots_data,savepath,x_label="Frequenzkategorien", y_label="Durchschnittliches Frachtgewicht")







