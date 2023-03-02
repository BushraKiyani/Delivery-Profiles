import pandas as pd
import os


def write_txt(df_nodes, df_vehicles, df_instance,var_gew, var_freq, servicetime,multi,veh_cap, min_freq):
    if os.path.exists(r"../00_Resources/Instances/MR_Instance/Instanz"+str(min_freq)+"-"+str(var_gew)+"-"+str(var_freq)+"-SZ"+str(servicetime)+"Multi"+str(multi)+"Veh_cap"+str(veh_cap)+".txt"):
        os.remove(r"../00_Resources/Instances/MR_Instance/Instanz"+str(min_freq)+"-"+str(var_gew)+"-"+str(var_freq)+"-SZ"+str(servicetime)+"Multi"+str(multi)+"Veh_cap"+str(veh_cap)+".txt")

    with open(
            r"../00_Resources/Instances/MR_Instance/Instanz"+str(min_freq)+"-"+str(var_gew)+"-"+str(var_freq)+"-SZ"+str(servicetime)+"Multi"+str(multi)+"Veh_cap"+str(veh_cap)+".txt",
            'a') as the_file:
        for index, row in df_instance.iterrows():
            the_file.write("{0}\t{1}\t{2}\t{3}\n".format(row["inst_type"], row["num_veh_types"], row["num_nodes"],
                                                         row["num_days"]))

        for index, row in df_vehicles.iterrows():
            the_file.write(
                "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\n".format(int(row["veh_ID_array"]), int(row["veh_num_array"]),
                                                             int(row["veh_dist_array"]),
                                                             int(row["veh_cap_array"]), row["veh_price_per_km"],
                                                             row["veh_price_per_min"], row["veh_price_per_charge"]))

        for index, row in df_nodes.iterrows():
            if row["ID_Empfänger"] == 0:
                the_file.write(
                    "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\t{9}\t{10}\t{11}\t{12}\t{13}\n".format(index, int(row[
                        "ID_Empfänger"]), "Depot", int(0), round(row["lat"], 3), round(
                        row["lon"], 3), 0, 0, 0, 0, 20, 5, 1, 0))
            else:
                the_file.write(
                    "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\t{9}\t{10}\t{11}\t{12}\t{13}\n".format(index, int(row[
                        "ID_Empfänger"]), int(row["ID_Empfänger"]), int(0), round(row["lat"], 3), round(
                        row["lon"], 3), int(row["avg_Gewicht"]), round(servicetime, 4), int(round(row["avg_Frequenz"])),
                                                                                                0, 20, 5, 1,float(row["AF_Kosten"])))


if __name__ == '__main__':
    multi = 1.2

    var_gew = 100
    var_freq = 100
    min_freq = 0.5

    veh_cap = 1

    df_nodes = pd.read_csv(r"../00_Resources/Instances/MR_Instance_Nodes/MR_Instance_Nodes"+str(min_freq)+"_"+str(var_gew)+"_"+str(var_freq)+".csv",
                        encoding="latin_1", sep=";")
    df_nodes = df_nodes.drop(columns=["Koordinaten"])
    print(df_nodes.dtypes)
    veh_num = df_nodes.shape[0]

    servicetime = 15
    veh_ID_array = [0,1,2]
    veh_num_array = [veh_num,veh_num,veh_num]
    veh_dist_array = [9*60,9*60,9*60]
    veh_cap_array = [9000*veh_cap, 12000*veh_cap, 24000*veh_cap]

    veh_price_per_km = [0.3,0.4,0.6]
    veh_price_per_km = [round(i * multi,4) for i in veh_price_per_km]

    veh_price_per_min = [35/60, 35/60, 35/60]
    veh_price_per_min = [round(i * multi,4) for i in veh_price_per_min]

    veh_price_per_charge = [0.155, 0.155, 0.155]
    veh_price_per_charge = [round(i * 1,4) for i in veh_price_per_charge]

    df_vehicles = pd.DataFrame(data={"veh_ID_array":veh_ID_array,"veh_num_array":veh_num_array, "veh_dist_array":veh_dist_array,"veh_cap_array":veh_cap_array, "veh_price_per_km":veh_price_per_km, "veh_price_per_min":veh_price_per_min,"veh_price_per_charge":veh_price_per_charge})
    print(df_vehicles.dtypes)
    df_instance = pd.DataFrame(data={"inst_type":[3], "num_veh_types":[len(veh_ID_array)], "num_nodes": [df_nodes.shape[0]-1], "num_days": [5]})

    write_txt(df_nodes, df_vehicles, df_instance,var_gew,var_freq,servicetime,multi, veh_cap, min_freq)
    print(df_instance)