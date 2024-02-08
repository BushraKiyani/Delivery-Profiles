# config.py

# Sender's Coordinates
sender_lon = 9.3372
sender_lat = 53.124339

# Processed data Path
data_path = r"00_Resources/Basic_Data/preprocessed_data.csv" #renamed
# Transport matrix path
transport_price_path = r"00_Resources/Transportpreismatrix_TK.csv"
# Adding coordinates
json_coordinate_list_path = r"00_Resources/Basic_Data/coordinates_list.json"
df_coordinates_path = r"00_Resources/Basic_Data/added_coordinates1.csv" #renamed

# Adding distances
chunk_size = 100
distances_path_C = r"00_Resources/Matrices/Real_Distanzmatrix.csv"
duration_path_C = r"00_Resources/Matrices/Real_Durationsmatrix.csv"
euk_distance_path_C = "00_Resources/Matrices/Euclidean_Distancematrix.csv"
matrix_table_path_C = r"00_Resources/Matrices/Combined_Matrixtable.csv"
distances_path_S =  r"00_Resources/Matrices/Real_Distances_Sender.csv"
duration_path_S = r"00_Resources/Matrices/Durations_Sender.csv"
euk_distance_path_S = r"00_Resources/Matrices/Euclidean_Distance_Sender.csv"
df_distance_path = r"00_Resources/Basic_Data/df_added_distances_re.csv" #renamed

# Freight cost calculations
tariff_type = "matrix"  # "grundpreis + tonne", "matrix"
price_basis = 23.28
price_per_ton = 35.31
column_name = 'Freight_Cost' # Name of the column where freight cost will be saved in the dataset
df_freightcost_path = "00_Resources/Basic_Data/df_added_freightcost_re.csv" #renamed
#new_freightcost_path = "00_Resources/Basic_Data/df_recal_freightcost.csv" #renamed
new_freightcost_path = "00_Resources/Basic_Data/df_recal_test_freightcost.csv"
# Variability Evaluation
df_frequency_path = r"00_Resources/pre_Analysis/Variability_Analysis/Frequency_per_week.csv" #renamed
df_weight_path = r"00_Resources/pre_Analysis/Variability_Analysis/weight_per_week.csv" #renamed
variability_path = r"00_Resources/pre_Analysis/Variability_Analysis/variability_evaluation.csv" #renamed
variability_path_EU = r"00_Resources/pre_Analysis/Variability_Analysis/variability_evaluation_EU.csv" #renamed recheck the structure

# Profle assigmnet parameters
var_weight = 1.33
var_frequency = 1.33
min_frequency = 2

# Profiles assignment paths
save_path_special = "var_Weight" + str(var_weight) + "_var_Frequency" + str(
    var_frequency) + "_minimum_Frequency" + str(min_frequency)

# Setting up the path to files
save_path_base = r"00_Resources/profile_results"
#output_csv_path = r"C:\Users\Owner\PycharmProjects\cls_delivery\00_Resources\profile_results\Results\routing_" + save_path_special + ".csv"
df_shipments_profile_path = r"00_Resources/profile_results/Results/Pattern_results_data_only_withoutprofile_" + save_path_special + ".csv"
df_assigned_profile_path = r"00_Resources/profile_results/Results/Pattern_results_data_only_" + save_path_special + ".csv"
df_result_path = r"00_Resources/profile_results/Results/Pattern_results_data_" + save_path_special +".csv"
df_clustered_shipments_profile_path = r"00_Resources/profile_results/Clustered_Results/Pattern_results_data_only_withoutprofile_" + save_path_special + ".csv"
df_clustered_assigned_profile_path = r"00_Resources/profile_results/Clustered_Results/Pattern_results_data_only_" + save_path_special + ".csv"
df_clustered_result_path = r"00_Resources/profile_results/Clustered_Results/Pattern_results_data_" + save_path_special +".csv"

df_demand_base = r"00_Resources/profile_results/Profile_Assignment" #Model result
df_profile_base = r"00_Resources/profile_results/Results/Pattern_results_data_only_"
plots_base = r'00_Resources/profile_results/Plots/'

df_clustered_demand_base = r"00_Resources/profile_results/Clustered_Profile_Assignment" #Model result
df_clustered_profile_base = r"00_Resources/profile_results/Clustered_Results/Pattern_results_data_only_"
clustered_plots_base = r'00_Resources/profile_results/Plots/'


num_clusters = 5
# Assign colors to clusters
cluster_colors = ['#FF5733', '#33FF57', '#5733FF', '#FF33E6', '#33E6FF']
# '#FF0233', '#33FF98', '#8803FF', '#FF3188', '#88FF33']
output_json_path = r"00_Resources/profile_results/routes.json"
output_json_path_C = r"00_Resources/profile_results/routes_cluster.json"
