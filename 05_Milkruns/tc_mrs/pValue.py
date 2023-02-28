
import pandas as pd
from ast import literal_eval
import seaborn as sns
import matplotlib.pyplot as plt

def MR_kosten_berechnen():
    print("")

def pkr_berechnen(df_tours, df_mr_sendungen, multi, var):

    df_tours["var"] = var
    df_tours["Anzahl_Stationen"] = df_tours["Sequenz_extID"].apply(lambda seq: len(seq)-1)
    df_tours["Summe_AF_Kosten"] = df_tours["MR_ID"].apply(lambda row: df_mr_sendungen[df_mr_sendungen["MR_ID"]== row]["Frachtkosten_AF"].sum())

    df_tours["Summe_MR_Kosten"] = df_tours["MR_ID"].apply(lambda row: df_mr_sendungen[df_mr_sendungen["MR_ID"]== row]["Frachtkosten"].sum())

    df_tours["p_kr"] = df_tours["Summe_AF_Kosten"] / df_tours["Summe_MR_Kosten"]
    df_tours["K-Faktor"] = multi
    #print(df_tours)
    return df_tours

def pkr_visualisierung(df_pk_collected):
    palette = ["lightgray", "gray", "darkgray"]

    print(df_pk_collected)

    fig, ax0 = plt.subplots(figsize=(10, 4))
    boxplot = sns.boxplot(data=df_pk_collected,
                          x=df_pk_collected["var"],
                          y=df_pk_collected["p_kr"],
                          ax=ax0,
                          palette=palette,
                          hue="K-Faktor",
                          showmeans=True,
                          showfliers=False,
                          meanprops={"marker": "o",
                                     "markerfacecolor": "white",
                                     "markeredgecolor": "black",
                                     "markersize": "3"})
    boxplot.set(xlabel="Variabilitätsklassen", ylabel="$p_{kr}$", ylim=(None, None))
    boxplot.set_xticklabels(["max. geringe Var.", "max. mittlere Var.","max. moderate Var."])

    fig.tight_layout()



    fig.savefig(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\p-value\diagramms\p_kr_per_VarKlasse.pdf")

def pq_berechnen(df_nodes,multi, df_basedata, var):
    df_nodes["var"] = var
    df_nodes["K-Faktor"] = multi

    veh_dist_array = [9 * 60, 9 * 60, 9 * 60]
    veh_cap_array = [6500, 12000, 25000]

    veh_price_per_km = [0.3, 0.4, 0.6]  # 0.3296
    veh_price_per_km = [round(i * multi, 4) for i in veh_price_per_km]

    veh_price_per_min = [35 / 60, 35 / 60, 35 / 60]
    veh_price_per_min = [round(i * multi, 4) for i in veh_price_per_min]

    veh_price_per_charge = [0.155, 0.155, 0.155]
    veh_price_per_charge = [round(i * multi, 4) for i in veh_price_per_charge]

    df_nodes["AF_Kosten"] = df_nodes["ID_Empfänger"].apply(lambda ID: df_basedata[df_basedata["ID_Empfänger"]==ID]["Frachtkosten"].sum())

    df_nodes["MR_6500"] = df_nodes.apply(lambda row: ((row["Distanz"]*veh_price_per_km[0]+ (row["Dauer"]+20)*veh_price_per_min[0])*(1+veh_price_per_charge[0]))*row["avg_Frequenz"]*50 if row["avg_Gewicht"] <= 6500 else 9999999999999999, axis=1)

    df_nodes["MR_12500"] = df_nodes.apply(lambda row: ((row["Distanz"]*veh_price_per_km[1]+ (row["Dauer"]+20)*veh_price_per_min[1])*(1+veh_price_per_charge[1]))*row["avg_Frequenz"]*50 if row["avg_Gewicht"] <= 12500 else 9999999999999999, axis=1)

    df_nodes["MR_25000"] = df_nodes.apply(lambda row: ((row["Distanz"]*veh_price_per_km[2]+ (row["Dauer"]+20)*veh_price_per_min[2])*(1+veh_price_per_charge[2]))*row["avg_Frequenz"]*50 if row["avg_Gewicht"] <= 25000 else 9999999999999999, axis=1)

    df_nodes["cheapest_MR"] = df_nodes.apply(lambda row: min([row["MR_6500"],row["MR_12500"],row["MR_25000"]]), axis=1)

    df_nodes["p_q"] = df_nodes.apply(lambda row: row["AF_Kosten"] / row["cheapest_MR"], axis=1)

    print("Avg p_q ",df_nodes["p_q"].mean())
    print("Max p_q ",df_nodes["p_q"].max())
    print(df_nodes)

    data_max_avg = {
        "var": str(var),
        "multi" : str(multi),
        "max": df_nodes["p_q"].max(),
        "avg": df_nodes["p_q"].mean(),
    }
    return df_nodes, data_max_avg

def pq_visualisieren(df_max_avg_collected):
    palette = ["lightgray", "gray", "darkgray"]
    df_max_avg_collected["Einsparungen"] = df_max_avg_collected["Einsparungen"].astype(float)
    df_max_avg_collected["K-Faktor"] = df_max_avg_collected["multi"].astype(str)

    yticklabels = ["0%","-5%","-10%","-15%","-20%","-25%"]
    yticks = [-0,-5,-10,-15,-20,-25]

    ### p-mean
    fig, axes = plt.subplots(figsize=(10, 4), nrows=1, ncols=2)
    scatterplot1 = sns.scatterplot(
        data= df_max_avg_collected,
        x=df_max_avg_collected["avg"],
        y=df_max_avg_collected["Einsparungen"],
        hue = "K-Faktor",
        palette= palette,
        ax=axes[0]
    )
    scatterplot1.get_legend().remove()
    scatterplot1.set(xlabel="$mean(p_{s}^{Q}$)", ylabel="Einsparung", yticks = yticks, xlim=(0, df_max_avg_collected["avg"].max()+0.1), yticklabels = yticklabels)
    scatterplot1.xaxis.set_ticks_position("top")

    ### p-max
    scatterplot = sns.scatterplot(
        data= df_max_avg_collected,
        x=df_max_avg_collected["max"],
        y=df_max_avg_collected["Einsparungen"],
        hue = "K-Faktor",
        palette= palette,
        ax=axes[1],
    )
    scatterplot.set(xlabel="$max(p_{s}^{Q}$)", ylabel=None, yticks = yticks, xlim=(0, df_max_avg_collected["max"].max()+0.2),yticklabels =yticklabels)
    scatterplot.xaxis.set_ticks_position("top")
    fig.tight_layout()

    fig.savefig(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\p-value\diagramms\multi_p_Q_Einsparung_per_VarKlasse.pdf")

    print(df_max_avg_collected.info())
    df_max_avg_collected.loc[df_max_avg_collected["var"] == "0.75","VarK-Grenze"] = "0.75"
    df_max_avg_collected.loc[df_max_avg_collected["var"] == "1", "VarK-Grenze"]= "1"
    df_max_avg_collected.loc[df_max_avg_collected["var"] == "1.33","VarK-Grenze"] = "1.33"
    print(df_max_avg_collected)

    ### p-mean
    fig, axes = plt.subplots(figsize=(10, 4), nrows=1, ncols=2)
    scatterplot1 = sns.scatterplot(
        data= df_max_avg_collected,
        x=df_max_avg_collected["avg"],
        y=df_max_avg_collected["Einsparungen"],
        hue = "VarK-Grenze",
        palette= palette,
        ax=axes[0]
    )
    scatterplot1.get_legend().remove()
    scatterplot1.set(xlabel="$mean(p_{s}^{Q}$)", ylabel="Einsparung", xlim=(0, df_max_avg_collected["avg"].max()+0.1), yticks = yticks, yticklabels = yticklabels )
    scatterplot1.xaxis.set_ticks_position("top")

    ### p-max
    scatterplot = sns.scatterplot(
        data= df_max_avg_collected,
        x=df_max_avg_collected["max"],
        y=df_max_avg_collected["Einsparungen"],
        hue = "VarK-Grenze",
        palette= palette,
        ax=axes[1],

    )
    scatterplot.set(xlabel="$max(p_{s}^{Q}$)", ylabel=None, yticks = yticks, xlim=(0, df_max_avg_collected["max"].max()+0.2), yticklabels = yticklabels)
    scatterplot.xaxis.set_ticks_position("top")
    scatterplot.legend(loc='upper left')

    fig.tight_layout()

    fig.savefig(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\p-value\diagramms\var_p_Q_Einsparung_per_VarKlasse.pdf")

    #plt.show()

def add_dist_dur(df_nodes):
    df_distmatrix_real = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Matrizen\TK_distmatrix_1.33-1.33.csv",
        encoding="latin-1", sep=";", index_col="Unnamed: 0")
    df_durmatrix_real = pd.read_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Matrizen\TK_durmatrix_1.33-1.33.csv",
        encoding="latin-1", sep=";", index_col="Unnamed: 0")

    df_nodes["Distanz_real"] = df_nodes["ID_Empfänger"].apply(lambda ID: df_distmatrix_real.loc[ID, "0"])
    df_nodes["Dauer_real"] = df_nodes["ID_Empfänger"].apply(lambda ID: df_durmatrix_real.loc[ID, "0"])

    #print(df_nodes)
    return df_nodes


def pValue_berechnen():
    var_list = [0.75, 1, 1.33]
    multi_list = [0.8, 1, 1.2]

    df_pk_collected =pd.DataFrame()
    df_max_avg_collected =pd.DataFrame()

    for var in var_list:
        var_gew = var
        var_freq = var
        for mul in multi_list:
            multi = mul

            df_tours = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Rohergebnisse"+"\df_tours_TK_Instanz"+str(var_gew)+ "-"+str(var_freq)+ "-SZ20Multi"+str(multi)+".csv",
                                encoding="latin_1", sep=";",converters={"Sequenz_extID": literal_eval})

            df_mr_sendungen = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Feinergebnisse\only_MR"+"\df_only_MR_Sendungsdaten_"+str(var_gew)+ "-"+str(var_freq)+ "-SZ20Multi"+str(multi)+ "_außer_KW[1, 53]Knappsack_True"+".csv",
                                encoding="latin_1", sep=";",converters={"ID_Empfänger": literal_eval})

            df_nodes = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Instanznodes\TK_Instanz_Nodes"+str(var_gew)+"-"+str(var_gew)+".csv",
                                encoding="latin_1", sep=";")
            df_nodes = df_nodes.drop([0], axis=0)

            df_basedata = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Datensatz_TK_fertig"+".csv",
                                encoding="latin_1", sep=";")

            df_pk = pkr_berechnen(df_tours, df_mr_sendungen, multi, var_freq)
            df_pk_collected = df_pk_collected.append(df_pk, ignore_index=True)

            df_nodes, data_max_avg = pq_berechnen(df_nodes, multi, df_basedata, var)
            df_max_avg_collected = df_max_avg_collected.append(data_max_avg, ignore_index=True)
    print(df_pk_collected)
    print(df_max_avg_collected)

    erg_list = []
    for index, row in df_max_avg_collected.iterrows():
        print(row["var"])
        try:
            df_ergebnisse = pd.read_csv(
                r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Zusammenfassungen\df_MR_Zusammenfassung_"+row["var"]+"-"+row["var"]+"-SZ20Multi"+row["multi"]+"_außer_KW[1, 53]Knappsack_True" + ".csv",
                encoding="latin_1", sep=";")
        except:
            df_ergebnisse = pd.read_csv(
                r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Zusammenfassungen\df_MR_Zusammenfassung_" +
                row["var"] + "-" + row["var"] + "-SZ20Multi" + row["multi"] + "3-600-1800_außer_KW[1, 53]Knappsack_True" + ".csv",
                encoding="latin_1", sep=";")
        erg_list.append(round(df_ergebnisse["Einsparung_alle"].values[0]*-1*100,2))
    df_max_avg_collected["Einsparungen"] = erg_list
    print(df_max_avg_collected)

    pq_visualisieren(df_max_avg_collected)

    df_max_avg_collected.to_csv(
                r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\p-value\data\p_s_data"+".csv",
                encoding="latin_1", sep=";", index=False)

    df_pk_collected.to_csv(
                r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Auswertung\p-value\data\p_kr_per_VarKlasse"+".csv",
                encoding="latin_1", sep=";", index=False)
    pkr_visualisierung(df_pk_collected)




if __name__ == '__main__':
    pValue_berechnen()