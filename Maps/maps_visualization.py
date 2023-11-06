import folium
from config import *



def maps(list_coordinates, df_assigned_clustered_pattern ):

    selected_df = list_coordinates[list_coordinates['Empfänger_id'].isin(df_assigned_clustered_pattern['ID_Empfänger'])].copy()
    # Create a map centered at a certain location (adjust coordinates)
    map_center = [selected_df['latitude'].mean(),
                  selected_df['longitude'].mean()]  # Give original Coordinates, not radians
    m = folium.Map(location=map_center, zoom_start=10)

    # Create a dictionary to store Empfänger_id for each cluster
    cluster_empfanger = {cluster: [] for cluster in range(num_clusters)}
    # Add markers to the map with different colors for each cluster
    for _, row in selected_df.iterrows():
        cluster = int(row['Cluster'])  # Convert to integer
        empfanger_id = int(row['Empfänger_id'])  # Convert Empfänger_id to an integer
        cluster_empfanger[cluster].append(empfanger_id)  # Store Empfänger_id in the cluster dictionary
        # Look up the Pattern_clear value from df_ergebnisse1 based on Empfänger_id and cluster
        pattern_clear = \
        df_assigned_clustered_pattern.loc[(df_assigned_clustered_pattern['ID_Empfänger'] == empfanger_id) & (df_assigned_clustered_pattern['Cluster'] == cluster)][
            'Pattern_clear'].values[0]
        folium.CircleMarker(
            location=(row['latitude'], row['longitude']),
            radius=5,
            color=cluster_colors[cluster],
            fill=True,
            fill_color=cluster_colors[cluster],
            # Add a Popup to display Empfänger_id, cluster, and Pattern_clear
            popup=f'Empfänger_id: {empfanger_id}, Cluster: {cluster}, Profile: {pattern_clear}'
        ).add_to(m)

    # Print Empfänger_id in each cluster
    for cluster, empfangers in cluster_empfanger.items():
        print(f'Cluster {cluster}: Empfänger_ids {empfangers}')

    # Add a marker for the sender's location with a different color and size
    folium.CircleMarker(
        location=(sender_lat, sender_lon),
        radius=10,  # Adjust the size as needed
        color='blue',  # Change to your preferred color
        fill=True,
        fill_color='blue',
        popup='Sender Location'  # Popup message for sender location
    ).add_to(m)

    # Save the map as an HTML file or display it in a Jupyter notebook
    m.save(f'cluster_map_only_filterd'+ save_path_special +'.html')

