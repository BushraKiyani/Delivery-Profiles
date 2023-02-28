# -------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      meyer
#
# Created:     10.06.2014
# Copyright:   (c) meyer 2014
# Licence:     <your licence>
# -------------------------------------------------------------------------------

import time

from tc_mrs.VRPSolutionObjects import *
from tc_mrs.TSPPermutation import *
from tc_mrs.TSPDynamicProg import *


class GenerateAPRioriCols4(object):
    def __init__(self, instance, dima):
        self.inst = instance
        self.dima = dima
        self.resMaxNumStops = 0
        self.maxNumStopsAllowed = 0
        self.upperBoundStops = 0
        self.timeLimit = 0
        self.s = []  # auxiliary variable for recursive subsetgeneration
        self.cols = []  # arrray of resulting cols

        self.genColTime = 0
        self.numCols = 0

    def generateCols(self, maxAllowedStops, timeLimit): #zulässige Touren

        self.timeLimit = timeLimit
        if (timeLimit == -1):
            timeLimit = float("inf")

        self.maxNumStopsAllowed = maxAllowedStops
        self.upperBoundStops = self.upperBoundNumOfNodes() + 1 #Maximale Anzahl Nodes pro Tour
        if (maxAllowedStops == -1):
            stopLimit = self.upperBoundStops
        else:
            stopLimit = min(self.upperBoundStops, maxAllowedStops)

        t0 = time.time()

        S = self.generateColsSize1()  # returns only the nodes, which lead to feasibel columns in terms of maxTourLength and Capacity
        print("Ready with size ", 1)
        diff = time.time() - t0
        print('Laufzeit: {:5.3f}s'.format(diff))

        self.generateDP(stopLimit, S, t0, timeLimit) #???

        t1 = time.time()

        self.genColTime = t1 - t0
        self.numCols = len(self.cols)
        self.resMaxNumStops = len(self.cols[-1].sequ) - 1

        print("================")
        print(self.resMaxNumStops)
        print(self.genColTime)
        print(self.numCols)

    ##        for c in self.cols:
    ##            print c

    def distance(self, i, j):
        if (self.dima == None):
            dx = self.inst.setOfOrders[i].x - self.inst.setOfOrders[j].x
            dy = self.inst.setOfOrders[i].y - self.inst.setOfOrders[j].y
            return math.sqrt(dx * dx + dy * dy)

        else:
            return self.dima.getDist(self.inst.setOfOrders[i].intId, self.inst.setOfOrders[j].intId)

    def time(self, i, j):
        if (self.dima == None):
            return self.distance(i, j)
        else:
            return self.dima.getTime(self.inst.setOfOrders[i].intId, self.inst.setOfOrders[j].intId)

    def generateDP(self, stopLimit, feasNodes, t0, timeLimit):
        # A: initial value - just distance from 0 to every other point + keep the track of edges
        # frozenset is the set of visits and end of chain as key of the dictionary, the distance, the sequence
        # and total volume corresponds to the value:
        # { ([0,1,4], 1) : (214, [0,4,1], 1200) } =
        # { (frozenset, ending node) : (dist, sequence, volume) }
        # based on: http://www.digitalmihailo.com/traveling-salesman-problem-dynamic-algorithm-implementation-in-python/
        A = {(frozenset([0, idx]), idx): (self.distance(0, idx), [0, idx], self.inst.setOfOrders[idx].dem) for idx in
             feasNodes}

        for m in range(2, stopLimit + 1):
            B = {}
            aall = []
            #[aall.append(j[0]) for j in A.keys() if j[0] not in aall]

            for j in A.keys():
                diff = time.time() - t0
                if (diff > timeLimit):
                    print("Time Limit for generating Cols is reached")
                    print("max number of supplier stops ", len(self.cols[-1].sequ) - 1)
                    return
                if j[0] not in aall:
                    aall.append(j[0])


            for S1 in aall:
                for i in range(max(S1) + 1, len(self.inst.setOfOrders)):
                    S = S1 | {i}
                    D = {}
                    for j in S - {0}:  # fuer alle j in S ausser 0

                        pred = [(A[(S - {j}, k)][0] + self.distance(k, j), A[(S - {j}, k)][1] + [j],
                                 A[(S - {j}, k)][2] + self.inst.setOfOrders[j].dem) for k in S if
                                k != 0 and k != j and (S - {j}, k) in A]

                        if (len(pred) > 0):
                            minCol = min(pred)
                            if (self.checkSequ(minCol[1], minCol[0], minCol[2])):
                                B[(S,
                                   j)] = minCol  # this will use 0th index of tuple for ordering, the same as if key=itemgetter(0) used
                                D[(S, j)] = minCol

                    pred2 = [(D[d][0], D[d][1], D[d][2]) for d in iter(D)]

                    if (len(pred2) > 0):
                        minCol2 = min([(D[d][0], D[d][1], D[d][2]) for d in iter(D)])
                        self.checkAndAddCol(minCol2[1], minCol2[0], minCol2[2])

                    diff = time.time() - t0
                    if (diff > timeLimit):
                        print("Time Limit for generating Cols is reached")
                        print("max number of supplier stops ", len(self.cols[-1].sequ) - 1)
                        return

            print("Ready with size ", m)
            print('Laufzeit: {:5.3f}s'.format(diff))

            A = B

    def log(self, logFile=None):
        if (logFile == None):
            f = open("logColGen.txt", 'w+')
        else:
            f = logFile

        f.write(("genColTime[s]; " + str(self.genColTime) + ";\n"))
        f.write(("timeLimit[s]; " + str(self.timeLimit) + ";\n"))
        f.write(("numCols; " + str(self.numCols) + ";\n"))
        f.write(("resMaxNumStops; " + str(self.resMaxNumStops) + ";\n"))
        f.write(("maxNumStopsAllowed; " + str(self.maxNumStopsAllowed) + ";\n"))
        f.write(("upperBoundStops; " + str(self.upperBoundStops) + ";\n"))

        if (logFile == None):
            f.close()

    def checkSequ(self, sequ, dist, vol):
        s = [i for i in reversed(sequ)]

        if (vol <= self.inst.getMaxVolCap()):
            sos = self.calcSos(s)
            if (sos[-1] <= self.inst.getMaxTimeCap()):
                return True

        return False

    def checkAndAddCol(self, sequ, dist, vol):
        s = [i for i in reversed(sequ)]

        if (vol <= self.inst.getMaxVolCap()):
            sos = self.calcSos(s)
            if (sos[-1] <= self.inst.getMaxTimeCap()):
                self.cols.append(Column(len(self.cols), s, sos, dist, vol))

    def getSumVolume(self, set):
        suml = 0
        for o in set:
            l = self.inst.setOfOrders[o].dem  # HEIJUNKA case
            suml += l
        return suml

    def upperBoundNumOfNodes(self):
        nodesSortedByDemand = sorted(self.inst.setOfOrders, key=lambda Node: Node.dem)
        load = 0
        for i in range(0, len(nodesSortedByDemand)):
            load += nodesSortedByDemand[i].dem
            if (load > self.inst.getMaxVolCap()):
                break
        return i

    def generateColsSize1(self):
        S = []

        for i in range(1, len(self.inst.setOfOrders)):
            n = self.inst.setOfOrders[i].intId
            sequ = [n, 0]

            sos = self.calcSos(sequ) #Servicezeit + Fahrtzeit der Sequenz berechnen
            cost = self.calcCost(sequ)  #Kosten der Sequenz berechnen

            if (sos[-1] > self.inst.getMaxTimeCap()): #Prüfung ob Grenzen eingehalten werden
                print("No feasible exclusive tour due to time Capacity for node id", n, self.inst.setOfOrders[i].extId)
            elif (self.inst.setOfOrders[i].dem > self.inst.getMaxVolCap()):
                print("No feasible exclusive tour due to volume Capacity for node id", n, self.inst.setOfOrders[i].extId)
            else:
                S.append(i)
                self.cols.append(Column(len(self.cols), sequ, sos, cost, self.inst.setOfOrders[i].dem))

        return S

    def calcCost(self, sequ):
        cost = 0
        for i in range(1, len(sequ)):
            cost += self.dima.getDist(sequ[i - 1], sequ[i])

        return cost

    def calcSos(self, sequ):
        sos = [self.inst.setOfOrders[sequ[0]].st] #Servicezeit
        for i in range(1, len(sequ)):
            newsos = sos[i - 1] + self.inst.setOfOrders[sequ[i]].st + self.dima.getTime(sequ[i - 1], sequ[i])
            sos.append(newsos)

        return sos


if __name__ == '__main__':
    # instfile = "C:/SVNRepositories/Diss2/AnalyseBoschData/TCMRSinst.txt"
    # instfile = "C:/SVNRepositories/Diss2/AnalyseBoschData/Instances/TCMRSinst_cv_0.9_SMALL_weight_1.txt"
    #
    # instfile = "C:/Projekte/Dissertation/AnalyseBoschDaten/Instances/TCMRSinst_cv_0.9_SMALL_weight_1.txt"

    instfile = "Resources/tcmilk.txt"
    inst = TCMilkInstance(instfile)

    ##    #dimaFile=None
    ##    #dimaFile="C:\SVNRepositories\Diss2\Porgrammiertes\PythonPVRPModule\DimaExample25.txt"
    #dimaFile = "C:/SVNRepositories/Diss2/AnalyseBoschData/Bewegungsdaten_dima.txt"

    dima = DimaProvider(inst.setOfOrders)

    g = GenerateAPRioriCols4(inst, dima)
    g.generateCols(-1, -1)
    g.log()

    for t in g.cols:
        print(t)



##    import cProfile
##    cProfile.run("g.generateCols(6, -1)")
