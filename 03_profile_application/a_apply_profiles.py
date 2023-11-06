from ortools.linear_solver import pywraplp
from b_calc_costs import *
import math
solver = pywraplp.Solver.CreateSolver('SCIP')

############################################################################################################
# Filter the empfänger based on max_Weight, max_Frequency and minimum_Frequency
def empfänger_filtern(df_touren,speicherpfad_base, speicherpfad_speziell, var_Weight = 100, var_Frequency = 100, minimum_Frequency = 1):
    #filter
    data = df_touren.loc[(df_touren["Variability_Weight"]<= var_Weight)
                         & (df_touren["Variability_Frequency"]<= var_Frequency)
                         & (df_touren["AVG_Frequency"]>= minimum_Frequency)].copy()
    speicherpfad = speicherpfad_base +r'/Filtern/' + speicherpfad_speziell+ ".csv"
    data.to_csv(speicherpfad, encoding="latin-1", sep=";")
    return data

# round a numerical value based on a specified border.
def round_costum(value_x, border):
    value_floor = math.floor(value_x)
    return math.ceil(value_x) if value_x - value_floor >= border else math.floor(value_x)

# Create a new DataFrame named df_parameter
def process_data(data, speicherpfad_base, speicherpfad_speziell):
    # Round values in "AVG_Frequency" and "avg_Weight" columns
    data["Frequency"] = data["AVG_Frequency"].apply(lambda x: round_costum(x, 0.5)) # used function round_costum1
    data["Demand"] = data.apply(lambda row: round(row["avg_Weight"] / row["AVG_Frequency"]), axis=1)
    df_parameter = pd.DataFrame(data={ "Recipient_ID": data["Recipient_ID"], "Frequency": data["Frequency"], "Demand": data["Demand"] })
    speicherpfad = speicherpfad_base + r'/Output_Data' + r"/Data_" + speicherpfad_speziell + ".csv"
    df_parameter.to_csv(speicherpfad, encoding="latin-1", sep=";")
    return df_parameter

def parameter(df_touren):
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


    C = df_touren['Recipient_ID'].values
    q = df_touren['Demand'].values
    f = df_touren['Frequency'].values
    days = 5

    return PAT, C, q, f, days

def variablen(PAT,C, f):
    infinity = solver.infinity()

    s = solver.IntVar(0, infinity, "")

    x = {}
    for j in range(len(C)):
        for m in range(len(PAT[f[j]])):
            x[j, m] = solver.IntVar(0, 1, "")

    return s,x

def nebenbedingungen(PAT,days,C, q, f, s,x):
    # Restrictions
    # 13.  Max less than the model specified max limit s
    for t in range(days):
        solver.Add(solver.Sum([x[j, m] * PAT[f[j]][m][t] * q[j]
                               for j in range(len(C))
                               for m in range(len(PAT[f[j]]))])
                   <= s)

    # 16. Every Recipient must be assigned one profile
    for j in range(len(C)):
        solver.Add(solver.Sum(x[j, m] for m in range(len(PAT[f[j]]))) == 1)

    # Recipients with same cluster and same frequency have same pattern
    #for j in range(len(C)): # c with same freq and cluster
        #for i in range(len(C)): # c with same freq and cluster
           # solver.Add(x[j, m] == x[i, m] for m in range(len(PAT[f[j]])))

def print_ergebnisse(PAT, days, C, q, f, x, sol):
    selected_patterns = [(j, m) for j in range(len(C)) for m in range(len(PAT[f[j]])) if x[j, m].solution_value() != 0]
    for j, m in selected_patterns:
        print("Recipient: ", j)
        print("Demand: ", q[j])
        print("Frequency: ", f[j])
        print("Selected Pattern: ", PAT[f[j]][m])
        print()

    demand_array = [sum([PAT[f[j]][m][t] * q[j] for j, m in selected_patterns]) for t in range(days)]

    if sol == pywraplp.Solver.OPTIMAL:
        print("---Optimal Solution found---")
    else:
        print('The problem does not have an optimal solution.')

    print("Shipping Quantity per Day", demand_array)
    print()
    print('Maximum per Day = ', solver.Objective().Value())
    print()
    print('Problem solved in %f milliseconds' % solver.wall_time())
    print('Problem solved in %d iterations' % solver.iterations())
    print('Problem solved in %d branch-and-bound nodes' % solver.nodes())

def save_ergebnisse(PAT, C, q, f, x, speicherpfad_base, speicherpfad_speziell):
    selected_patterns = [(C[j], f[j], q[j], m, PAT[f[j]][m]) for j in range(len(C)) for m in range(len(PAT[f[j]])) if x[j, m].solution_value() != 0]
    ID_array, freq_array, dem_array, pat_array, pat_clear = zip(*selected_patterns)

    df_ergebnisse = pd.DataFrame(data={
        "Recipient_ID": ID_array,
        "Frequency": freq_array,
        "Demand": dem_array,
        "Pattern": pat_array,
        "Pattern_clear": pat_clear,
    })

    speicherpfad = speicherpfad_base + r'/Profile_Assignment/' + speicherpfad_speziell + ".csv"
    df_ergebnisse.to_csv(speicherpfad, encoding="latin-1", sep=";", index= False)

    return df_ergebnisse

def pattern_assignment(data, var_weight, var_Frequency, min_Frequency,speicherpfad_base, speicherpfad_speziell):
    print("Profile application has been started.")
    filtered_df = empfänger_filtern(data,speicherpfad_base,speicherpfad_speziell, var_weight,var_Frequency,min_Frequency) # Gerundete avg. Frequency und Weight ergänzen
    #data_fil = pd.read_csv(r"../00_Resources/profile_results/Filtern/var_Weight100_var_Frequency100_minimum_Frequency1.csv",
       # encoding="latin_1", sep=";")
    df_parameter = process_data(filtered_df, speicherpfad_base, speicherpfad_speziell)
    PAT, C, q, f, days = parameter(df_parameter)

    s,x = variablen(PAT,C,f)

    nebenbedingungen(PAT, days, C, q, f, s, x)

    # Zielfunktion
    solver.Minimize(s)
    # Solver Timelimit
    solver.SetTimeLimit(180)

    sol = solver.Solve()

    print_ergebnisse(PAT, days, C, q, f, x, sol)

    df_ergebnisse = save_ergebnisse(PAT, C, q, f, x, speicherpfad_base, speicherpfad_speziell)
    print("Pattern assignment has completed.")
    return df_ergebnisse




