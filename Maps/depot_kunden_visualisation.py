import os
import pandas as pd
import folium
import webbrowser
import ast


# Maps
def load_map(m,profil_kund, depot_coord):
    folium.Marker(
    location=depot_coord,
    popup="Depot",
    #icon=folium.Icon(icon="cloud"),
    icon=folium.Icon(color='red', icon='envelope')
    ).add_to(m)
    #print(profil_kunden.head())
    for index, row in profil_kund.iterrows():
        #print(profil_kund.index)
        #Customer_id = row['']
        #print(Customer_id)
        folium.Marker(
        location=[row['lat'], row['lon']],
        #popup=f'Customer {}',
        popup='Customer:{}'.format(index),
        icon=folium.Icon(color='green', icon='home')
        ).add_to(m)

        #folium.PolyLine(locations=[coord1, coord2], color='red').add_to(m)
    return m


def create_connections(m,df_tour,profile_kunden,depot_coordinate):
    df_tour_expanded = df_tour
    wochentag_list = ['Montag','Dienstag','Mittwoch','Donnerstag','Freitag']
    group1 = folium.FeatureGroup(name=wochentag_list[0])
    group2 = folium.FeatureGroup(name=wochentag_list[1])
    group3 = folium.FeatureGroup(name=wochentag_list[2])
    group4 = folium.FeatureGroup(name=wochentag_list[3])
    group5 = folium.FeatureGroup(name=wochentag_list[4])

    for index, row in df_tour_expanded.iterrows():
        sequence = ast.literal_eval(row['Sequenz_extID'])
        l = len(sequence)-1
        coordinate_list = []
        Customer_ID = sequence[0]
        color_dict = {'9000': 'red', '12000': 'yellow', '24000': 'blue'}
        for i in range(l):

            #print(profile_kunden.loc[sequence[i]][1])
            coordinate_list.append((profile_kunden.loc[sequence[i]][0],profile_kunden.loc[sequence[i]][1]))
        coordinate_list.append(depot_coordinate)
        group = row['Kapazität']
        #print(group)
        color = color_dict[str(group)]
        MR_ID,Wochentag,Fahrzeugtyp,Kapazitaet = row['MR_ID'],row['Wochentag'],row['Fahrzeugtyp'],row['Kapazität']
        Tourdauer, Tourdistanz, Tourkosten, AF_Kosten, Sequenz_extID = row['Tourdauer'],row['Tourdistanz'],row['Tourkosten'],row['AF_Kosten'],row['Sequenz_extID']
        #can use round(variable name, upto digits) for better view
        path = folium.PolyLine(coordinate_list, color=color,
                               tooltip=f'MR_ID: {MR_ID} <br>'
                                       f'Customer ID: {Customer_ID} <br>'
                                       f'Wochentag: {wochentag_list[Wochentag]}<br>Fahrzeugtyp: {Fahrzeugtyp}<br>'
                                       f'Kapazitaet: {Kapazitaet}<br> Tourdauer:{round(Tourdauer,2)} <br>'
                                       f'Tourdistanz: {round(Tourdistanz,2)}<br> Tourkosten:{round(Tourkosten,2)}<br>'
                                       f'AF_Kosten: {round(AF_Kosten,2)}<br>Sequenz_extID: {Sequenz_extID}',
                               weight=4)
        #print(type(row['Wochentag']))
        if row['Wochentag'] == 0:
            path.add_to(group1)
        elif row['Wochentag'] == 1:
            path.add_to(group2)
            #path.add_to(group2)
        elif row['Wochentag'] == 2:
            path.add_to(group3)
            #path.add_to(group3)
        elif row['Wochentag'] == 3:
            path.add_to(group4)
            #path.add_to(group4)
        elif row['Wochentag'] == 4:
            path.add_to(group5)

        #print("end")
    m.add_child(group1)
    m.add_child(group2)
    m.add_child(group3)
    m.add_child(group4)
    m.add_child(group5)

    folium.LayerControl().add_to(m)
    return m


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    depot_coordinate = [48.136324834975376, 11.62875580190314]
    m = folium.Map(location=depot_coordinate,tiles="Stamen Terrain",zoom_start=10)
    read_profile_kunden = os.path.join(os.getcwd(), "Profilkunden_Koordinaten.csv")
    read_df_tour = os.path.join(os.getcwd(), "df_tours_Instanz1-1.33-1.33-SZ15Multi1Veh_cap13-600-1800.csv")
    write_directory = os.path.join(os.getcwd(), "map.html")

    df_tour = pd.read_csv(read_df_tour,sep=';',encoding='latin-1')
    profile_kunden = pd.read_csv(read_profile_kunden,sep=';',encoding='latin-1')
    profile_kunden.dropna(axis='columns',inplace=True)
    profile_kunden.set_index('ID_Empfänger', inplace=True)
    load_map(m,profile_kunden,depot_coordinate)
    #profile_kunden.set_index('ID_Empfänger', inplace=True)
    #print(df_tour.head())
    # loading map using depot coordinates and customer coordinates
    #load_map(m,profile_kunden,depot_coordinate)
    create_connections(m,df_tour,profile_kunden,depot_coordinate)
    m.save(write_directory)
    webbrowser.open(write_directory)

