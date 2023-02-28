import pandas as pd
from datetime import datetime, timedelta, date
import seaborn as sns
import matplotlib.pyplot as plt
import glob
from ast import literal_eval

def scatter_plot(datenpfad, instanzname):
    df_einsparungen = pd.read_csv(datenpfad, encoding="latin-1",sep=";")

    # Add Scatter
    fig, ax0 = plt.subplots(figsize=(10,4))

    df_einsparungen["Farbe"] = df_einsparungen["MR_Ersparnis"].apply(lambda x: "Verteuerung" if x>0 else "Einsparung")

    scatter_plot = sns.scatterplot(x=df_einsparungen["Auslastung"]*100, y=df_einsparungen["MR_Ersparnis"], palette=dict({"Verteuerung": "red", "Einsparung" : "grey"}), ax= ax0, hue= df_einsparungen["Farbe"], legend=False)
    scatter_plot.set(xlabel="durchschnittliche Auslastung [%]", ylabel="Kostenveränderung [€]")

    for index, row in df_einsparungen.iterrows():
        if row["MR_Ersparnis"] > 0:
            plt.text(row["Auslastung"]*100, row["MR_Ersparnis"],int(row["Kalenderwoche"]), horizontalalignment='left', size='small')
        else:
            continue

    fig.savefig(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\Scatter\Scatter_Auslastung_Einsparung_"+ instanzname+".pdf")

def bar_plot_einzel(datenpfad, instanzname):
    df_einsparungen = pd.read_csv(datenpfad, encoding="latin-1", sep=";")

    fig, ax0 = plt.subplots(figsize=(10, 4))

    df_einsparungen["Farbe"] = df_einsparungen["MR_Ersparnis"].apply(lambda x: "red" if x > 0 else "grey")

    bar_plot = sns.barplot(x=df_einsparungen["Kalenderwoche"], y=df_einsparungen["MR_Ersparnis"], palette= df_einsparungen["Farbe"], ax= ax0)
    bar_plot.set(xlabel="durchschnittliche Auslastung [%]", ylabel="Kostenveränderung [€]")

    for label in bar_plot.axes.xaxis.get_ticklabels()[::2]:
        label.set_visible(False)

    fig.savefig(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\Bar\Barplot_Einsparung_" + instanzname + ".pdf")

def vergleich_knappsack():
    df_einsparungen_knapsack_True = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\Diagrammdaten\df_MR_Einsparungen_0.75-0.75-SZ20Multi1_außer_KW[1, 53]Knappsack_True.csv", encoding="latin-1", sep=";")
    df_einsparungen_knapsack_False = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\Diagrammdaten\df_MR_Einsparungen_0.75-0.75-SZ20Multi1_außer_KW[1, 53]Knappsack_False.csv",encoding="latin-1", sep=";")

    df_combined = df_einsparungen_knapsack_True[["Kalenderwoche","MR_Ersparnis"]].join(df_einsparungen_knapsack_False.set_index('Kalenderwoche'), on="Kalenderwoche", lsuffix='_True', rsuffix='_False')

    df_combined = df_combined.rename({"MR_Ersparnis_True": "Branch-and-Bound","MR_Ersparnis_False":"Smallest-First"}, axis='columns')

    df_combined_melt = pd.melt(df_combined, id_vars=["Kalenderwoche"], value_vars=["Branch-and-Bound","Smallest-First"])

    fig, ax0 = plt.subplots(figsize=(10, 4))
    bar_plot_vergleich = sns.barplot(x=df_combined_melt["Kalenderwoche"], y=df_combined_melt["value"], palette= {"Branch-and-Bound":"grey", "Smallest-First":"lightgrey",}, ax= ax0, hue = df_combined_melt["variable"], hue_order=["Smallest-First","Branch-and-Bound" ])
    bar_plot_vergleich.set(xlabel="Kalenderwoche", ylabel="Kostenveränderung [€]", )
    plt.gca().legend().set_title('')

    for label in bar_plot_vergleich.axes.xaxis.get_ticklabels()[::2]:
        label.set_visible(False)

    fig.savefig(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\Bar\Barplot_Einsparung_Vergleich_Knappsack.pdf")

def MR_auslastung_VarK_optimierung():

    def sum_gewicht(list, df_nodes):
        mr_gewicht = 0
        for id in list:
            mr_gewicht+= df_nodes.loc[id,"avg_Gewicht"]
        return mr_gewicht

    print("")


    # df_MR_075_1 = pd.read_csv(
    #     r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Rohergebnisse\df_tours_TK_Instanz0.75-0.75-SZ20Multi1.csv",
    #     encoding="latin-1", sep=";",converters={"Sequenz_extID": literal_eval})
    # df_MR_075_1["Dataframe"] = "VarK <= 0.75"
    # df_MR_075_1["K-Faktor"] = 1
    #
    # df_MR_075_12 = pd.read_csv(
    #     r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Rohergebnisse\df_tours_TK_Instanz0.75-0.75-SZ20Multi1.2.csv",
    #     encoding="latin-1", sep=";",converters={"Sequenz_extID": literal_eval})
    # df_MR_075_12["Dataframe"] = "VarK <= 0.75"
    # df_MR_075_12["K-Faktor"] = 1.2
    #
    # df_MR_075_08 = pd.read_csv(
    #     r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Rohergebnisse\df_tours_TK_Instanz0.75-0.75-SZ20Multi0.8.csv",
    #     encoding="latin-1", sep=";",converters={"Sequenz_extID": literal_eval})
    # df_MR_075_08["Dataframe"] = "VarK <= 0.75"
    # df_MR_075_08["K-Faktor"] = 0.8
    #
    # df_MR_1_1 = pd.read_csv(
    #     r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Rohergebnisse\df_tours_TK_Instanz1-1-SZ20Multi13-600-1800.csv",
    #     encoding="latin-1", sep=";",converters={"Sequenz_extID": literal_eval})
    # df_MR_1_1["Dataframe"] = "VarK <= 1"
    # df_MR_1_1["K-Faktor"] = 1
    #
    # df_MR_1_12 = pd.read_csv(
    #     r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Rohergebnisse\df_tours_TK_Instanz1-1-SZ20Multi1.23-600-1800.csv",
    #     encoding="latin-1", sep=";",converters={"Sequenz_extID": literal_eval})
    # df_MR_1_12["Dataframe"] = "VarK <= 1"
    # df_MR_1_12["K-Faktor"] = 1.2
    #
    # df_MR_1_08 = pd.read_csv(
    #     r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Rohergebnisse\df_tours_TK_Instanz1-1-SZ20Multi0.83-600-1800.csv",
    #     encoding="latin-1", sep=";",converters={"Sequenz_extID": literal_eval})
    # df_MR_1_08["Dataframe"] = "VarK <= 1"
    # df_MR_1_08["K-Faktor"] = 0.8
    #
    df_MR_133_1 = pd.read_csv(
        r"../00_Resources/Instances/Results/tours/df_tours_Instanz1-1.33-1.33-SZ15Multi1Veh_cap13-600-1800.csv",
        encoding="latin-1", sep=";",converters={"Sequenz_extID": literal_eval})
    df_MR_133_1["Dataframe"] = "VarK <= 1.33"
    df_MR_133_1["K-Faktor"] = 1

    df_MR_133_12 = pd.read_csv(
        r"../00_Resources/Instances/Results/tours/df_tours_Instanz1-1.33-1.33-SZ15Multi1.2Veh_cap13-600-1800.csv",
        encoding="latin-1", sep=";",converters={"Sequenz_extID": literal_eval})
    df_MR_133_12["Dataframe"] = "VarK <= 1.33"
    df_MR_133_12["K-Faktor"] = 1.2

    df_MR_133_15 = pd.read_csv(
        r"../00_Resources/Instances/Results/tours/df_tours_Instanz1-1.33-1.33-SZ15Multi1.5Veh_cap13-600-1800.csv",
        encoding="latin-1", sep=";",converters={"Sequenz_extID": literal_eval})
    df_MR_133_15["Dataframe"] = "VarK <= 1.33"
    df_MR_133_15["K-Faktor"] = 1.5

    df_MR = pd.concat([
                       df_MR_133_1, df_MR_133_12, df_MR_133_15
                       ], ignore_index=True)

    df_nodes = pd.read_csv(
        r"../00_Resources/Instances/MR_Instance_Nodes/MR_Instance_Nodes1_1.33_1.33.csv",
        encoding="latin-1", sep=";", index_col="ID_Empfänger")

    df_MR["Gewicht"] = df_MR["Sequenz_extID"].apply(lambda list: sum_gewicht(list, df_nodes))

    df_MR["Auslastung"] = df_MR["Gewicht"]/df_MR["Kapazität"]

    print("VarK <= 0.75")
    print(df_MR[df_MR["Dataframe"] == "VarK <= 0.75"]["Auslastung"].describe())
    print("")
    print("VarK <= 1")
    print(df_MR[df_MR["Dataframe"] == "VarK <= 1"]["Auslastung"].describe())
    print("")
    print("VarK <= 1.33")
    print(df_MR[df_MR["Dataframe"] == "VarK <= 1.33"]["Auslastung"].describe())
    print(df_MR["Auslastung"].describe())

    palette = ["lightgray", "gray", "darkgray"]

    fig, ax0 = plt.subplots(figsize=(10, 4))
    boxplot = sns.boxplot(data=df_MR,
                          x=df_MR["Dataframe"],
                          y=df_MR["Auslastung"]*100,
                          ax=ax0,
                          hue="K-Faktor",
                          palette=palette,
                          showmeans=True,
                          showfliers=True,
                          meanprops={"marker":"o",
                                     "markerfacecolor":"white",
                                     "markeredgecolor":"black",
                                     "markersize":"3"})
    boxplot.set(xlabel= "Variabilitätsklassen", ylabel= "Auslastung", ylim = (0,105),yticks= [20,40,60,80,100], yticklabels= ["20%", "40%","60%","80%","100%"])

    fig.tight_layout()

    fig.savefig(
        r"../00_Resources/Instances/MR_Figures/Boxplots/Boxplot_Auslastung_nach_VarK_nach_opt.pdf")

    #df_MR.to_csv(
    #    r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\Boxplot\Boxplot_Auslastung_nach_VarK_nach_opt_data.csv",
    #    encoding="latin_1", sep=";", index=False)

    # only <=1.33
    df_MR = df_MR[df_MR["Dataframe"] == "VarK <= 1.33"]
    fig, ax0 = plt.subplots(figsize=(4, 4))
    boxplot = sns.boxplot(data=df_MR,
                          #x=df_MR["K-Faktor"],
                          y=df_MR["Auslastung"]*100,
                          ax=ax0,
                          #hue="K-Faktor",
                          #palette=palette,
                          color= "grey",
                          showmeans=True,
                          showfliers=True,
                          meanprops={"marker":"o",
                                     "markerfacecolor":"white",
                                     "markeredgecolor":"black",
                                     "markersize":"3"})
    boxplot.set(#xlabel= "Cost factor",
                ylabel= "Weight capacity utilization", ylim = (0,105),yticks= [20,40,60,80,100], yticklabels= ["20%", "40%","60%","80%","100%"])

    fig.tight_layout()

    fig.savefig(
        r"../00_Resources/Instances/MR_Figures/Boxplots/Boxplot_Auslastung_nach_VarK_nach_opt_1.33.pdf")

def MR_auslastung_Monat_ohne_korr():
    df_MR_Auslastung = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\df_MR_Auslastung_0.75-0.75-SZ20Multi1_außer_KW[1, 53]Knappsack_True.csv",
        encoding="latin-1", sep=";")

    #df_MR_Auslastung = df_MR_Auslastung.groupby(["Monat"])
    #df_MR_Auslastung = df_MR_Auslastung.reset_index()
    df_MR_Auslastung["Auslastung"] = df_MR_Auslastung["Auslastung"].apply(lambda x: int(x*100))

    palette = ["gray" for i in range(1,12+1)]

    fig, ax0 = plt.subplots(figsize=(10, 4))
    boxplot = sns.boxplot(data=df_MR_Auslastung,
                          x=df_MR_Auslastung["Monat"],
                          y=df_MR_Auslastung["Auslastung"],
                          ax=ax0,
                          palette=palette,
                          showmeans=True,
                          meanprops={"marker":"o",
                                     "markerfacecolor":"white",
                                     "markeredgecolor":"black",
                                     "markersize":"3"})
    boxplot.set(xlabel= "Monat", ylabel= "Auslastung", ylim= (-5,None))

    fig.savefig(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\Boxplot\Boxplot_Auslastung_pro_Monat_ohne_korr.pdf")

def MR_auslastung_VarK_ohne_korr():
    df_MR_075_1 = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\df_MR_Auslastung_0.75-0.75-SZ20Multi1_außer_KW[1, 53]Knappsack_True.csv",
        encoding="latin-1", sep=";")
    df_MR_075_1["Dataframe"] = "VarK <= 0.75"
    df_MR_075_1["K-Faktor"] = 1

    df_MR_075_12 = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\df_MR_Auslastung_0.75-0.75-SZ20Multi1.2_außer_KW[1, 53]Knappsack_True.csv",
        encoding="latin-1", sep=";")
    df_MR_075_12["Dataframe"] = "VarK <= 0.75"
    df_MR_075_12["K-Faktor"] = 1.2

    df_MR_075_08 = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\df_MR_Auslastung_0.75-0.75-SZ20Multi0.8_außer_KW[1, 53]Knappsack_True.csv",
        encoding="latin-1", sep=";")
    df_MR_075_08["Dataframe"] = "VarK <= 0.75"
    df_MR_075_08["K-Faktor"] = 0.8


    df_MR_1_1 = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\df_MR_Auslastung_1-1-SZ20Multi13-600-1800_außer_KW[1, 53]Knappsack_True.csv",
        encoding="latin-1", sep=";")
    df_MR_1_1["Dataframe"] = "VarK <= 1"
    df_MR_1_1["K-Faktor"] = 1

    df_MR_1_12 = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\df_MR_Auslastung_1-1-SZ20Multi1.23-600-1800_außer_KW[1, 53]Knappsack_True.csv",
        encoding="latin-1", sep=";")
    df_MR_1_12["Dataframe"] = "VarK <= 1"
    df_MR_1_12["K-Faktor"] = 1.2

    df_MR_1_08 = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\df_MR_Auslastung_1-1-SZ20Multi0.83-600-1800_außer_KW[1, 53]Knappsack_True.csv",
        encoding="latin-1", sep=";")
    df_MR_1_08["Dataframe"] = "VarK <= 1"
    df_MR_1_08["K-Faktor"] = 0.8


    df_MR_133_1 = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\df_MR_Auslastung_1.33-1.33-SZ20Multi13-600-1800_außer_KW[1, 53]Knappsack_True.csv",
        encoding="latin-1", sep=";")
    df_MR_133_1["Dataframe"] = "VarK <= 1.33"
    df_MR_133_1["K-Faktor"] = 1

    df_MR_133_12 = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\df_MR_Auslastung_1.33-1.33-SZ20Multi1.23-600-1800_außer_KW[1, 53]Knappsack_True.csv",
        encoding="latin-1", sep=";")
    df_MR_133_12["Dataframe"] = "VarK <= 1.33"
    df_MR_133_12["K-Faktor"] = 1.2

    df_MR_133_08 = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\df_MR_Auslastung_1.33-1.33-SZ20Multi0.83-600-1800_außer_KW[1, 53]Knappsack_True.csv",
        encoding="latin-1", sep=";")
    df_MR_133_08["Dataframe"] = "VarK <= 1.33"
    df_MR_133_08["K-Faktor"] = 0.8

    df_MR = pd.concat([df_MR_075_1, df_MR_075_12, df_MR_075_08,
                       df_MR_1_1, df_MR_1_12, df_MR_1_08,
                       df_MR_133_1, df_MR_133_12, df_MR_133_08
                       ],ignore_index=True)

    df_MR["Auslastung"] = df_MR["Auslastung"].apply(lambda x: int(x*100))

    palette = ["lightgray", "gray", "darkgray"]

    fig, ax0 = plt.subplots(figsize=(10, 4))
    boxplot = sns.boxplot(data=df_MR,
                          x=df_MR["Dataframe"],
                          y=df_MR["Auslastung"],
                          ax=ax0,
                          hue= "K-Faktor",
                          palette=palette,
                          showmeans=True,
                          showfliers=False,
                          meanprops={"marker":"o",
                                     "markerfacecolor":"white",
                                     "markeredgecolor":"black",
                                     "markersize":"3"})
    boxplot.set(xlabel= "Variabilitätsklassen", ylabel= "Auslastung", ylim= (-5,None), yticks = [0,50,100,150,200,250],yticklabels = ["0%","50%","100%","150%","200%","250%"])
    boxplot.legend(loc='upper right', title = "K-Faktor")

    fig.tight_layout()

    fig.savefig(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\Boxplot\Boxplot_Auslastung_nach_VarK_ohne_korr.pdf")

    df_list = [df_MR_075_08, df_MR_075_1, df_MR_075_12, df_MR_1_08, df_MR_1_1, df_MR_1_12, df_MR_133_08, df_MR_133_1, df_MR_133_12]

    table_data = {"VarK-Limit":[0.75,0.75,0.75, 1,1,1, 1.33, 1.33, 1.33],
                  "K-Faktor" : [0.8,1,1.2, 0.8,1,1.2, 0.8,1,1.2],
                  "bis 10%": [df[df["Auslastung"]<=0.1].shape[0]/df["Auslastung"].shape[0] for df in df_list],
                  "10% bis 50%": [df[(df["Auslastung"]>0.1)&(df["Auslastung"]<=0.5)].shape[0]/df["Auslastung"].shape[0] for df in df_list],
                  "50% bis 100%": [df[(df["Auslastung"]>0.5)&(df["Auslastung"]<=1)].shape[0]/df["Auslastung"].shape[0] for df in df_list],
                  "über 100%": [df[df["Auslastung"]>1].shape[0]/df["Auslastung"].shape[0] for df in df_list],
                  }

    df_auslastung_table = pd.DataFrame(data=table_data)
    df_auslastung_table["bis 10%"] = (df_auslastung_table["bis 10%"]*100).round(2).astype(str) + "%"
    df_auslastung_table["10% bis 50%"] = (df_auslastung_table["10% bis 50%"] * 100).round(2).astype(str) + "%"
    df_auslastung_table["50% bis 100%"] = (df_auslastung_table["50% bis 100%"] * 100).round(2).astype(str) + "%"
    df_auslastung_table["über 100%"] = (df_auslastung_table["über 100%"] * 100).round(2).astype(str) + "%"
    #print(df_auslastung_table)

    df_auslastung_table.to_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\Boxplot\df_MR_Auslastung_Vergleich"+".csv",
                    encoding="latin_1", sep=";", index=False)
    df_auslastung_table.to_latex(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\Boxplot\df_MR_Auslastung_Vergleich"+".txt",)

def run_visualisierung_MR():
    #dateiname = r"\df_MR_Einsparungen_0.75-0.75-SZ20Multi1_außer_KW[1, 53]Knappsack_True"
    #instanzname = dateiname[19:]
    #datenpfad = r"..\00_Resources\Instances\Results\MR_savings\Diagrammdaten"+ str(dateiname)+".csv"

    #scatter_plot(datenpfad,instanzname)

    #bar_plot_einzel(datenpfad, instanzname)

    #vergleich_knappsack()

    #MR_auslastung_Monat_ohne_korr()

    #MR_auslastung_VarK_ohne_korr()

    MR_auslastung_VarK_optimierung()

def instanzauswertung():
    kunden_kategorien = ["ZZZ", "GRAU", "BLAU", "GELB", "GRÜN", "ALLE"]
    var_kategorien = [0.75, 1, 1.33, 100]

    df_Variabilitätsauswertung = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Variabiltätsauswertung\Variablitaetsauswertung.csv",
        encoding="latin-1", sep=";")

    for var_kat in var_kategorien:
        df_Variabilitätsauswertung_var_filter = df_Variabilitätsauswertung[(df_Variabilitätsauswertung["variability_Gewicht"]<=var_kat) & (df_Variabilitätsauswertung["variability_Frequenz"]<=var_kat)& (df_Variabilitätsauswertung["avg_Frequenz"]>=1)]

        df_Instanzzusammensetzung = pd.DataFrame(columns=["Kundenkategorisierung", "Kundenanteil", "Sendungsanteil", "Kostenanteil", "Gewichtsanteil"])


        for kat in kunden_kategorien[:-1]:
            data_row = {"Kundenkategorisierung" : kat,
                        #"Kundenanteil abs.": df_Variabilitätsauswertung_var_filter[df_Variabilitätsauswertung_var_filter["Kategorisierung"]==kat].shape[0],
                        "Kundenanteil": (df_Variabilitätsauswertung_var_filter[df_Variabilitätsauswertung_var_filter["Kategorisierung"]==kat].shape[0] / df_Variabilitätsauswertung.shape[0])*100,
                        "Sendungsanteil": df_Variabilitätsauswertung_var_filter[df_Variabilitätsauswertung_var_filter["Kategorisierung"]==kat]["Sendungen"].sum() / df_Variabilitätsauswertung["Sendungen"].sum()*100,
                        "Gewichtsanteil": df_Variabilitätsauswertung_var_filter[df_Variabilitätsauswertung_var_filter["Kategorisierung"]==kat]["Gewicht"].sum() / df_Variabilitätsauswertung["Gewicht"].sum()*100,
                        "Kostenanteil": df_Variabilitätsauswertung_var_filter[df_Variabilitätsauswertung_var_filter["Kategorisierung"]==kat]["Frachtkosten"].sum() / df_Variabilitätsauswertung["Frachtkosten"].sum()*100,
            }
            df_Instanzzusammensetzung = df_Instanzzusammensetzung.append(data_row, ignore_index=True)
        data_row = {"Kundenkategorisierung" : "Alle Kategorien",
                    #"Kunden abs.": df_Instanzzusammensetzung["Kundenanteil abs."].sum(),
                    "Kundenanteil": df_Instanzzusammensetzung["Kundenanteil"].sum(),
                    "Sendungsanteil": df_Instanzzusammensetzung["Sendungsanteil"].sum(),
                    "Gewichtsanteil": df_Instanzzusammensetzung["Gewichtsanteil"].sum(),
                    "Kostenanteil": df_Instanzzusammensetzung["Kostenanteil"].sum(),
            }
        df_Instanzzusammensetzung = df_Instanzzusammensetzung.append(data_row, ignore_index=True)

        df_Instanzzusammensetzung = df_Instanzzusammensetzung.round(2)

        for cols in df_Instanzzusammensetzung.columns[1:]:
            df_Instanzzusammensetzung[cols] = df_Instanzzusammensetzung[cols].astype(str) + "%"

        #print(df_Instanzzusammensetzung)

        df_Instanzzusammensetzung.to_csv(
                    r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Instanzbeschreibung\df_Instanzbeschreibung_"+str(var_kat)+".csv",
                    encoding="latin_1", sep=";", index=False)
        df_Instanzzusammensetzung.to_latex(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Instanzbeschreibung\df_Instanzbeschreibung_"+str(var_kat)+".txt", index=False)

def milkrun_frachtanteile():
    df_MR_Anteile = pd.DataFrame()

    filelist = glob.glob(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Feinergebnisse\only_MR\used\*.csv")
    #print(filelist)
    for file in filelist:
        if "False" not in file:
            df_only_MR = pd.read_csv(
                file ,
                encoding="latin-1", sep=";")

            df_only_MR["Milkrun"] = df_only_MR["ID_Sendung"].apply(lambda x: True if "[" in x else False)
            #print(df_only_MR)

            data_row = {"VarK": file.split("-")[1],
                        "Kosten": file.split("Multi")[1].split("_")[0],
                        "Frachtgewichtsanteil Milkruns": (df_only_MR[df_only_MR["Milkrun"]== True]["Gewicht"].sum() / df_only_MR["Gewicht"].sum()),
                        "Frachtgewichtsanteil Gebietsspediteur": (df_only_MR[df_only_MR["Milkrun"]== False]["Gewicht"].sum() / df_only_MR["Gewicht"].sum()),
                        "Frachtkostenanteil Milkruns": df_only_MR[df_only_MR["Milkrun"] == True]["Frachtkosten"].sum() / df_only_MR["Frachtkosten"].sum(),
                        "Frachtkostenanteil Gebietsspediteur": df_only_MR[df_only_MR["Milkrun"] == False]["Frachtkosten"].sum() /df_only_MR["Frachtkosten"].sum(),
                        }
            #print(data_row)
            df_MR_Anteile = df_MR_Anteile.append(data_row, ignore_index=True)
    for col in ["Frachtgewichtsanteil Milkruns", "Frachtgewichtsanteil Gebietsspediteur", "Frachtkostenanteil Milkruns","Frachtkostenanteil Gebietsspediteur"]:
        df_MR_Anteile[col] = (df_MR_Anteile[col]*100).round(2).astype(str) + "%"
    df_MR_Anteile.to_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Zusammenfassungen\df_MR_AF_Anteile.csv",
                    encoding="latin_1", sep=";", index=False)
    #print(df_MR_Anteile)

    #print("")

def einsparungen_vis():
    df_ergebnisse = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\Einsparungen_MR.csv",
        encoding="latin-1", sep=";")
    df_ergebnisse["Einsparung"] = df_ergebnisse["Einsparung"]/100
    print(df_ergebnisse)

    palette = ["lightgray", "gray", "darkgray"]

    fig, ax0 = plt.subplots(figsize=(10, 4))
    bar = sns.barplot(data=df_ergebnisse,
                          x=df_ergebnisse["ï»¿Var"],
                          y=df_ergebnisse["Einsparung"],
                          ax=ax0,
                          hue= df_ergebnisse["Kostenfaktor"],
                          palette=palette,)

    bar.set(xlabel= "Variabilitätsklassen", ylabel= "Einsparung", yticks = [0,-0.05,-0.10,-0.15,-0.20],yticklabels = ["0%","-5%","-10%","-15%","-20%"],xticklabels = ["<= 0.75","<= 1","<= 1.33"])

    for p in bar.patches:
        bar.annotate(format(p.get_height(), '.2%'),
                       (p.get_x() + p.get_width() / 2., p.get_height()),
                       ha='center', va='center',
                       xytext=(0, 9),
                       textcoords='offset points')

    fig.tight_layout()

    fig.savefig(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\Bar\Einsparungen_MR.pdf")

def MR_AF_Anteile_vis():
    df_anteile= pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Zusammenfassungen\df_MR_AF_Anteile.csv",
        encoding="latin-1", sep=";")
    print(df_anteile)

    s1 = sns.barplot(x='VarK', y='Frachtgewichtsanteil Gebietsspediteur', data=df_anteile, color='red', hue= "Kosten")

    s2 = sns.barplot(x='VarK', y='Frachtgewichtsanteil Milkruns', data=df_anteile, color='blue', hue= "Kosten")
    plt.show()

def MR_Time_cap_usage():
    basepath = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Rohergebnisse\\"
    filelist = ["df_tours_TK_Instanz1-1-SZ20Multi13-600-1800",
                "df_tours_TK_Instanz1-1-SZ20Multi0.83-600-1800",
                "df_tours_TK_Instanz1-1-SZ20Multi1.23-600-1800",
                "df_tours_TK_Instanz1.33-1.33-SZ20Multi13-600-1800",
                "df_tours_TK_Instanz1.33-1.33-SZ20Multi1.23-600-1800",
                "df_tours_TK_Instanz1.33-1.33-SZ20Multi0.83-600-1800",
                "df_tours_TK_Instanz0.75-0.75-SZ20Multi1",
                "df_tours_TK_Instanz0.75-0.75-SZ20Multi1.2",
                "df_tours_TK_Instanz0.75-0.75-SZ20Multi0.8"]

    df_tours_collected = pd.DataFrame()
    for file in filelist:
        kfaktor = file.split("i")[1].split("-")[0].strip("3")
        VarK = file.split("-")[1]

        print(basepath + file + ".csv")
        df_tours = pd.read_csv(basepath + file + ".csv", encoding="latin-1", sep=";")
        df_tours["VarK"]=VarK
        df_tours["K-Faktor"]=kfaktor

        df_tours_collected = df_tours_collected.append(df_tours, ignore_index=True)

    print(df_tours_collected)
    df_tours_collected["Zeitauslastung"] = df_tours_collected["Tourdauer"]/540

    print(df_tours_collected["Zeitauslastung"].describe())


    palette = ["lightgray", "gray", "darkgray"]

    fig, ax0 = plt.subplots(figsize=(10, 4))
    bar = sns.boxplot(data=df_tours_collected,
                          x=df_tours_collected["VarK"],
                          y=df_tours_collected["Zeitauslastung"],
                          ax=ax0,
                          hue= df_tours_collected["K-Faktor"],
                          palette=palette,
                          showmeans=True,
                          meanprops={"marker":"o",
                                     "markerfacecolor":"white",
                                     "markeredgecolor":"black",
                                     "markersize":"3"})

    bar.set(xlabel= "Variabilitätsklassen",xticklabels=["VarK <= 0.75", "VarK <= 1","VarK <= 1.33"] , ylabel= "Auslastung", ylim= (0,1.05) , yticks = [0.2,0.4,0.6,0.8,1], yticklabels = ["20%","40%","60%","80%","100%"])

    bar.legend(loc='lower right', title = "K-Faktor")
    fig.tight_layout()
    fig.savefig(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\Boxplot\Zeitauslastung_MR.pdf")


    #only <=1.33

    df_tours_collected = df_tours_collected[df_tours_collected["VarK"]== "1.33"]
    print(df_tours_collected.head(10))

    fig, ax0 = plt.subplots(figsize=(4, 4))
    bar = sns.boxplot(data=df_tours_collected,
                      #x=df_tours_collected["K-Faktor"],
                      y=df_tours_collected["Zeitauslastung"],
                      ax=ax0,
                      #hue=df_tours_collected["K-Faktor"],
                      #palette=palette,
                      color= "grey",
                      showmeans=True,
                      meanprops={"marker": "o",
                                 "markerfacecolor": "white",
                                 "markeredgecolor": "black",
                                 "markersize": "3"})

    bar.set(#xlabel="Cost factors",
            ylabel="Time capacity utilization", ylim=(0, 1.05), yticks=[0.2, 0.4, 0.6, 0.8, 1],
            yticklabels=["20%", "40%", "60%", "80%", "100%"])

    #bar.legend(loc='lower right', title="K-Faktor")
    fig.tight_layout()
    fig.savefig(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\Boxplot\Zeitauslastung_MR_1.33.pdf")

    df_tours_collected_grouped = df_tours_collected.groupby(["VarK", "K-Faktor"])
    print(df_tours_collected_grouped["Zeitauslastung"].describe())

if __name__ == '__main__':
    run_visualisierung_MR()
    #instanzauswertung()
    #milkrun_frachtanteile()
    #einsparungen_vis()
    #MR_AF_Anteile_vis()
    #MR_Time_cap_usage()