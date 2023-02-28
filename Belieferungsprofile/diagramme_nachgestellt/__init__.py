import pandas as pd
from datetime import datetime, timedelta, date
import seaborn as sns
import matplotlib.pyplot as plt
import glob
import numpy as np
from scipy.interpolate import make_interp_spline, BSpline

def diagramm_local_search():

    y_2 = np.array([6.5, 6, 5.8, 5.5, 5,   4,  3, 2.5,  2.0, 4, 6])
    y_1 = np.array([5.5, 4, 3,   4,   4.5, 4,  3, 2.5,   2.0, 4, 6])

    x = np.array([1,2,3,4,5,6, 6.5,7,8,9,10])
    xnew = np.linspace(x.min(), x.max(), 300)

    spl = make_interp_spline(x, y_1, k=3)
    y_smooth_1 = spl(xnew)

    spl = make_interp_spline(x, y_2, k=3)
    y_smooth_2 = spl(xnew)


    plt.figure(figsize= (10,4))
    l_1 = plt.plot(xnew, y_smooth_2, color = "grey",linewidth=2.0, linestyle='--')
    l_2 = plt.plot(xnew, y_smooth_1, color="lightgrey",linewidth=2.0)
    plt.xticks([])
    plt.yticks([])
    plt.ylabel("Zielfunktionswert")
    plt.xlabel("Lösungen")

    plt.tight_layout()

    plt.savefig((
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Diagramme\Local_search.pdf"))


def diagramm_tarif():
    data_s_konst_1 = {"s_konst": [10] * 3,
                    "x": [1,2,3]}
    data_s_konst_2 = {"s_konst": [20] * 3,
                      "x": [3,4,5]}
    data_s_konst_3 = {"s_konst": [30] * 3,
                      "x": [5,6,7]}

    plt.clf()
    plt.figure(figsize=(10, 4))
    s_1 = plt.plot(data_s_konst_1["x"], data_s_konst_1["s_konst"], color="grey", linewidth=2.0, )
    s_2 = plt.plot(data_s_konst_2["x"], data_s_konst_2["s_konst"], color="grey", linewidth=2.0, )
    s_3 = plt.plot(data_s_konst_3["x"], data_s_konst_3["s_konst"], color="grey", linewidth=2.0,label = "$S^{konstant}$" )


    data_s_var_1 = {"s_var": [ 1,1],
                    "x": [1,2]}
    data_s_var_2 = {"s_var": [3, 3],
                    "x": [2, 3]}
    data_s_var_3 = {"s_var": [5, 5],
                    "x": [3, 4]}
    data_s_var_4 = {"s_var": [6,6,6],
                    "x": [4, 5,6]}
    data_s_var_5 = {"s_var": [7,7,7,7],
                    "x": [6, 7,8,9]}
    data_s_var_6 = {"s_var": [8,8,8,8],
                    "x": [9,10,11,12]}
    data_s_var_7 = {"s_var": [8.5,8.5,8.5,8.5,8.5],
                    "x": [12,13,14,15,16]}

    s_4 = plt.plot(data_s_var_1["x"], data_s_var_1["s_var"], color="grey", linewidth=2.0,linestyle = "dotted" )
    s_5 = plt.plot(data_s_var_2["x"], data_s_var_2["s_var"], color="grey", linewidth=2.0,linestyle = "dotted" )
    s_6 = plt.plot(data_s_var_3["x"], data_s_var_3["s_var"], color="grey", linewidth=2.0,linestyle = "dotted" )
    s_7 = plt.plot(data_s_var_4["x"], data_s_var_4["s_var"], color="grey", linewidth=2.0,linestyle = "dotted" )
    s_8 = plt.plot(data_s_var_5["x"], data_s_var_5["s_var"], color="grey", linewidth=2.0,linestyle = "dotted" )
    s_9 = plt.plot(data_s_var_6["x"], data_s_var_6["s_var"], color="grey", linewidth=2.0,linestyle = "dotted")
    s_9 = plt.plot(data_s_var_7["x"], data_s_var_7["s_var"], color="grey", linewidth=2.0, label = "$S^{variabel}$",linestyle = "dotted")

    data_l_1 = {"l_1": [1,5,9,14,16,18,20,22,23,24,25,26,27,28,29,30],
                    "x": list(range(1,17))}
    l_1 = plt.plot(data_l_1["x"], data_l_1["l_1"], color="grey", linewidth=2.0,label = "$L_{1}$",linestyle = "dashdot")

    data_l_21 = {"l_2": [1,4,7,10],
                    "x": [1,2,3,4]}
    data_l_22 = {"l_2": [7,9,11,13,15],
                    "x": [4,5,6,7,8]}
    data_l_23 = {"l_2": [11,12,13,14,15,16,17,18,19],
                    "x": [8,9,10,11,12,13,14,15,16]}

    l21 = plt.plot(data_l_21["x"], data_l_21["l_2"], color="grey", linewidth=2.0, linestyle = (0,(5,1)))
    l22 = plt.plot(data_l_22["x"], data_l_22["l_2"], color="grey", linewidth=2.0, linestyle = (0,(5,1)))
    l23 = plt.plot(data_l_23["x"], data_l_23["l_2"], color="grey", linewidth=2.0, label = "$L_{2}$", linestyle = (0,(5,1)))

    plt.margins(0)
    plt.ylim(top=35,bottom = 0)
    plt.xticks([2,4,6,8,10,12,14,16],labels = [])
    plt.yticks([5,10,15,20,25,30], labels = [])
    plt.ylabel("Frachtkosten")
    plt.xlabel("Gewicht/Volumen")
    legend = plt.legend(loc='upper left')

    plt.tight_layout()
    plt.savefig((
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Diagramme\Tarifstrukturen.pdf"))
    plt.show()





if __name__ == '__main__':
    print("")
    diagramm_local_search()
    diagramm_tarif()