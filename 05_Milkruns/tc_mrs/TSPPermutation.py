#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      meyer
#
# Created:     24.06.2014
# Copyright:   (c) meyer 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sys

import math

import itertools

from tc_mrs.VRPInstanceObjects import *

class TSPPermutation(object):

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
        # here we assume, that the first node is the destination
        n = [i for i in range(1,len(self.nodes))]

        mindist = sys.maxint
        minSequ = []
        for perm in itertools.permutations(n):
            dist = 0
            for p in range(1, len(perm)):
                dist += self.distance(perm[p-1],perm[p])
            dist += self.distance(perm[-1], 0)
            if (dist < mindist):
                mindist = dist
                minSequ = perm

##            print perm
##            print dist
##            s = [i for i in perm]
##            s.append(0)
##            time = self.getTime(s)
##            print time, time/60

        sequ =[]
        for i in minSequ:
            sequ.append(self.nodes[i].intId)

        sequ.append(self.nodes[0].intId)

        return sequ, mindist


##    def getTime(self, sequ):
##        time = 0
##        for r in range(1, len(sequ)):
##            time += self.time(sequ[r-1], sequ[r])
##        return time

if __name__ == '__main__':

    import random

    instfile = "C:/SVNRepositories/Diss2/AnalyseBoschData/Instances/TCMRSinst_cv_0.3_BIG_weight_1.txt"
    #instfile = "C:/SVNRepositories/Diss2/AnalyseBoschData/TCMRSinst_small.txt"
    inst = TCMilkInstance(instfile)

    #dimaFile=None
    #dimaFile="C:\SVNRepositories\Diss2\Porgrammiertes\PythonPVRPModule\DimaExample25.txt"
    dimaFile="C:/SVNRepositories/Diss2/AnalyseBoschData/Bewegungsdaten_dima.txt"


    dima = DimaProvider(inst.setOfOrders, dimaFile)

    sol = TSPPermutation(inst.setOfOrders, dima)
    res, dist = sol.run()

    time = 0
    for r in range(1, len(res)):
        time += dima.getTime(inst.setOfOrders[res[r-1]].intId, inst.setOfOrders[res[r]].intId)

    print("TSPPErmutation")
    print(dist)
##    print time, time/60
    print(res)

    sequ = res
    sos=[0 + inst.setOfOrders[sequ[0]].st]
    for i in range(1,len(sequ)):
        newsos = sos[i-1]+ inst.setOfOrders[sequ[i-1]].st + dima.getTime(sequ[i-1], sequ[i])
        sos.append(newsos)

    print(sos)


##    import cProfile
##    cProfile.run("sol.run()")
