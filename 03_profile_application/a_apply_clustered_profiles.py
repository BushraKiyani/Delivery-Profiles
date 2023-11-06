from ortools.linear_solver import pywraplp
from b_calc_costs import *
import math
from sklearn.cluster import KMeans
from math import radians

solver = pywraplp.Solver.CreateSolver('SCIP')

def empfänger_filtern(df_touren,speicherpfad_base, speicherpfad_speziell, var_Weight = 100, var_Frequency = 100, minimum_Frequency = 1):
    #filter
    data = df_touren.loc[(df_touren["Variability_Weight"]<= var_Weight)
                         & (df_touren["Variability_Frequency"]<= var_Frequency)
                         & (df_touren["AVG_Frequency"]>= minimum_Frequency)].copy()
    speicherpfad = speicherpfad_base +r'/Filtern/' + speicherpfad_speziell+ ".csv"
    data.to_csv(speicherpfad, encoding="latin-1", sep=";")
    return data

def round_costum(value_x, border):
    value_floor = math.floor(value_x)
    return math.ceil(value_x) if value_x - value_floor >= border else math.floor(value_x)

def process_data(data, speicherpfad_base, speicherpfad_speziell):
    # Round values in "AVG_Frequency" and "avg_Weight" columns
    data["Frequency"] = data["AVG_Frequency"].apply(lambda x: round_costum(x, 0.5)) # used function round_costum1
    data["Demand"] = data.apply(lambda row: round(row["avg_Weight"] / row["AVG_Frequency"]), axis=1)
    df_parameter = pd.DataFrame(data={ "Recipient_ID": data["Recipient_ID"], "Frequency": data["Frequency"], "Demand": data["Demand"], "Cluster": data["Cluster"] })
    speicherpfad = speicherpfad_base + r'/Clustered_Output_Data' + r"/Data_" + speicherpfad_speziell + ".csv"
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
    clusters = df_touren['Cluster'].values  # Add this line to get cluster information

    return PAT, C, q, f, days, clusters

def variablen(PAT, C, f):
    infinity = solver.infinity()

    s = solver.IntVar(0, infinity, "")

    x = {}
    for j in range(len(C)):
        for m in range(len(PAT[f[j]])):
            x[j, m] = solver.IntVar(0, 1, "")

    return s, x

def nebenbedingungen(PAT, days, C, q, f, s, x, clusters):
    # Restrictions
    # 13. Max less than the model specified max limit s
    for t in range(days):
        solver.Add(solver.Sum([x[j, m] * PAT[f[j]][m][t] * q[j]
                               for j in range(len(C))
                               for m in range(len(PAT[f[j]]))])
                   <= s)

    # 16. Every Recipient must be assigned one profile
    for j in range(len(C)):
        solver.Add(solver.Sum(x[j, m] for m in range(len(PAT[f[j]]))) == 1)

    # Recipients with the same cluster and the same frequency have the same pattern
    for j in range(len(C)):
        for i in range(len(C)):
            if clusters[j] == clusters[i] and f[j] == f[i]:
                for m in range(len(PAT[f[j]])):
                    solver.Add(x[j, m] == x[i, m])


def print_ergebnisse(PAT, days, C, q, f, clusters, x, sol):
    selected_patterns = [(j, m) for j in range(len(C)) for m in range(len(PAT[f[j]])) if x[j, m].solution_value() != 0]
    for j, m in selected_patterns:
        print("Recipient: ", j)
        print("Cluster: ", clusters[j])  # Print the cluster
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
    print('Maximum per Day= ', solver.Objective().Value())
    print()
    print('Problem solved in %f milliseconds' % solver.wall_time())
    print('Problem solved in %d iterations' % solver.iterations())
    print('Problem solved in %d branch-and-bound nodes' % solver.nodes())

def save_ergebnisse(PAT, C, q, f, clusters, x, speicherpfad_base, speicherpfad_speziell):
    selected_patterns = [(C[j], f[j], q[j], clusters[j], m, PAT[f[j]][m]) for j in range(len(C)) for m in range(len(PAT[f[j]])) if x[j, m].solution_value() != 0]
    ID_array, freq_array, dem_array, cluster_array, pat_array, pat_clear = zip(*selected_patterns)

    df_ergebnisse = pd.DataFrame(data={
        "Recipient_ID": ID_array,
        "Frequency": freq_array,
        "Demand": dem_array,
        "Cluster": cluster_array,  # Include the 'Cluster' column
        "Pattern": pat_array,
        "Pattern_clear": pat_clear,
    })

    speicherpfad = speicherpfad_base + r'/Clustered_Profile_Assignment/' + speicherpfad_speziell + ".csv"
    df_ergebnisse.to_csv(speicherpfad, encoding="latin-1", sep=";", index=False)

    return df_ergebnisse

def add_clusters(list_coordinates, filtered_df, num_clusters):
    df = pd.DataFrame(list_coordinates)
    # Select rows from df where Empfänger_id matches Recipient_ID in df_profile
    selected_df = df[df['Empfänger_id'].isin(filtered_df['Recipient_ID'])].copy()
    # Perform clustering (you can use your existing clustering code)
    selected_df['Latitude_Radians'] = selected_df['latitude'].apply(radians)
    selected_df['Longitude_Radians'] = selected_df['longitude'].apply(radians)
    X = selected_df[['Latitude_Radians', 'Longitude_Radians']]
    kmeans = KMeans(n_clusters=num_clusters, random_state=0, n_init=10)
    selected_df['Cluster'] = kmeans.fit_predict(X)
    cluster_mapping = dict(zip(selected_df['Empfänger_id'], selected_df['Cluster']))
    filtered_df['Cluster'] = filtered_df['Recipient_ID'].map(cluster_mapping)
    return filtered_df, selected_df

def clustered_pattern_assignment(data,list_coordinates, var_weight, var_Frequency, min_Frequency,num_clusters, speicherpfad_base, speicherpfad_speziell):
    print("Profile application has been started.")
    filtered_df = empfänger_filtern(data,speicherpfad_base,speicherpfad_speziell, var_weight,var_Frequency,min_Frequency) # Gerundete avg. Frequency und Weight ergänzen

    filtered_df_cluster, list_coordinates_clustered = add_clusters(list_coordinates, filtered_df, num_clusters)
    df_parameter = process_data(filtered_df_cluster, speicherpfad_base, speicherpfad_speziell)
    PAT, C, q, f, days, clusters = parameter(df_parameter)

    s,x = variablen(PAT,C,f)

    nebenbedingungen(PAT, days, C, q, f, s, x, clusters)

    # Zielfunktion
    solver.Minimize(s)
    # Solver Timelimit
    solver.SetTimeLimit(180)

    sol = solver.Solve()

    print_ergebnisse(PAT, days, C, q, f,clusters, x, sol)

    df_ergebnisse = save_ergebnisse(PAT, C, q, f,clusters, x, speicherpfad_base, speicherpfad_speziell)
    print("Clustered Pattern assignment has completed.")
    return df_ergebnisse, list_coordinates_clustered