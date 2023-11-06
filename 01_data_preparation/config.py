# config.py

# Sender's Coordinates
sender_lon = 9.3372
sender_lat = 53.124339

# Processed data Path
data_path = r"00_Resources/Grunddaten/preprocessed_data.csv"
# Transport matrix path
transport_price_path = r"00_Resources/Transportpreismatrix_TK.csv"
# Adding coordinates
json_coordinate_list_path = r"00_Resources/Grunddaten/coordinates_list.json"
df_coordinates_path = r"00_Resources/Grunddaten/added_coordinates1.csv"

# Adding distances
chunk_size = 100
distances_path_C = r"00_Resources/Matrices/Real_Distanzmatrix.csv"
duration_path_C = r"00_Resources/Matrices/Real_Durationsmatrix.csv"
euk_distance_path_C = "00_Resources/Matrices/Euclidean_Distancematrix.csv"
matrix_table_path_C = r"00_Resources/Matrices/Combined_Matrixtable.csv"
distances_path_S =  r"00_Resources/Matrices/Real_Distances_Sender.csv"
duration_path_S = r"00_Resources/Matrices/Durations_Sender.csv"
euk_distance_path_S = r"00_Resources/Matrices/Euclidean_Distance_Sender.csv"
df_distance_path = r"00_Resources/Grunddaten/df_added_distances.csv"

# Freight cost calculations
tarifart = "matrix"  # "grundpreis + tonne", "matrix"
preis_basis = 23.28
preis_tonne = 35.31
column_name = 'Frachtkosten' # Name of the column where freight cost will be saved in the dataset
df_freightcost_path = "00_Resources/Grunddaten/df_added_freightcost.csv"
new_freightcost_path = "00_Resources/Grunddaten/df_recal_freightcost.csv"

# Variability Evaluation
df_frequency_path = r"00_Resources/pre_Analysis/Variabilitätsauswertung/frequenz_per_week.csv"
df_weight_path = r"00_Resources/pre_Analysis/Variabilitätsauswertung/weight_per_week.csv"
variability_path = r"00_Resources/pre_Analysis/Variabilitätsauswertung/variability_evaluation.csv"
variability_path_EU = r"00_Resources/pre_Analysis/Variabilitätsauswertung/variability_evaluation_EU.csv"

# Profle assigmnet parameters
var_weight = 1.33
var_frequency = 1.33
min_frequency = 2

# Profiles assignment paths
save_path_special = "var_gewicht" + str(var_weight) + "_var_frequenz" + str(
    var_frequency) + "_mindest_frequenz" + str(min_frequency)

# Setting up the path to files
save_path_base = r"00_Resources/profile_results"

df_shipments_profile_path = r"00_Resources/profile_results/Ergebnisse/Pattern_results_data_only_withoutprofile_" + save_path_special + ".csv"
df_assigned_profile_path = r"00_Resources/profile_results/Ergebnisse/Pattern_results_data_only_" + save_path_special + ".csv"
df_result_path = r"00_Resources/profile_results/Ergebnisse/Pattern_results_data_" + save_path_special +".csv"
df_clustered_shipments_profile_path = r"00_Resources/profile_results/Clustered_Ergebnisse/Pattern_results_data_only_withoutprofile_" + save_path_special + ".csv"
df_clustered_assigned_profile_path = r"00_Resources/profile_results/Clustered_Ergebnisse/Pattern_results_data_only_" + save_path_special + ".csv"
df_clustered_result_path = r"00_Resources/profile_results/Clustered_Ergebnisse/Pattern_results_data_" + save_path_special +".csv"

df_demand_base = r"00_Resources/profile_results/Profilzuweisung" #Model result
df_profile_base = r"00_Resources/profile_results/Ergebnisse/Pattern_results_data_only_"
plots_base = r'00_Resources/profile_results/Plots/'

df_clustered_demand_base = r"00_Resources/profile_results/Clustered_Profilzuweisung" #Model result
df_clustered_profile_base = r"00_Resources/profile_results/Clustered_Ergebnisse/Pattern_results_data_only_"
clustered_plots_base = r'00_Resources/profile_results/Plots/'


num_clusters = 5
# Assign colors to clusters
cluster_colors = ['#FF5733', '#33FF57', '#5733FF', '#FF33E6', '#33E6FF']
# '#FF0233', '#33FF98', '#8803FF', '#FF3188', '#88FF33']

