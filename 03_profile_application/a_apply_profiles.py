from ortools.linear_solver import pywraplp
import numpy
import pandas as pd
from b_calc_costs import *
import time
import math

solver = pywraplp.Solver.CreateSolver('SCIP')

def data(speicherpfad_base, speicherpfad_speziell, var_gewicht = 100, var_frequenz = 100, mindest_frequenz = 1):
    data = pd.read_csv(
        r"../00_Resources/pre_Analysis/Variabilitätsauswertung/Variablitätsauswertung.csv",
        encoding="latin-1",
        sep=";")

    #filter
    data = data.loc[(data["variability_Gewicht"]<= var_gewicht) & (data["variability_Frequenz"]<= var_frequenz) & (data["avg_Frequenz"]>= mindest_frequenz) ]
    print(data.head())

    def round_costum(value_x, border):
        value_floor = math.floor(value_x)
        if value_x - value_floor >= border:
            return math.ceil(value_x)
        else:
            return  math.floor(value_x)

    frequenz_avg_array = []
    gewicht_avg_array = []
    for index, row in data.iterrows():
        frequenz_avg_array.append(round_costum(row["avg_Frequenz"], 0.25))
        gewicht_avg_array.append(round(row["avg_Gewicht"] /row["avg_Frequenz"]))

    df_parameter = pd.DataFrame(data= {"ID_Empfänger": data["ID_Empfänger"],
                                       "Frequenz": frequenz_avg_array,
                                       "Nachfrage": gewicht_avg_array})

    speicherpfad = speicherpfad_base +r'/Ausgangsdaten' +r"/Daten_" + speicherpfad_speziell+ ".csv"
    df_parameter.to_csv(speicherpfad, encoding="latin-1", sep=";")
    return df_parameter

def parameter(empfänger, nachfrage ,frequenz):
    PAT = {
        5:
            [[1, 1, 1, 1, 1]],
        4:
            [[0, 1, 1, 1, 1],
             [1, 0, 1, 1, 1],
             [1, 1, 0, 1, 1],
             [1, 1, 1, 0, 1],
             [1, 1, 1, 1, 0]],

        3: [[0, 1, 0, 1, 1],
            [1, 0, 1, 0, 1],
            [1, 1, 0, 1, 0],
            [0, 1, 1, 0, 1],
            [1, 0, 1, 1, 0],
            ],

        2: [[1, 0, 1, 0, 0],
            [0, 1, 0, 1, 0],
            [0, 0, 1, 0, 1],
            [1, 0, 0, 1, 0],
            [0, 1, 0, 0, 1]],

        1: [[1, 0, 0, 0, 0],
            [0, 1, 0, 0, 0],
            [0, 0, 1, 0, 0],
            [0, 0, 0, 1, 0],
            [0, 0, 0, 0, 1]],
    }

    days = 5
    C = empfänger
    #print(C)
    q = nachfrage
    #print(q)
    f = frequenz


    bigM = 999999999

    return PAT,days,C, q, f, bigM

def variablen(PAT,days,C, q, f, bigM):
    infinity = solver.infinity()

    s = solver.IntVar(0, infinity, "")

    x = {}
    for j in range(len(C)):
        for m in range(len(PAT[f[j]])):
            x[j, m] = solver.IntVar(0, 1, "")

    return infinity,s,x

def nebenbedingungen(PAT,days,C, q, f, bigM, s,x):
    # 13

    for t in range(days):
        solver.Add(solver.Sum([x[j, m] * PAT[f[j]][m][t] * q[j]
                               for j in range(len(C))
                               for m in range(len(PAT[f[j]]))])
                   <= s)

    # 16
    for j in range(len(C)):
        solver.Add(solver.Sum(x[j, m] for m in range(len(PAT[f[j]]))) == 1)

def print_ergebnisse(PAT,days,C, q, f, bigM, s,x, sol):
    for j in range(len(C)):
        for m in range(len(PAT[f[j]])):
            if x[j,m].solution_value() != 0:
                print("Kunde: ", j)
                print("Demand: ", q[j])
                print("Frequenz: ", f[j])
                print("Ausgewählte Pattern: ",PAT[f[j]][m])
                print()

    demand_array = []

    for t in range(days):
        demand_per_day = 0
        for j in range(len(C)):
            for m in range(len(PAT[f[j]])):
                if x[j, m].solution_value() != 0:
                    demand_per_day += PAT[f[j]][m][t] * q[j]
        demand_array.append(demand_per_day)

    if sol == pywraplp.Solver.OPTIMAL:
        print("---Optimal Solution found---")
    else:
        print('The problem does not have an optimal solution.')

    print("Versandmenge pro Tag", demand_array)
    print()
    print('Maximum am Tag = ', solver.Objective().Value())
    print()
    print('Problem solved in %f milliseconds' % solver.wall_time())
    print('Problem solved in %d iterations' % solver.iterations())
    print('Problem solved in %d branch-and-bound nodes' % solver.nodes())

def save_ergebnisse(PAT,days,C, q, f, bigM, s,x, speicherpfad_base, speicherpfad_speziell ):
    ID_array = []
    dem_array = []
    freq_array = []
    pat_array = []
    pat_clear = []

    for j in range(len(C)):
        for m in range(len(PAT[f[j]])):
            if x[j,m].solution_value() != 0:
                ID_array.append(C[j])
                dem_array.append(q[j])
                freq_array.append(f[j])
                pat_array.append([m][0])
                pat_clear.append(PAT[f[j]][m])

    df_ergebnisse =  pd.DataFrame(data= {"ID_Empfänger": ID_array,
                                         "Frequenz": freq_array,
                                         "Nachfrage": dem_array,
                                         "Pattern" : pat_array,
                                         "Pattern_clear" : pat_clear,
                                         })
    speicherpfad = speicherpfad_base + r'/Profilzuweisung/' + speicherpfad_speziell + ".csv"
    df_ergebnisse.to_csv(speicherpfad, encoding="latin-1", sep=";")

    return df_ergebnisse

def patternzuordnung(var_gewicht, var_frequenz, mindest_frequenz, speicherpfad_speziell):

    speicherpfad_base = r"../00_Resources/profile_results"

    df_parameter = data(speicherpfad_base, speicherpfad_speziell, var_gewicht, var_frequenz, mindest_frequenz) # Gerundete avg. Frequenz und Gewicht ergänzen

    PAT, days, C, q, f, bigM = parameter(df_parameter["ID_Empfänger"].values, df_parameter["Nachfrage"].values,
                                         df_parameter["Frequenz"].values)

    infinity, s, x = variablen(PAT, days, C, q, f, bigM)

    nebenbedingungen(PAT, days, C, q, f, bigM, s, x)

    # Zielfunktion
    solver.Minimize(s)
    # Solver Timelimit
    solver.SetTimeLimit(180)

    sol = solver.Solve()

    print_ergebnisse(PAT, days, C, q, f, bigM, s, x, sol)

    df_ergebnisse = save_ergebnisse(PAT, days, C, q, f, bigM, s, x, speicherpfad_base, speicherpfad_speziell)
    return df_ergebnisse

if __name__ == '__main__':
    var_gewicht = 1.33
    var_frequenz = 1.33
    mindest_frequenz = 1


    einsparungs_array = []
    solvingtime_array = []

    speicherpfad_speziell = "var_gewicht" + str(var_gewicht) + "_var_frequenz" + str(
            var_frequenz) + "_mindest_frequenz" + str(mindest_frequenz)


    df_pattern = patternzuordnung(var_gewicht, var_frequenz, mindest_frequenz, speicherpfad_speziell)
    print("---PATTTERNZUORDNUNG ERFOLGT---")

    df_touren = pd.read_csv(
            r"../00_Resources/Grunddaten/Datensatz_TK_fertig.csv",
            encoding="latin_1", sep=";")
    frachtkosten_vorher = df_touren["Frachtkosten"].sum()

    frachtkosten_nachher = profilanwendung(speicherpfad_speziell)
    print("---PATTERN ANGEWENDET---")

    print(str(round(((frachtkosten_vorher - frachtkosten_nachher) / frachtkosten_vorher)*100,2))+"%")
    einsparungs_array.append(str(round(((frachtkosten_vorher - frachtkosten_nachher) / frachtkosten_vorher)*100,2))+"%")
    solvingtime_array.append(solver.wall_time())

    df_ergebnisse = pd.DataFrame(data={"Einsparung":einsparungs_array,
                                       "Lösungszeit": solvingtime_array})