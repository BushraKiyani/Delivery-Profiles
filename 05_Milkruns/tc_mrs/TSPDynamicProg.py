#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      meyer
#
# Created:     04.07.2014
# Copyright:   (c) meyer 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import math
import itertools

from tc_mrs.VRPInstanceObjects import *

class TSPDynamicProg(object):

    def __init__(self, nodes, dimaprovider=None):
        if (isinstance(nodes[0], Node)):
            self.n = len(nodes)
            self.nodes = nodes
            self.dima = dimaprovider
        else:
            print("Nodes is of wrong type")
            exit(1)


    # Euclidean distance between two points
    def distance(self, i, j):
        if(self.dima == None):
            dx = self.nodes[i].x - self.nodes[j].x
            dy = self.nodes[i].y - self.nodes[j].y
            return math.sqrt(dx*dx + dy*dy)

        else:
            return self.dima.getDist(self.nodes[i].intId,self.nodes[j].intId)

    def time(self, i, j):
        if(self.dima == None):
            return self.distance(i,j)
        else:
            return self.dima.getTime(self.nodes[i].intId,self.nodes[j].intId)

    def run(self):
        # initial value - just distance from 0 to every other point + keep the track of edges
        # frozenset is the set of visits and end of chain as key of the dictionary, the distance and the sequence
        # corresponds to the value
        A = {(frozenset([0, idx+1]), idx+1): (self.distance(0,idx+1), [0,idx+1]) for idx in range(0, len(self.nodes)-1)}
        cnt = len(self.nodes)

        for m in range(2, cnt):
            B = {}
            # itertools.combinations(iterable , size): generiert alle subsets von iterable mit groesse size
            # | vertcial bar ist ein union wenn es im Zusammenhang mit sets verwendet wird
            # es werden also alle subsets von range(1, cnt) gebildet und {0} hinzugefuegt
            for S in [frozenset(C) | {0} for C in itertools.combinations(range(1, cnt), m)]:
                for j in S - {0}: # fuer alle j in S ausser 0
                    B[(S, j)] = min( [(A[(S-{j},k)][0] + self.distance(k, j), A[(S-{j},k)][1] + [j]) for k in S if k != 0 and k!=j])  #this will use 0th index of tuple for ordering, the same as if key=itemgetter(0) used

            A = B

        res = min([(A[d][0], A[d][1]) for d in iter(A)])

        sequ =[]
        for i in reversed(res[1]):
            sequ.append(self.nodes[i].intId)

        return sequ, res[0]




if __name__ == '__main__':

    import random

    instfile = "C:/SVNRepositories/Diss2/AnalyseBoschData/Instances/TCMRSinst_cv_0.3_BIG_weight_1.txt"
    #instfile = "C:/SVNRepositories/Diss2/AnalyseBoschData/TCMRSinst_small.txt"
    inst = TCMilkInstance(instfile)

    #dimaFile=None
    #dimaFile="C:\SVNRepositories\Diss2\Porgrammiertes\PythonPVRPModule\DimaExample25.txt"
    dimaFile="C:/SVNRepositories/Diss2/AnalyseBoschData/Bewegungsdaten_dima.txt"


    dima = DimaProvider(inst.setOfOrders, dimaFile)

    sol = TSPDynamicProg(inst.setOfOrders, dima)
    res, dist  = sol.run()

    print("TSPDynamicProg")
    print(res)
    print(dist)

    time = 0
    for r in range(1, len(res)):
        time += dima.getTime(inst.setOfOrders[res[r-1]].intId, inst.setOfOrders[res[r]].intId)

    print("optimal")
    print(dist)
    print(time, time/60)
    print(res)


    sequ = res

    sos=[0 + inst.setOfOrders[sequ[0]].st]
    for i in range(1,len(sequ)):
        newsos = sos[i-1]+ inst.setOfOrders[sequ[i-1]].st + dima.getTime(sequ[i-1], sequ[i])
        sos.append(newsos)

    print(sequ)
    print(sos)

##    import cProfile
##    cProfile.run("sol.run()")
