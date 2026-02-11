import pandas as pd
import seaborn as sns
import requests
import folium
from folium import plugins
import numpy as np
import matplotlib.pyplot as plt

colmap_kat = {"ZZZ": "red", "BLAU": "blue", "GRAU": "gray", "GELB":"yellow", "GRÜN": "green"}
colmap_kat_Marker = {"ZZZ": "red", "BLAU": "blue", "GRAU": "lightgray", "GELB":"orange", "GRÜN": "green"}
colmap = {"Rotenburg (Wümme)": "red"}
list_kat= ["ZZZ", "BLAU", "GRAU", "GELB", "GRÜN"]

def visualize_routes_map(df_map_tours, path_map_routes):
    min_lat = df_map_tours['empfaenger_lat'].min()
    min_long = df_map_tours['empfaenger_lon'].min()
    max_lat = df_map_tours['empfaenger_lat'].max()
    max_long = df_map_tours['empfaenger_lon'].max()

    bound_box = [(min_lat, min_long), (max_lat, max_long)]

    map_tours = folium.Map()
    map_tours.fit_bounds(bound_box)


    depos = df_map_tours["Stadt_Absender"].unique()

    for depo in depos:
        group_depot = folium.FeatureGroup(name=depo)
        df_map_tours_filtered = df_map_tours[df_map_tours["Stadt_Absender"] == depo]
        df_map_tours_filtered_grouped = df_map_tours_filtered.groupby('Transport')

        for index, group in df_map_tours_filtered_grouped:
            stationen_array = []
            cor_absender = [group.iloc[0, -4], group.iloc[0, -5]]
            stationen_array.append(cor_absender)

            line = group_depot.add_child(folium.Marker(location=cor_absender,
                                                       color=colmap[depo],
                                                       icon=folium.Icon(icon='truck', prefix='fa', color=colmap[depo]),
                                                       tooltip="Depot: " + depo))

            for index, row in group.iterrows():
                cor_empfänger = [row["empfaenger_lon"], row["empfaenger_lat"]]
                stationen_array.append(cor_empfänger)

            tooltip_values = group["Recipient_City"].values
            tooltip = ", ".join(tooltip_values)

            body = {"coordinates": stationen_array}
            headers = {
                'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
                'Authorization': '5b3ce3597851110001cf6248033cc8f1b7c245168f99842d15f1fa05',
                'Content-Type': 'application/json; charset=utf-8'
            }

            call = requests.post('https://api.openrouteservice.org/v2/directions/driving-hgv/geojson', json=body,
                                 headers=headers)
            response_dict = call.json()
            print(response_dict)
            route = response_dict["features"][0]["geometry"]["coordinates"]

            new_route_array = []

            for i in route:
                cor = [i[1], i[0]]
                new_route_array.append(cor)

            line = group_depot.add_child(
                folium.PolyLine(new_route_array, color=colmap[depo], tooltip=tooltip, overlay=True))

        map_tours.add_child(group_depot)

    folium.LayerControl().add_to(map_tours)
    map_tours.save(path_map_routes)
    print("Routenkarte fertig.")
    return map_tours

def visualize_locations(df_map_tours, path_map_location):
    df_touren = df_map_tours

    min_lat = df_touren['empfaenger_lat'].min()
    min_long = df_touren['empfaenger_lon'].min()
    max_lat = df_touren['empfaenger_lat'].max()
    max_long = df_touren['empfaenger_lon'].max()

    bound_box = [(min_lat, min_long), (max_lat, max_long)]  # be careful, the depot nodes are not considered!

    map_locations = folium.Map()
    map_locations.fit_bounds(bound_box)


    depos = df_touren["Stadt_Absender"].unique()

    for depo in depos:
        group = folium.FeatureGroup(name=depo)
        df_touren_filtered = df_touren[df_touren["Stadt_Absender"] == depo]

        for index, row in df_touren_filtered.iterrows():
            depot_node = (row['versandzentrum_lat'], row['versandzentrum_lon'])
            line = group.add_child(folium.Marker(location=depot_node,
                                                 color=colmap[row["Stadt_Absender"]],
                                                 icon=folium.Icon(icon='truck', prefix='fa',
                                                                  color=colmap[row["Stadt_Absender"]]),
                                                 tooltip="Depot: " + row["Stadt_Absender"]))
            line = group.add_child(folium.Circle(location= depot_node,
                                                 color='red',
                                                 radius=300,
                                                 fill= True
                                                 ))
            client_depot = row['Stadt_Absender']
            client_node = (row['empfaenger_lat'], row['empfaenger_lon'])
            line = group.add_child(folium.CircleMarker(location=client_node,
                                                       radius=3,
                                                       color=colmap[client_depot],
                                                       tooltip="Recipient: " + str(row["Recipient_ID"]) + ", Depot: " + row[
                                                           "Stadt_Absender"]))
        map_locations.add_child(group)
    map_locations.add_child(folium.LayerControl())
    map_locations.save(path_map_location)
    print("Locationkarte fertig.")
    return map_locations

def add_koordinates_to_df(df_Recipientn, df_koordianten):
    df_koordianten = df_koordianten.set_index("Recipient_ID")
    lat_array= []
    lon_array= []
    name_array = []
    straße_array = []
    PLZ_array =[]
    for index, row in df_Recipientn.iterrows():
        lat_array.append(df_koordianten.loc[row["Recipient_ID"],"lat"])
        lon_array.append(df_koordianten.loc[row["Recipient_ID"],"lon"])
        name_array.append(df_koordianten.loc[row["Recipient_ID"],"Name_Empfänger"])
        straße_array.append(df_koordianten.loc[row["Recipient_ID"],"Recipient_Street"])
        PLZ_array.append(df_koordianten.loc[row["Recipient_ID"], "Recipient_Postal_Code"])

    df_Recipientn["lat"] = lat_array
    df_Recipientn["lon"] = lon_array
    df_Recipientn["Name_Empfänger"] = name_array
    df_Recipientn["Recipient_Street"] = straße_array
    df_Recipientn["Recipient_Postal_Code"] = PLZ_array
    return df_Recipientn

def visualize_frequency_weight(df_map_tours, path_map_location):

    min_lat = df_map_tours['lat'].min()
    min_long = df_map_tours['lon'].min()
    max_lat = df_map_tours['lat'].max()
    max_long = df_map_tours['lon'].max()

    bound_box = [(min_lat, min_long), (max_lat, max_long)]  # be careful, the depot nodes are not considered!

    map_locations = folium.Map()
    folium.TileLayer('stamentoner').add_to(map_locations)
    folium.TileLayer('Stamen Toner').add_to(map_locations)
    folium.TileLayer('cartodbpositron').add_to(map_locations)
    #folium.TileLayer().add_to(map_locations)
    map_locations.fit_bounds(bound_box)

    layers = ["avg_Shipments_pro_Woche", "avg_Freight_Cost_pro_Sendung", "avg_Weight_pro_Sendung"]

    depot_node = (53.123745, 9.3437254)
    line = map_locations.add_child(folium.Marker(location=depot_node,
                                         color="black",
                                         icon=folium.Icon(icon='truck', prefix='fa',
                                                          color="black"),
                                         tooltip="Depot: Rotenburg (Wümme)"))

    kreis = folium.FeatureGroup(name="Gebiet", show=False)
    kreis.add_child(folium.Circle(
        radius=300000,
        location=depot_node,
        popup="Versorgungsgebiet",
        color="crimson",
        fill=True,
        fill_opacity=0.1,
    ))
    map_locations.add_child(kreis)



    for layer in layers:

        group = folium.FeatureGroup(name=layer, show= False)
        map_locations.add_child(group)

        max_value = df_map_tours[layer].max()
        min_value = df_map_tours[layer].min()


        for kat in list_kat:
            df_map_tours_filtered = df_map_tours[df_map_tours["Kategorisierung"] == kat]
            kategorie = plugins.FeatureGroupSubGroup(group, name=kat +": "+ layer, show= False)

            for index, row in df_map_tours_filtered.iterrows():

                radius = ((row[layer]*20 -min_value)/(max_value-min_value))
                client_node = (row['lat'], row['lon'])
                line = kategorie.add_child(folium.CircleMarker(location=client_node,
                                                               radius=radius,
                                                               color=colmap_kat[row["Kategorisierung"]],
                                                               fill = True,
                                                               fill_color = colmap_kat[row["Kategorisierung"]],
                                                               fill_opacity=0.7,
                                                               tooltip= "Recipient_ID: {} <br> Name Empfänger: {} <br> Straße Empfänger: {} <br> PLZ Empfänger: {} <br> {}: {:.2f} <br> GesamtfrachtWeight: {} <br> GesamtFreight_Cost: {} <br> Sendungsanzahl: {} <br>".format(row["Recipient_ID"], str(row["Name_Empfänger"]),row["Recipient_Street"], row["Recipient_Postal_Code"], layer, row[layer], row["Weight"],row["Freight_Cost"],row["Shipments"])
                                                               )
                                           )

            map_locations.add_child(kategorie)


    layer = "Empfänger_Circle"
    group = folium.FeatureGroup(name="Empfänger_Circle", show=False)
    map_locations.add_child(group)
    df_map_tours_frequent = df_map_tours[df_map_tours["avg_Shipments_pro_Woche"]>=1]

    for kat in list_kat:
        df_map_tours_filtered = df_map_tours_frequent[df_map_tours["Kategorisierung"] == kat]
        kategorie = plugins.FeatureGroupSubGroup(group, name=kat + ": " + layer, show=False)

        for index, row in df_map_tours_filtered.iterrows():
            client_node = (row['lat'], row['lon'])
            line = kategorie.add_child(folium.CircleMarker(location=client_node,
                                                               radius=3,
                                                               color=colmap_kat[row["Kategorisierung"]],
                                                               fill = True,
                                                               fill_color = colmap_kat[row["Kategorisierung"]],
                                                               fill_opacity=0.7,
                                                           tooltip="Recipient_ID: {} <br> Name Empfänger: {} <br> Straße Empfänger: {} <br> PLZ Empfänger: {} <br> GesamtfrachtWeight: {} <br> GesamtFreight_Cost: {} <br> Sendungsanzahl: {} <br>".format(
                                                               row["Recipient_ID"],
                                                               str(row["Name_Empfänger"]),
                                                               row["Recipient_Street"],
                                                               row["Recipient_Postal_Code"],
                                                               row["Weight"],
                                                               row["Freight_Cost"],
                                                               row["Shipments"])
                                                           )
                                       )

        map_locations.add_child(kategorie)

    layer = "Empfänger_Marker"
    group = folium.FeatureGroup(name="Empfänger_Marker", show=False)
    map_locations.add_child(group)
    df_map_tours_frequent = df_map_tours[df_map_tours["avg_Shipments_pro_Woche"] >= 1]

    for kat in list_kat:
        df_map_tours_filtered = df_map_tours_frequent[df_map_tours["Kategorisierung"] == kat]
        kategorie = plugins.FeatureGroupSubGroup(group, name=kat + ": " + layer, show=False)

        for index, row in df_map_tours_filtered.iterrows():
            client_node = (row['lat'], row['lon'])
            line = kategorie.add_child(folium.Marker(location=client_node,
                                                     icon=folium.Icon(color=colmap_kat_Marker[row["Kategorisierung"]],
                                                                      prefix='fa', icon_color="black",
                                                                      icon="industry"),
                                                     tooltip="Recipient_ID: {} <br> Name Empfänger: {} <br> Straße Empfänger: {} <br> PLZ Empfänger: {} <br> GesamtfrachtWeight: {} <br> GesamtFreight_Cost: {} <br> Sendungsanzahl: {} <br>".format(
                                                         row["Recipient_ID"],
                                                         str(row["Name_Empfänger"]),
                                                         row["Recipient_Street"],
                                                         row["Recipient_Postal_Code"],
                                                         row["Weight"],
                                                         row["Freight_Cost"],
                                                         row["Shipments"])
                                                     )
                                       )

        map_locations.add_child(kategorie)




    plugins.Fullscreen(
        position="topright",
        title="Expand me",
        title_cancel="Exit me",
        force_separate_button=True,
    ).add_to(map_locations)

    plugins.LocateControl(auto_start=False ).add_to(map_locations)

    map_locations.add_child(folium.LayerControl())
    map_locations.save(path_map_location)
    print("Locationkarte fertig.")
    return map_locations

if __name__ == "__main__":
    version = "\Version_2"
    path_map_location = r'C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources'+ version+ '\Maps\map_locations.html'
    path_map_routes = r'C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Maps\map_touren_depo.html'

    df_Recipientn = pd.read_csv(r'C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources'+ version+ '\Diagramme\DiagrammData\df_AuswertungNachRecipientn.csv', encoding="latin_1", sep=";")
    df_koordinaten = pd.read_csv(r'C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources'+ version+ '\ID_liste.csv', encoding="latin_1", sep=";")
    df_Recipientn = add_koordinates_to_df( df_Recipientn,df_koordinaten)
    visualize_frequency_weight(df_Recipientn, path_map_location)
    #map_touren_depo = visualize_routes_map(df_touren, path_map_routes)
    #print(df_Recipientn.head())

    map_locations = visualize_locations(df_Recipientn, path_map_location)
