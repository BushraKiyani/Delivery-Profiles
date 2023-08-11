from b_create_Tarifmatrix import *
from c_create_Distancematrix import *
from a_Variability import *
from a_apply_profiles import *
from a_adjust_Record import *
from config import *

if __name__ == "__main__":

    transport_preis = pd.read_csv(transport_price_path, encoding="latin_1", sep=";", decimal=',')
    data_processed = pd.read_csv(df_coordinates_path, encoding="latin_1", sep=";", decimal=',')

    # Check if 'latitude' and 'longitude' columns exist in the DataFrame
    if 'Empfänger_lon' in data_processed.columns and 'Empfänger_lat' in data_processed.columns\
            and 'Absender_lon' in data_processed.columns and 'Absender_lat' in data_processed.columns:
        print("Coordinates already exist in the data. Calculating distances...")
        df_added_coordinates = data_processed
        # Load coordinates from JSON file
        with open(json_coordinate_list_path, 'r') as f:
            list_coordinates = json.load(f)
    else:
        print("Coordinates do not exist in the data. Adding coordinates...")
        df_added_coordinates, list_coordinates = add_coordinates(data_processed, sender_lon, sender_lat, df_coordinates_path, json_coordinate_list_path)

    # Calculate distance matrices
    distances, durations, euclidean, distance_table, df_added_distances = \
        create_distance_matrices(df_added_coordinates, list_coordinates, sender_lon, sender_lat,distances_path_C,duration_path_C,euk_distance_path_C,matrix_table_path_C,
                                 distances_path_S, duration_path_S, euk_distance_path_S, df_distance_path, chunk_size=100)
    # Calculate Freight Cost
    df_added_freightcost = add_costs(df_added_distances, transport_preis, df_freightcost_path, column_name)
    # Shipments and weight per week per ID_recipient
    df_frequency, df_weight = evaluation_after_KW1(df_added_freightcost,df_frequency_path, df_weight_path )
    # Variability analysis
    df_var_evaluation = variability_evaluation(df_frequency, df_weight, df_added_freightcost, variability_path, variability_path_EU)
    df_assigned_pattern = pattern_assignment(df_var_evaluation, var_weight, var_frequency, min_frequency,save_path_base, save_path_special)
    df_assigned_profile = profile_application(df_added_freightcost, df_assigned_pattern)
    df_recal_freightcost= recalulate_costs(df_assigned_profile, transport_preis, column_name,new_freightcost_path)