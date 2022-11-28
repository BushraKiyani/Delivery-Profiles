#Multiplot für 4*2 und 3*2 Diagramme
import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def multiplot4x2(df_analyse_kat,speicherpfad,title = None):
    def set_form_right(bar):
        bar.set(ylim=(-0.01, 1.1))
        bar.yaxis.set_ticks(np.arange(0, 1.01, 0.25))
        bar.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))
        bar.set(xlabel=None)
        bar.set(ylabel=None)
        bar.yaxis.set_label_position("right")
        bar.xaxis.set_label_position("top")

    def set_form_left(bar):
        bar.set(ylim=(-0.01, 1.1))
        bar.yaxis.set_ticks(np.arange(0, 1.01, 0.25))
        bar.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))
        bar.set(xlabel=None)
        bar.set(ylabel=None)
        bar.xaxis.set_label_position("top")

    def add_values(bar):
        def nachkomma(height):
            if height== 0:
                return ".0%"
            elif height<= 0.01:
                return ".2%"
            elif height>= 0.99:
                return ".0%"
            elif height< 0.99:
                return ".1%"


        for p in bar.patches:
            bar.annotate(format(p.get_height(), nachkomma(p.get_height())), (p.get_x() + p.get_width() / 2., p.get_height()), ha='center',
                         va='center', xytext=(0, 5), textcoords='offset points')

    figure, axes = plt.subplots(nrows=4, ncols=2, figsize=(10, 10))
    #figure.suptitle(title,fontsize = 16)

    bar11 = sns.barplot(x='Kategorisierung', y="Empfänger_Prozent", data=df_analyse_kat,
                        ax=axes[0][0], color="grey")
    set_form_left(bar11)
    bar11.set(xlabel="Anteil")
    bar11.set(xticks=[])
    add_values(bar11)

    bar12 = sns.barplot(x='Kategorisierung', y="Empfänger_Prozent_cumsum", data=df_analyse_kat,
                        ax=axes[0][1], color="grey")
    set_form_right(bar12)
    bar12.set(xlabel="akkumulierter Anteil")
    bar12.set(ylabel="Kunden")
    bar12.set(xticks=[])
    bar12.set(yticks=[])
    add_values(bar12)

    bar21 = sns.barplot(x='Kategorisierung', y="Sendungen_Prozent", data=df_analyse_kat,
                        ax=axes[1][0], color="grey")
    set_form_left(bar21)
    bar21.set(xticks=[])
    add_values(bar21)

    bar22 = sns.barplot(x='Kategorisierung', y="Sendungen_Prozent_cumsum", data=df_analyse_kat,
                        ax=axes[1][1], color="grey")
    set_form_right(bar22)
    bar22.set(ylabel="Sendungen")
    bar22.set(xticks=[])
    bar22.set(yticks=[])
    add_values(bar22)

    bar31 = sns.barplot(x='Kategorisierung', y="Frachtkosten_Prozent", data=df_analyse_kat,
                        ax=axes[2][0], color="grey")
    set_form_left(bar31)
    bar31.set(xticks=[])
    add_values(bar31)

    bar32 = sns.barplot(x='Kategorisierung', y="Frachtkosten_Prozent_cumsum", data=df_analyse_kat,
                        ax=axes[2][1], color="grey")
    set_form_right(bar32)
    bar32.set(ylabel="Kosten")
    bar32.set(xticks=[])
    bar32.set(yticks=[])
    add_values(bar32)

    bar41 = sns.barplot(x='Kategorisierung', y="Gewicht_Prozent", data=df_analyse_kat,
                        ax=axes[3][0], color="grey")
    set_form_left(bar41)
    for tick in bar41.get_xticklabels():
        tick.set_rotation(45)
    add_values(bar41)

    bar42 = sns.barplot(x='Kategorisierung', y="Gewicht_Prozent_cumsum", data=df_analyse_kat,
                        ax=axes[3][1], color="grey")
    set_form_right(bar42)
    bar42.set(ylabel="Gewicht")
    bar42.set(yticks=[])
    for tick in bar42.get_xticklabels():
        tick.set_rotation(45)
    add_values(bar42)

    figure.tight_layout()
    #figure.subplots_adjust(top=0.88)
    plt.subplots_adjust(wspace=0.05, hspace=0.05)

    plt.savefig(speicherpfad, dpi=2000)
    # plt.show()

def multiplot3x2(df_analyse_kat,speicherpfad, title =None):
    def set_form_right(bar):
        bar.set(ylim=(-0.01, 1.1))
        bar.yaxis.set_ticks(np.arange(0, 1.01, 0.25))
        bar.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))
        bar.set(xlabel=None)
        bar.set(ylabel=None)
        bar.yaxis.set_label_position("right")
        bar.xaxis.set_label_position("top")
    def set_form_left(bar):
        bar.set(ylim=(-0.01, 1.1))
        bar.yaxis.set_ticks(np.arange(0, 1.01, 0.25))
        bar.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))
        bar.set(xlabel=None)
        bar.set(ylabel=None)
        bar.xaxis.set_label_position("top")
    def nachkomma(height):
        if height == 0:
            return ".0%"
        elif height >= 0.01:
            return ".0%"
        elif height < 0.01:
            return ".1%"
    def add_values(bar):
        for p in bar.patches:
            bar.annotate(format(p.get_height(), nachkomma(p.get_height())), (p.get_x() + p.get_width() / 2., p.get_height()), ha='center',
                           va='center', xytext=(0, 5), textcoords='offset points')

    figure, axes = plt.subplots(nrows=3, ncols=2, figsize=(10, 10))
    #figure.suptitle(title,fontsize = 16)

    bar11 = sns.barplot(x='Kategorisierung', y="Sendungen_Prozent", data=df_analyse_kat,
                ax=axes[0][0], color="grey")
    set_form_left(bar11)
    bar11.set(xlabel="Anteil")
    bar11.set(xticks=[])
    add_values(bar11)

    bar12 = sns.barplot(x='Kategorisierung', y="Sendungen_Prozent_cumsum", data=df_analyse_kat,
                ax=axes[0][1], color="grey")
    set_form_right(bar12)
    bar12.set(xlabel="akkumulierter Anteil")
    bar12.set(ylabel="Sendungen")
    bar12.set(xticks=[])
    bar12.set(yticks=[])
    add_values(bar12)

    bar31 = sns.barplot(x='Kategorisierung', y="Frachtkosten_Prozent", data=df_analyse_kat,
                ax=axes[1][0], color="grey")
    set_form_left(bar31)
    bar31.set(xticks=[])
    add_values(bar31)

    bar32 = sns.barplot(x='Kategorisierung', y="Frachtkosten_Prozent_cumsum", data=df_analyse_kat,
                ax=axes[1][1], color="grey")
    set_form_right(bar32)
    bar32.set(ylabel= "Kosten")
    bar32.set(xticks=[])
    bar32.set(yticks=[])
    add_values(bar32)

    bar41 = sns.barplot(x='Kategorisierung', y="Gewicht_Prozent", data=df_analyse_kat,
                ax=axes[2][0], color="grey")
    set_form_left(bar41)
    for tick in bar41.get_xticklabels():
        tick.set_rotation(45)
    add_values(bar41)

    bar42 = sns.barplot(x='Kategorisierung', y="Gewicht_Prozent_cumsum", data=df_analyse_kat,
                ax=axes[2][1], color="grey")
    set_form_right(bar42)
    bar42.set(ylabel= "Gewicht")
    bar42.set(yticks=[])
    for tick in bar42.get_xticklabels():
        tick.set_rotation(45)
    add_values(bar42)

    figure.tight_layout()
    #figure.subplots_adjust(top=0.88)
    plt.subplots_adjust(wspace=0.05, hspace=0.05)

    plt.savefig(speicherpfad,dpi = 2000)
    #plt.show()