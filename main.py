from b_create_Tarifmatrix import *
from c_create_Distancematrix import *
from a_Variability import *
from a_apply_profiles import *
from a_add_Coordinates import *
from config import *
from weekday_analysis_plots import *
from a_apply_clustered_profiles import *
from maps_visualization import *

if __name__ == "__main__":

    transport_preis = pd.read_csv(transport_price_path, encoding="latin_1", sep=";", decimal=',')
    data_processed = pd.read_csv(df_freightcost_path, encoding="latin_1", sep=";", decimal=',')

    # Check if 'latitude' and 'longitude' columns exist in the DataFrame
    if 'Recipient_Longitude' in data_processed.columns and 'Recipient_Latitude' in data_processed.columns\
            and 'Sender_Longitude' in data_processed.columns and 'Sender_Latitude' in data_processed.columns:
        print("Coordinates already exist in the data. Calculating distances...")
        df_added_coordinates = data_processed
        # Load coordinates from JSON file
        with open(json_coordinate_list_path, 'r') as f:
            list_coordinates = json.load(f)
    else:
        print("Coordinates do not exist in the data. Adding coordinates...")
        df_added_coordinates, list_coordinates = add_coordinates(data_processed, sender_lon, sender_lat,
                                                                 df_coordinates_path, json_coordinate_list_path)

    # Check if 'latitude' and 'longitude' columns exist in the DataFrame
    if 'Real_Distance' in data_processed.columns and 'Duration' in data_processed.columns\
            and 'Euc_Distance' in data_processed.columns:
        print("Distances already exist in the data. Calculating freightcost...")
        df_added_distances = df_added_coordinates
    else:
       print("Distances do not exist in the data. Adding distances...")
       # Calculate distances
       distances, durations, euclidean, distance_table, df_added_distances = \
        create_distance_matrices(df_added_coordinates, list_coordinates, sender_lon, sender_lat,distances_path_C,
                                 duration_path_C,euk_distance_path_C,matrix_table_path_C,distances_path_S,
                                 duration_path_S, euk_distance_path_S, df_distance_path, chunk_size=100)

    if column_name in data_processed.columns:
        print("Cost already exists in the data. Calculating shipments and weight per week per ID_recipient...")
        df_added_freightcost = df_added_distances
    else:
        print("Costs do not exist in the data. Adding costs...")
        # Calculate Freight Cost
        df_added_freightcost = add_cost(df_added_distances,transport_preis,df_freightcost_path, column_name, tariff_type,
                                        price_basis, price_per_ton)
    # Shipments and weight per week per ID_recipient
    df_frequency, df_weight = evaluation_after_KW1(df_added_freightcost,df_frequency_path, df_weight_path )
    # Variability analysis
    df_var_evaluation = variability_evaluation(df_frequency, df_weight, df_added_freightcost, variability_path,
                                               variability_path_EU)
    df_assigned_pattern = pattern_assignment(df_var_evaluation, var_weight, var_frequency, min_frequency,save_path_base,
                                             save_path_special)
    df_assigned_clustered_pattern, list_coordinates_clustered = clustered_pattern_assignment(df_var_evaluation, list_coordinates, var_weight, var_frequency, min_frequency, num_clusters, save_path_base,
                                             save_path_special)
    df_assigned_profile = profile_application(df_added_freightcost, df_assigned_pattern, df_assigned_profile_path, df_result_path, df_shipments_profile_path, df_clustered_shipments_profile_path, df_clustered_assigned_profile_path, df_clustered_result_path, clustered="No")
    df_clustered_assigned_profile = profile_application(df_added_freightcost, df_assigned_clustered_pattern, df_assigned_profile_path,
                                              df_result_path, df_shipments_profile_path,
                                              df_clustered_shipments_profile_path, df_clustered_assigned_profile_path,
                                              df_clustered_result_path, clustered="Yes")

    df_recal_freightcost= add_cost(df_assigned_profile,transport_preis,new_freightcost_path, column_name, tariff_type,
                                   price_basis, price_per_ton)
    df_recal_clustered_freightcost= add_cost(df_clustered_assigned_profile,transport_preis,new_freightcost_path, column_name, tariff_type,
                                   price_basis, price_per_ton)

    plots(df_demand_base, save_path_special, df_profile_base, df_added_freightcost, plots_base, df_result_path, "Non-Clustered")
    plots(df_clustered_demand_base, save_path_special, df_clustered_profile_base, df_added_freightcost,
          clustered_plots_base, df_clustered_result_path, clustered= "Clustered")

    maps(list_coordinates_clustered, df_assigned_clustered_pattern)
