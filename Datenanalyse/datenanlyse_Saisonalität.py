import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

import datetime

hue_order= ["ZZZ", "BLAU", "GRAU", "GELB", "GRÜN"]
colors = {"ZZZ": "red", "BLAU": "blue", "GRAU": "grey", "GELB": "yellow", "GRÜN": "green"}



def creatDiagrammAbsolute(df, groupCol, version):
    df = df.groupby([groupCol, "Kategorisierung"]).sum().reset_index()

    figure, ax = plt.subplots(figsize = (20,5))

    plot1= sns.pointplot(x= groupCol, y= "Gewicht", hue= "Kategorisierung", data= df, hue_order= hue_order, palette=colors, ax=ax)
    plot1.set(ylim=(0, None))
    plot1.ticklabel_format(style='plain', axis='y')

    filename= r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources"+version+ "\Diagramme\Saisonalität\FrachtkostenProKategoriePro" + groupCol +".pdf"
    plt.savefig(filename, dpi=2000)


    #plt.show()
    plt.clf()

def creatDiagrammGewichtWeekdays(df, version, df_pattern):
    df = df[(df["Wochentag"] != 5)]
    df_pattern = df_pattern[(df_pattern["Wochentag"] != 5)]

    df = df.groupby(["Wochentag"]).sum().reset_index()
    df_pattern = df_pattern.groupby(["Wochentag"]).sum().reset_index()

    gewicht_anteil_array = []
    for index, row in df.iterrows():
        gewicht_anteil_array.append(row["Gewicht"]/ df["Gewicht"].sum())
    df["Gewicht_Prozent"] = gewicht_anteil_array
    #print(gewicht_anteil_array)

    gewicht_anteil_array_pattern =[]
    for index, row in df_pattern.iterrows():
        gewicht_anteil_array_pattern.append(row["Gewicht"]/ df_pattern["Gewicht"].sum())
    df_pattern["Gewicht_Prozent_pattern"] = gewicht_anteil_array_pattern
    #print(gewicht_anteil_array_pattern)

    labels = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag'] #, "Samstag"
    x = np.arange(len(labels))
    width = 0.35

    figure, axes = plt.subplots(figsize=(10, 5))

    plot1 = axes.bar(x - width/1.9, gewicht_anteil_array, width, label = "ohne Belieferungsprofilen", color= "grey")
    plot2 = axes.bar(x + width / 1.9, gewicht_anteil_array_pattern, width, label="mit Belieferungsprofilen", color= "lightgrey")

    axes.set(ylabel = "Frachtgewichtsanteil", xlabel= "Wochentage")
    axes.set_xticks(np.arange(len(x)))
    axes.set_xticklabels(labels)
    axes.set_yticklabels(["0"+"%","5"+"%","10"+"%","15"+"%","20"+"%","25"+"%"])
    axes.legend()

    def autolabel(rects):
        """
        Attach a text label above each bar displaying its height
        """
        for rect in rects:
            height = rect.get_height()
            axes.text(rect.get_x() + rect.get_width() / 2., 1.01 * height,
                    '%s' % str(round(height*100,1))+"%",
                    ha='center', va='bottom')

    autolabel(plot1)
    autolabel(plot2)
    figure.tight_layout()

    plt.savefig(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources"+version+ "\Diagramme\Saisonalität\FrachtgewichtanteilProWochentag.pdf", dpi=2000)
    #plt.show()
    plt.clf()

def creatDiagrammGewichtWeekdays_vergleich(df, version, df_pattern_075, df_pattern_133,df_pattern_100):

    df = df[(df["Wochentag"] != 5)]
    df_pattern_075 = df_pattern_075[(df_pattern_075["Wochentag"] != 5)]
    df_pattern_133 = df_pattern_133[(df_pattern_133["Wochentag"] != 5)]
    df_pattern_100 = df_pattern_100[(df_pattern_100["Wochentag"] != 5)]

    df = df.groupby(["Wochentag"]).sum().reset_index()
    df_pattern_075 = df_pattern_075.groupby(["Wochentag"]).sum().reset_index()
    df_pattern_133 = df_pattern_133.groupby(["Wochentag"]).sum().reset_index()
    df_pattern_100 = df_pattern_100.groupby(["Wochentag"]).sum().reset_index()

    gewicht_anteil_array = []
    for index, row in df.iterrows():
        gewicht_anteil_array.append(row["Gewicht"]/ df["Gewicht"].sum())
    df["Gewicht_Prozent"] = gewicht_anteil_array
    #print(gewicht_anteil_array)

    gewicht_anteil_array_pattern_075 = []
    for index, row in df_pattern_075.iterrows():
        gewicht_anteil_array_pattern_075.append(row["Gewicht"]/ df_pattern_075["Gewicht"].sum())
    df_pattern_075["Gewicht_Prozent_pattern"] = gewicht_anteil_array_pattern_075

    gewicht_anteil_array_pattern_133 = []
    for index, row in df_pattern_133.iterrows():
        gewicht_anteil_array_pattern_133.append(row["Gewicht"]/ df_pattern_133["Gewicht"].sum())
    df_pattern_133["Gewicht_Prozent_pattern"] = gewicht_anteil_array_pattern_133

    gewicht_anteil_array_pattern_100 = []
    for index, row in df_pattern_100.iterrows():
        gewicht_anteil_array_pattern_100.append(row["Gewicht"]/ df_pattern_100["Gewicht"].sum())
    df_pattern_100["Gewicht_Prozent_pattern"] = gewicht_anteil_array_pattern_100

    labels = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag'] #, "Samstag"
    x = np.arange(len(labels))
    width = 0.3

    f, (a0, a1, a2) = plt.subplots(3,1, figsize=(8, 10))
    plot1 = a0.bar(x - width/1.7, gewicht_anteil_array, width, label = "ohne Belieferungsprofilen", color= "grey")
    plot2 = a0.bar(x + width / 1.7, gewicht_anteil_array_pattern_075, width, label="max. geringe Var", color= "lightgrey")
    a0.set_xticks(np.arange(len(x)))
    a0.set_yticklabels(["0"+"%","5"+"%","10"+"%","15"+"%","20"+"%","25"+"%"])
    a0.set_xticklabels([])

    plot3 = a1.bar(x - width/1.7, gewicht_anteil_array, width, label = "ohne Belieferungsprofilen", color= "grey")
    plot4 = a1.bar(x + width / 1.7, gewicht_anteil_array_pattern_133, width, label="max. geringe Var", color= "lightgrey")
    a1.set(ylabel = "Frachtgewichtsanteil")
    a1.set_xticks(np.arange(len(x)))
    a1.set_xticklabels([])
    a1.set_yticklabels(["0"+"%","5"+"%","10"+"%","15"+"%","20"+"%","25"+"%"])

    plot5 = a2.bar(x - width/1.7, gewicht_anteil_array, width, label = "ohne Belieferungsprofilen", color= "grey")
    plot6 = a2.bar(x + width / 1.7, gewicht_anteil_array_pattern_100, width, label="max. geringe Var", color= "lightgrey")
    a2.set(xlabel= "Wochentage")
    a2.set_xticks(np.arange(len(x)))
    a2.set_xticklabels(labels)
    a2.set_yticklabels(["0"+"%","5"+"%","10"+"%","15"+"%","20"+"%","25"+"%"])

    def autolabel(rects, axes):
        """
        Attach a text label above each bar displaying its height
        """
        for rect in rects:
            height = rect.get_height()
            axes.text(rect.get_x() + rect.get_width() / 2., 1.005 * height,
                    '%s' % str(round(height*100,1))+"%",
                    ha='center', va='bottom', size = "small")

    autolabel(plot1, a0)
    autolabel(plot2, a0)
    autolabel(plot3, a1)
    autolabel(plot4, a1)
    autolabel(plot5, a2)
    autolabel(plot6, a2)

    f.tight_layout()
    f.savefig(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources"+version+ "\Diagramme\Saisonalität\FrachtgewichtanteilProWochentag_vergleich.pdf", dpi=2000)

    f.clf()

def creatDiagrammSendungWeekdays(df, version, df_pattern):
    df = df[(df["Wochentag"] != 5)]
    df_pattern = df_pattern[(df_pattern["Wochentag"] != 5)]

    df = df.groupby(["Wochentag"]).count().reset_index()
    df_pattern = df_pattern.groupby(["Wochentag"]).count().reset_index()

    gewicht_anteil_array = []
    for index, row in df.iterrows():
        gewicht_anteil_array.append(row["Gewicht"]/ df["Gewicht"].sum())
    df["Gewicht_Prozent"] = gewicht_anteil_array
    #print(gewicht_anteil_array)

    gewicht_anteil_array_pattern =[]
    for index, row in df_pattern.iterrows():
        gewicht_anteil_array_pattern.append(row["Gewicht"]/ df_pattern["Gewicht"].sum())
    df_pattern["Gewicht_Prozent_pattern"] = gewicht_anteil_array_pattern
    #print(gewicht_anteil_array_pattern)

    labels = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag'] #, "Samstag"
    x = np.arange(len(labels))
    width = 0.35

    figure, axes = plt.subplots(figsize=(10, 5))

    plot1 = axes.bar(x - width/1.9, gewicht_anteil_array, width, label = "ohne Belieferungsprofilen", color= "grey")
    plot2 = axes.bar(x + width / 1.9, gewicht_anteil_array_pattern, width, label="mit Belieferungsprofilen", color= "lightgrey")

    axes.set(ylabel = "Sendungssanteil", xlabel= "Wochentage")
    axes.set_xticks(np.arange(len(x)))
    axes.set_xticklabels(labels)
    axes.set_yticklabels(["0"+"%","5"+"%","10"+"%","15"+"%","20"+"%","25"+"%"])
    axes.legend()

    def autolabel(rects):
        """
        Attach a text label above each bar displaying its height
        """
        for rect in rects:
            height = rect.get_height()
            axes.text(rect.get_x() + rect.get_width() / 2., 1.01 * height,
                    '%s' % str(round(height*100,1))+"%",
                    ha='center', va='bottom')

    autolabel(plot1)
    autolabel(plot2)
    figure.tight_layout()

    plt.savefig(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources"+version+ "\Diagramme\Saisonalität\SendungsanteilProWochentag.pdf", dpi=2000)
    #plt.show()
    plt.clf()

def creatDiagrammGewichtWeekdaysPattern_only(df, version, df_pattern):
    df = df[(df["ID_Empfänger"].isin(df_pattern["ID_Empfänger"].values)) & (df["Wochentag"] != 5)]

    df = df.groupby(["Wochentag"]).sum().reset_index()
    df_pattern = df_pattern.groupby(["Wochentag"]).sum().reset_index()

    gewicht_anteil_array = []
    for index, row in df.iterrows():
        gewicht_anteil_array.append(row["Gewicht"]/ df["Gewicht"].sum())
    df["Gewicht_Prozent"] = gewicht_anteil_array
    #print(gewicht_anteil_array)

    gewicht_anteil_array_pattern =[]
    for index, row in df_pattern.iterrows():
        gewicht_anteil_array_pattern.append(row["Gewicht"]/ df_pattern["Gewicht"].sum())
    df_pattern["Gewicht_Prozent_pattern"] = gewicht_anteil_array_pattern
    #print(gewicht_anteil_array_pattern)

    labels = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag']
    x = np.arange(len(labels))
    width = 0.35

    figure, axes = plt.subplots(figsize=(10, 5))

    plot1 = axes.bar(x - width / 1.9, gewicht_anteil_array, width, label = "ohne Belieferungsprofilen", color= "grey")
    plot2 = axes.bar(x + width / 1.9, gewicht_anteil_array_pattern, width, label="mit Belieferungsprofilen", color= "lightgrey")

    axes.set(ylabel = "Frachtgewichtsanteil", xlabel= "Wochentage")
    axes.set_xticks(np.arange(len(x)))
    axes.set_xticklabels(labels)
    axes.set_yticklabels(["0"+"%","5"+"%","10"+"%","15"+"%","20"+"%","25"+"%"])
    axes.legend()

    def autolabel(rects):
        """
        Attach a text label above each bar displaying its height
        """
        for rect in rects:
            height = rect.get_height()
            axes.text(rect.get_x() + rect.get_width() / 2., 1.01 * height,
                    '%s' % str(round(height*100,1))+"%",
                    ha='center', va='bottom')

    autolabel(plot1)
    autolabel(plot2)
    figure.tight_layout()

    plt.savefig(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources"+version+ "\Diagramme\Saisonalität\FrachtgewichtanteilProWochentagPatternOnly.pdf", dpi=2000)
    #plt.show()
    plt.clf()

def creatDiagrammSendungenWeekdaysPattern_only(df, version, df_pattern):
    df = df[(df["ID_Empfänger"].isin(df_pattern["ID_Empfänger"].values)) & (df["Wochentag"] != 5)]

    df = df.groupby(["Wochentag"]).count().reset_index()
    df_pattern = df_pattern.groupby(["Wochentag"]).count().reset_index()
    print(df)
    print(df_pattern)

    gewicht_anteil_array = []
    for index, row in df.iterrows():
        gewicht_anteil_array.append(row["Gewicht"]/ df["Gewicht"].sum())
    df["Gewicht_Prozent"] = gewicht_anteil_array
    print(gewicht_anteil_array)

    gewicht_anteil_array_pattern =[]
    for index, row in df_pattern.iterrows():
        gewicht_anteil_array_pattern.append(row["Gewicht"]/ df_pattern["Gewicht"].sum())
    df_pattern["Gewicht_Prozent_pattern"] = gewicht_anteil_array_pattern
    print(gewicht_anteil_array_pattern)

    labels = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag']
    x = np.arange(len(labels))
    width = 0.35

    figure, axes = plt.subplots(figsize=(10, 5))

    plot1 = axes.bar(x - width / 1.9, gewicht_anteil_array, width, label = "ohne Belieferungsprofilen", color= "grey")
    plot2 = axes.bar(x + width / 1.9, gewicht_anteil_array_pattern, width, label="mit Belieferungsprofilen", color= "lightgrey")

    axes.set(ylabel = "Sendungsanteil", xlabel= "Wochentage")
    axes.set_xticks(np.arange(len(x)))
    axes.set_xticklabels(labels)
    axes.set_yticklabels(["0"+"%","5"+"%","10"+"%","15"+"%","20"+"%","25"+"%"])
    axes.legend()

    def autolabel(rects):
        """
        Attach a text label above each bar displaying its height
        """
        for rect in rects:
            height = rect.get_height()
            axes.text(rect.get_x() + rect.get_width() / 2., 1.01 * height,
                    '%s' % str(round(height*100,1))+"%",
                    ha='center', va='bottom')

    autolabel(plot1)
    autolabel(plot2)
    figure.tight_layout()

    plt.savefig(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources"+version+ "\Diagramme\Saisonalität\SendungsanteilProWochentagPatternOnly.pdf", dpi=2000)
    #plt.show()
    plt.clf()


def creatDiagrammNoKategories(df, groupCol, version):
    df = df.groupby(groupCol).sum().reset_index()

    figure, ax = plt.subplots(figsize=(20, 10))

    plot1 = sns.pointplot(x=groupCol, y=df["Gewicht"], data=df, ax=ax)
    plot1.set(ylim=(0, None))
    plot1.ticklabel_format(style='plain', axis='y')

    filename = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources"+version+ "\Diagramme\Saisonalität\FrachtkostenPro" + groupCol + ".pdf"
    plt.savefig(filename, dpi=2000)
    # plt.show()
    plt.clf()

def creatDiagrammRelative(df, groupCol, version):
    df_time_agg = df.groupby([groupCol, "Kategorisierung"]).sum()
    df_Kat_agg = df_time_agg.groupby(groupCol).sum()
    df = (df_time_agg.div(df_Kat_agg, level = groupCol) *100).reset_index()

    df_Frachtgewicht = pd.pivot_table(data= df, values="Gewicht", columns= "Kategorisierung", index="Monat")

    df_Frachtgewicht = df_Frachtgewicht[["ZZZ","BLAU", "GRAU", "GELB", "GRÜN"]]
    #print(df_Frachtgewicht.head())
    df_Frachtgewicht.loc["mean"] = df_Frachtgewicht.mean()

    plot = df_Frachtgewicht.plot(kind= "bar", stacked = True, color = ["red", "blue", "grey", "yellow", "green"])
    plot.set(xlabel = "Monat", ylabel = "Anteil in %")
    #plot.set(title="Kategorieanteile an Frachtgewicht pro Monat")
    plt.tight_layout()

    filename= r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources"+version+ "\Diagramme\Saisonalität\FrachtgewichtanteilProKategoriePro" + groupCol
    plt.savefig(filename+".pdf", dpi=2000)
    df_Frachtgewicht.to_csv(filename+ "_Daten"+".csv", sep=";", encoding="latin1", decimal=".")
    #plt.show()
    plt.clf()

def creatDiagrammRelativeFrachtkosten(df, groupCol, version):
    df_time_agg = df.groupby([groupCol, "Kategorisierung"]).sum()
    df_Kat_agg = df_time_agg.groupby(groupCol).sum()
    df = (df_time_agg.div(df_Kat_agg, level = groupCol) *100).reset_index()
    #print(df.head())

    df_Frachtkosten = pd.pivot_table(data= df, values="Frachtkosten", columns= "Kategorisierung", index="Monat")

    df_Frachtkosten = df_Frachtkosten[["ZZZ","BLAU", "GRAU", "GELB", "GRÜN"]]
    #print(df_Frachtkosten.head())
    df_Frachtkosten.loc["mean"] = df_Frachtkosten.mean()

    plot = df_Frachtkosten.plot(kind= "bar", stacked = True, color = ["red", "blue", "grey", "yellow", "green"])
    plot.set( xlabel = "Monat", ylabel = "Anteil in %")
    #plot.set(title="Kategorieanteile an Frachtkosten pro Monat")
    plt.tight_layout()

    filename= r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources"+version+ "\Diagramme\Saisonalität\FrachtkostenanteilProKategoriePro" + groupCol
    plt.savefig(filename+".pdf", dpi=2000)
    df_Frachtkosten.to_csv(filename+ "_Daten"+".csv", sep=";", encoding="latin1", decimal=".")
    #plt.show()
    plt.clf()

def creatDiagrammRelativeSendungen(df, groupCol, version):
    df_time_agg = df.groupby([groupCol, "Kategorisierung"]).count()
    df_Kat_agg = df_time_agg.groupby(groupCol).sum()
    df = (df_time_agg.div(df_Kat_agg, level = groupCol) *100).reset_index()
    #print(df.head())

    df_Frachtkosten = pd.pivot_table(data= df, values="Frachtkosten", columns= "Kategorisierung", index="Monat")

    df_Frachtkosten = df_Frachtkosten[["ZZZ","BLAU", "GRAU", "GELB", "GRÜN"]]
    #print(df_Frachtkosten.head())
    df_Frachtkosten.loc["mean"] = df_Frachtkosten.mean()

    plot = df_Frachtkosten.plot(kind= "bar", stacked = True, color = ["red", "blue", "grey", "yellow", "green"])
    plot.set( xlabel = "Monat", ylabel = "Sendungsanteil", xticklabels = ["1","2","3","4","5","6","7","8","9","10","11","12","mean"], yticklabels=["0%","20%","40%","60%","80%","100%"])
    #plot.set(title="Kategorieanteile an Sendungen pro Monat")
    plt.tight_layout()

    filename= r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources"+version+ "\Diagramme\Saisonalität\SendungsanteilProKategoriePro" + groupCol
    plt.savefig(filename+".pdf", dpi=2000)
    df_Frachtkosten.to_csv(filename+ "_Daten"+".csv", sep=";", encoding="latin1", decimal=".")
    #plt.show()
    plt.clf()


if __name__ == '__main__':
    version = "\Version_2"
    df_touren = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Datensatz_TK_fertig.csv",
                                      encoding="latin_1", sep=";")
    df_touren["Beladedatum"] = pd.to_datetime(df_touren["Beladedatum"],dayfirst = True)
    df_touren["Kalenderwoche"] = df_touren["Beladedatum"].dt.week
    df_touren["Wochentag"] = df_touren["Beladedatum"].dt.dayofweek
    df_touren["Monat"] = df_touren["Beladedatum"].dt.month

    df_touren = df_touren[["ID_Empfänger","Beladedatum", "Kalenderwoche","Wochentag", "Monat", "Gewicht", "Frachtkosten", "Kategorisierung"]]
    #print(df_touren)
    df_pattern = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Belieferungsprofile\Ergebnisse\Pattern_results_data_['ZZZ', 'GRAU', 'BLAU', 'GELB', 'GRÜN']var_gewicht100_var_frequenz100_mindest_frequenz1.csv",
                                      encoding="latin_1", sep=";")

    df_pattern_only = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Belieferungsprofile\Ergebnisse\Pattern_results_data_only['ZZZ', 'GRAU', 'BLAU', 'GELB', 'GRÜN']var_gewicht100_var_frequenz100_mindest_frequenz1.csv",
                                      encoding="latin_1", sep=";")

    df_pattern_075 = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Belieferungsprofile\Ergebnisse\Pattern_results_data_['ZZZ', 'GRAU', 'BLAU', 'GELB', 'GRÜN']var_gewicht0.75_var_frequenz0.75_mindest_frequenz1.csv",
                                      encoding="latin_1", sep=";")
    df_pattern_133 = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Belieferungsprofile\Ergebnisse\Pattern_results_data_['ZZZ', 'GRAU', 'BLAU', 'GELB', 'GRÜN']var_gewicht1.33_var_frequenz1.33_mindest_frequenz1.csv",
                                      encoding="latin_1", sep=";")
    df_pattern_100 = pd.read_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Belieferungsprofile\Ergebnisse\Pattern_results_data_['ZZZ', 'GRAU', 'BLAU', 'GELB', 'GRÜN']var_gewicht100_var_frequenz100_mindest_frequenz1.csv",
                                      encoding="latin_1", sep=";")

    creatDiagrammAbsolute(df_touren, "Kalenderwoche", version)
    creatDiagrammAbsolute(df_touren, "Monat", version)
    creatDiagrammGewichtWeekdays(df_touren, version, df_pattern= df_pattern)
    creatDiagrammGewichtWeekdays_vergleich(df_touren, version, df_pattern_075, df_pattern_133, df_pattern_100)
    creatDiagrammSendungWeekdays(df_touren, version, df_pattern= df_pattern)
    creatDiagrammGewichtWeekdaysPattern_only(df_touren, version, df_pattern=df_pattern_only)
    creatDiagrammSendungenWeekdaysPattern_only(df_touren, version, df_pattern=df_pattern_only)
    creatDiagrammNoKategories(df_touren, "Kalenderwoche", version)
    creatDiagrammNoKategories(df_touren, "Monat", version)
    creatDiagrammRelative(df_touren, "Monat", version)
    creatDiagrammRelativeFrachtkosten(df_touren, "Monat", version)
    creatDiagrammRelativeSendungen(df_touren, "Monat", version)


    #df_pattern = pd.read_csv(
    #    r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Belieferungsprofile\Ergebnisse\Pattern_results_data_['ZZZ', 'GRAU', 'BLAU', 'GELB', 'GRÜN']var_gewicht0.75_var_frequenz0.75_mindest_frequenz1.csv",
    #    encoding="latin_1", sep=";")

    #df_pattern_only = pd.read_csv(
    #    r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Belieferungsprofile\Ergebnisse\Pattern_results_data_only['ZZZ', 'GRAU', 'BLAU', 'GELB', 'GRÜN']var_gewicht0.75_var_frequenz0.75_mindest_frequenz1.csv",
    #    encoding="latin_1", sep=";")

    #creatDiagrammWeekdays(df_touren, version, df_pattern=df_pattern)
    #creatDiagrammWeekdaysPattern_only(df_touren, version, df_pattern=df_pattern_only)


    #print(df_touren.head())