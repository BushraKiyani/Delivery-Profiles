from tc_mrs.TCPPVRPSetCover2 import TCMilkInstance
from tc_mrs.VRPInstanceObjects import DimaProvider
from tc_mrs.GenerateAPrioriCols4 import GenerateAPRioriCols4
from tc_mrs.TCPPVRPSetCover2 import TCPVRPSetCover2
from tc_mrs.CVRPwithColumnGeneration import *
import time
import pandas as pd

def runtcpvrp(instfile,suchzeit_heu,maxAllowedStops, dimafile=None, heuristicColumn_gen = False, lösungszeit = False):
    start = time.time()

    inst = TCMilkInstance(instfile)
    dima = DimaProvider(inst.setOfOrders, dimafile)

    if heuristicColumn_gen == False:
        g = GenerateAPRioriCols4(inst, dima)#Instanz instanziiert
        g.generateCols(-1, -1)
        cols = g.cols
    else:
        suchzeit_heu = [suchzeit_heu]
        g = GenerateAPRioriCols4(inst, dima)  # Instanz instanziiert
        g.generateCols(maxAllowedStops, -1)
        zeit = time.time()
        print('Laufzeit nach Columngenerierung im exakten Model: {:5.3f}s'.format(zeit - start))
        print("")
        cols = g.cols

        cols = CVRP_Column_gernation(instfile, suchzeit_heu, dima.dima, dima.tima,cols)

    #for t in cols:
        #print(t.id, " ", t.sequ, " ", t.sos, " ", t.dist, " ", t.vol)

    logging = True
    mrOnly = True
    wah = False

    solve = TCPVRPSetCover2(inst, dima, cols,lösungszeit)#g.cols
    sol, df_pattern_res, df_tours_res, df_AFNodes_res = solve.run(logging, mrOnly, wah, gap=0.005, lösungszeit=lösungszeit)
    solve.log()

    print(df_pattern_res)

    ende = time.time()

    print("")
    print("Anzahl Columns {}".format(len(cols)))
    print('Laufzeit: {:5.3f}s'.format(ende - start))

    ### Print results
    df_pattern_res.to_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Rohergebnisse\df_patterns_"+instfile.split("\\")[-1].split(".t")[0]+ str(maxAllowedStops)+ "-"+ str(suchzeit_heu[0]) +"-"+ str(lösungszeit) +".csv",
            encoding="latin_1", sep=";", index=False)
    df_tours_res.to_csv(r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Rohergebnisse\df_tours_"+instfile.split("\\")[-1].split(".t")[0]+ str(maxAllowedStops)+ "-"+ str(suchzeit_heu[0]) +"-"+ str(lösungszeit) +".csv",
            encoding="latin_1", sep=";", index=False)
    df_AFNodes_res.to_csv(
        r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Rohergebnisse\df_AFNodes_" +
        instfile.split("\\")[-1].split(".t")[0] + str(maxAllowedStops)+ "-"+ str(suchzeit_heu[0]) +"-"+ str(lösungszeit)+ ".csv",
        encoding="latin_1", sep=";", index=False)


    print(instfile)

    return len(cols), ende - start, sol.objValue

if __name__ == "__main__":
    heuristicColumn_gen = False
    suchzeit_heu = 600
    maxAllowedStops =3
    lösungszeit = 1800

    filelist = [
        r'C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Instanzen -TK\TK_Instanz0.75-0.75-SZ20Multi1.2.txt',
    ]

    instance_name_array = []
    col_numer_array = []
    solving_times_array = []
    obj_values_array = []

    for instfile in filelist:
        print(instfile)
        print(instfile.split("\\")[-1].split(".t")[0])
        print("__________________________________NEUE INSTANZ__________________________________")

        #instfile = r'C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Instanzen -3\5b-5-3-300.txt'
        dimafile = r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Matrizen\TK_matrizen_1.33-1.33.txt"
        colnumber, solvingtime, obj_value = runtcpvrp(instfile, suchzeit_heu, maxAllowedStops, dimafile= dimafile,heuristicColumn_gen =heuristicColumn_gen, lösungszeit = lösungszeit)

        instance_name_array.append(instfile.split("\\")[-1])
        col_numer_array.append(colnumber)
        solving_times_array.append(solvingtime)
        obj_values_array.append(obj_value)

        df_solutions = pd.DataFrame(data={"Instanz": [instfile.split("\\")[-1]],
                                          "Col. Anzahl": [colnumber],
                                          "Dauer": [solvingtime],
                                          "Zielfunktionswert": [obj_value],
                                          "heuristic_Column_gen":[heuristicColumn_gen],
                                          "heuristic_Dauer": [suchzeit_heu],
                                          "vollst_max_Stops": [maxAllowedStops],
                                          "lösungszeitlimit": [lösungszeit],
                                          })
        print(df_solutions)
        df_solutions.to_csv(
            r"C:\Users\Thomas\PycharmProjects\Masterarbeit\Resources\Version_2\Milkruns\Ergebnisse\Optimierungsergebnisse\\"+ instfile.split("\\")[-1]+ "_"+str(maxAllowedStops)+"_"+ str(suchzeit_heu)+"_"+ str(lösungszeit) +".csv",
            encoding="latin_1", sep=";")




