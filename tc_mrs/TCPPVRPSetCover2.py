#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      meyer
#
# Created:     10.06.2014
# Copyright:   (c) meyer 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------


import sys
p='C:\gurobi1001\win64\python37\lib\gurobipy'

if p not in sys.path:
    sys.path.append(p)

import time

import math
import random
from gurobipy import *
from tc_mrs.VRPInstanceObjects import *

from tc_mrs.VRPInstanceObjects import *
from tc_mrs.VRPSolutionObjects import *
import pandas as pd


def mycallback(model, where):
    if where == GRB.callback.PRESOLVE:
        # Presolve callback
        print('Removed %d columns and %d rows' % \
              (model.cbGet(GRB.callback.PRE_COLDEL), \
               model.cbGet(GRB.callback.PRE_ROWDEL)))
    elif where == GRB.callback.MIPSOL:
        # MIP solution callback
        obj     = model.cbGet(GRB.callback.MIPSOL_OBJ)
        nodecnt = int(model.cbGet(GRB.callback.MIPSOL_NODCNT))
        print('*** New solution at node %g objective %g' % (nodecnt, obj))



class TCPVRPSetCover2(object):

    def __init__(self, inst, dima, setOfCols,lösungszeit):
        self.inst = inst
        self.dima = dima
        self.setOfCols = setOfCols
        self.lösungszeit = lösungszeit

        self.scSolTime = 0
        self.numVars = 0
        self.numBinVars = 0
        self.numCons = 0


    def run(self, logging = True, onlyMR = False, wah = False, gap = -1, lösungszeit = False):
        t0 = time.time()

        m = Model()

        if (gap != -1):
            m.setParam(GRB.Param.MIPGap, gap)

        ######## Switch off logging:
        if (logging == False):
            m.setParam(GRB.Param.OutputFlag, 0)
            m.setParam(GRB.Param.LogFile, "")

        ######## Defining sets and parameters for easier use in the model
        ### set of customer nodes (== supplier nodes)
        V_c = range(self.inst.setOfOrders[1].intId, self.inst.setOfOrders[-1].intId+1)
        costAF = [0]    # offset fpr the plant node
        for i in V_c:
            costAF.append(self.inst.setOfOrders[i].frequ * self.inst.setOfOrders[i].osPrice)

        ### set of vehicle types
        K = range(len(self.inst.setOfVehilceTypes))
        # corresponding cost factor for objective value
        numK = [self.inst.setOfVehilceTypes[i].num  for i in K]


        ### set of candidate columns
        R = self.setOfCols

        ### number of days
        numDays = self.inst.numDays

        ######## Generating the necessary variables
        ## z_tdk: 1 if a column t is assigned to day d to vehicle k
        ## y_i: 1 if customer i is assigned to AF network
        ## u_ir: 1 if custoner i is assigned to pattern r

        print("======= start generating variabes ========")
        y = {}
        for i in V_c:
            y[i] = m.addVar(vtype=GRB.BINARY, obj=costAF[i], name='y_%s' % (i))

        z = {}
        for t in R:  # going trough col objects
            for d in range(0,numDays):
                for k in K:
                    tourPrice = \
                            (self.inst.setOfVehilceTypes[k].pricePerKm * t.dist + \
                                self.inst.setOfVehilceTypes[k].pricePerMin * t.sos[-1]) * \
                            ( self.inst.setOfVehilceTypes[k].percCharge +1 )
                    z[t.id, d, k] = m.addVar(vtype=GRB.BINARY, obj=(tourPrice), name='z_%s_%s_%s' % (t.id, d, k))


        feas, indices, KANmultiplier = self.inst.feasPattern.getFeasiblePattern(numDays)
        u = {}
        for i in V_c:
            for r in indices[self.inst.setOfOrders[i].frequ]:   # returns the indices of the feasible patterns for certain frequency
                u[i, r] = m.addVar(vtype=GRB.BINARY, name='u_%s_%s' % (i, r))


        m.update()


        ######## Modify y variable if only milk runs are allowed if feasible
        if (onlyMR == True):
            print("======= fix y[i] to zero if feasible tour in R ========")
            for i in V_c:
                if((self.inst.setOfOrders[i].dem < self.inst.getMaxVolCap() and \
                        (self.inst.setOfOrders[i].st  + self.dima.getTime(self.inst.setOfOrders[i].intId, self.inst.setOfOrders[0].intId)) < self.inst.getMaxTimeCap())):
                    y[i].lb = 0
                    y[i].ub = 0
                else:
                    print("not fixing ", i)

        if (wah != False):
            print("======= Weight based Assignment heuristic with weight limit of %i ========" %(wah))
            for i in V_c:
                if (self.inst.setOfOrders[i].dem <= wah or self.inst.setOfOrders[i].dem > self.inst.getMaxVolCap() or \
                        (self.inst.setOfOrders[i].st  + self.dima.getTime(self.inst.setOfOrders[i].intId, self.inst.setOfOrders[0].intId)) > self.inst.getMaxTimeCap) :
                    y[i].lb = 1
                    y[i].ub = 1
                    print("fix to AF ", i, " (%i)" %(self.inst.setOfOrders[i].dem))
                else:
                    y[i].lb = 0
                    y[i].ub = 0
                    print("fix to MR ", i, " (%i)" %(self.inst.setOfOrders[i].dem))

        ######## Generating the necessary constraints
        ## (1) y_i + sum_r u_ir = 1     # either Af or assignment of pattern
        ## (2) sum_t z_tdk <= 1         # just one assignment of a tour to a
        ##                              # vehicle on a certain day
        ## (3) sum_r u_ir * feas_rd - sum_t sum_k z_tdk * a_ti <= 0
        ##                              # linking pattern decision and column choice

        print("======= start generating constraint set (1) ========")
        ## constraint (1)
        for i in V_c:
            m.addConstr( y[i] + quicksum( u[i,r] for r in indices[self.inst.setOfOrders[i].frequ] ) == 1, 'con1:_%i' % (i))

        print("======= start generating constraint set (2) ========")
        ## constraint (2)
        for d in range(0,numDays):
            for k in K:
                m.addConstr( quicksum(z[t.id, d, k] for t in R) <= numK[k], 'con2:_%i_%i' %(d, k) )

        print("======= generating AF Cols and feasible vehTypes ========")
        a = self.calcAForCols()
        vehTypes = self.calcOptVehType()

        print("======= start generating constraint set (3) ========")
        ## constraint (3)
        for i in V_c:
            for d in range(0,numDays):
                m.addConstr(    quicksum( u[i, r] * feas[r][d] for r in indices[self.inst.setOfOrders[i].frequ] ) -
                                quicksum( z[t.id, d, k] * a[t.id][i] for k in K for t in R if (a[t.id][i] == 1 and vehTypes[t.id] == k) )
                                <= 0, 'con3:_%i_%i' %(i, d) )
        print("======= call update ========")
        m.update()

#        m.write("model.lp")
        m.Params.IntFeasTol = 1e-09

        if lösungszeit != False:
            print("LIMIT GESETZT")
            m.Params.timeLimit = lösungszeit

        print("TimeLimit",  m.Params.timeLimit)

        print("======= call optimize ========")
        m.optimize()

        t1 = time.time()

        self.setLoggingInfo(m, t0, t1)
        sol = self.generateSolutionObject(m, y, z, u, V_c, R, K)

        self.printSol(m, y, z, u, V_c, costAF, R, K, indices, feas)

        df_pattern_res,df_tours_res, df_AFNodes_res = self.writeSoltoCSV(m, y, z, u, V_c, costAF, R, K, indices, feas)

        return sol, df_pattern_res, df_tours_res,df_AFNodes_res



    def calcOptVehType(self):
        vehType = []

        for t in self.setOfCols:
            for k in self.inst.setOfVehilceTypes:
                if (t.vol <= k.volCap):
                    vehType.append(k.intId)
##                    print t.id, t.vol, k.volCap, k.intId
                    break

        return vehType


    def calcAForCols(self):
        a = []

        for t in self.setOfCols:
            ahelp = [0 for i in range(0,len(self.inst.setOfOrders))] # for the plant node
            for j in t.sequ:
                if (j != 0):
                    ahelp[j] = 1

            a.append(ahelp)

        return a

    def setLoggingInfo(self, m, t0, t1):
        self.scSolTime = t1 - t0
        self.numVars = m.getAttr("numVars")
        self.numBinVars = m.getAttr("numBinVars")
        self.numCons = m.getAttr("numConstrs")


    def generateSolutionObject(self, m, y, z, u, V_c, R, K):
        sol = TCMRSSolution(self.inst, self.dima)

        sol_y = m.getAttr('x', y)
        sol_z = m.getAttr('x', z)
        sol_u = m.getAttr('x', u)

        tourId = 0
        selectedTours = {}
        for d in range(self.inst.numDays):
            tours=[]
            for t in R:
                for k in K:
                    if(sol_z[t.id, d, k] > 0):
                        newTour = Tour(self.inst, self.dima, tourId, t, k)
                        tours.append(newTour)
                        tourId += 1

            selectedTours["day%i"%d] = tours


        afNodes = []
        for i in V_c:
            if (sol_y[i] > 0):
                afNodes.append(self.inst.setOfOrders[i])

        sol.setSolution(selectedTours, afNodes, m.getAttr("ObjVal"))

        return sol

    def printSol(self, m, y, z, u, V_c, costAF, R, K, indices, feas):
        sol_y = m.getAttr('x', y)
        sol_z = m.getAttr('x', z)
        sol_u = m.getAttr('x', u)

        print("\n\n=============================================")
        print("Objective Function ", m.getAttr("ObjVal"))


        print("\n\nAF Nodes:")
        for i in V_c:
            if (sol_y[i] > 0):
                print("Supplier:\t", i, "\tcost: ", costAF[i])

        print("\n\nSelected Pattern:")
        for i in V_c:
            for r in indices[self.inst.setOfOrders[i].frequ]:
                if (sol_u[i,r] > 0):
                    print("Supplier:\t", i, "\tpattern: ", r, "\t", feas[r])


        print("\n\nSelected Tours:")
        for d in range(self.inst.numDays):
            print("Day ", d)
            for t in R:
                for k in K:
                    if(sol_z[t.id, d, k] > 0):
                        tourPrice = \
                            (self.inst.setOfVehilceTypes[k].pricePerKm * t.dist + \
                                self.inst.setOfVehilceTypes[k].pricePerMin * t.sos[-1]) * \
                            ( self.inst.setOfVehilceTypes[k].percCharge +1 )
                        AFcost = self.calcAFCosts(t.sequ)
                        print("vehicle ", k, "\ttour ", t.id, "\ttime", t.sos[-1], "\tdist", t.dist, "\tvol", t.vol, "\tcost", tourPrice, "\tsequ", t.sequ, "\tAFcost", AFcost)

    def writeSoltoCSV(self, m, y, z, u, V_c, costAF, R, K, indices, feas):
        sol_y = m.getAttr('x', y)
        sol_z = m.getAttr('x', z)
        sol_u = m.getAttr('x', u)

        intern_ID_array = []
        extern_ID_array = []
        pattern_array_mon = []
        pattern_array_tue = []
        pattern_array_wed = []
        pattern_array_thu = []
        pattern_array_fri = []

        for i in V_c:
            for r in indices[self.inst.setOfOrders[i].frequ]:
                if (sol_u[i,r] > 0):
                    print("Supplier:\t", i, "\tpattern: ", r, "\t", feas[r])
                    intern_ID_array.append(i)
                    extern_ID_array.append(self.inst.setOfOrders[i].extId)
                    pattern_array_mon.append(feas[r][0])
                    pattern_array_tue.append(feas[r][1])
                    pattern_array_wed.append(feas[r][2])
                    pattern_array_thu.append(feas[r][3])
                    pattern_array_fri.append(feas[r][4])

        data_pattern = {"InternID": intern_ID_array,
                        "ExternID": extern_ID_array,
                        "Montag": pattern_array_mon,
                        "Dienstag": pattern_array_tue,
                        "Mittwoch":pattern_array_wed,
                        "Donnerstag": pattern_array_thu,
                        "Freitag": pattern_array_fri}
        df_pattern_res = pd.DataFrame(data = data_pattern)

        MR_ID_array = []
        weekday_array = []
        vehicletype_array = []
        tourduration_array = []
        tourdistance_array = []
        tourcosts_array = []
        AFcosts_array = []
        vehiclecapacity_array = []
        sequence_array = []

        for d in range(self.inst.numDays):
            print("Day ", d)
            for t in R:
                for k in K:
                    if(sol_z[t.id, d, k] > 0):
                        tourPrice = \
                            (self.inst.setOfVehilceTypes[k].pricePerKm * t.dist + \
                                self.inst.setOfVehilceTypes[k].pricePerMin * t.sos[-1]) * \
                            ( self.inst.setOfVehilceTypes[k].percCharge +1 )
                        AFcost = self.calcAFCosts(t.sequ)
                        MR_ID_array.append(str(d)+"-"+str(t.id)+"-"+str(k))
                        weekday_array.append(d)
                        vehicletype_array.append(k)
                        tourduration_array.append(t.sos[-1])
                        tourdistance_array.append(t.dist)
                        tourcosts_array.append(tourPrice)
                        AFcosts_array.append(AFcost)
                        vehiclecapacity_array.append(self.inst.setOfVehilceTypes[k].volCap)
                        sequence_array.append(t.sequ)
        data_tours = {"MR_ID": MR_ID_array,
                      "Wochentag": weekday_array,
                      "Fahrzeugtyp": vehicletype_array,
                      "Kapazität": vehiclecapacity_array,
                      "Sequenz": sequence_array,
                      "Tourdauer":tourduration_array,
                      "Tourdistanz": tourdistance_array,
                      "Tourkosten": tourcosts_array,
                      "AF_Kosten": AFcosts_array,
                      }
        df_tours_res = pd.DataFrame(data=data_tours)

        data_AFNodes = {"InternID": [],
                        "ExternID": [],
        }
        for i in V_c:
            if (sol_y[i] > 0):
                print("Supplier:\t", i, "\tcost: ", costAF[i])
                data_AFNodes["ExternID"].append(self.inst.setOfOrders[i].extId)
                data_AFNodes["InternID"].append(i)

        df_AFNodes_res = pd.DataFrame(data=data_AFNodes)

        return df_pattern_res, df_tours_res, df_AFNodes_res

    def log(self, logFile = None):
        if (logFile == None):
            f = open("logSc.txt", 'w+')
        else:
            f = logFile

        f.write(("numVars; " + str(self.numVars) + ";\n"))
        f.write(("numBinVars; " + str(self.numBinVars) + ";\n"))
        f.write(("numCons; " + str(self.numCons) + ";\n" ))
        f.write(("scSolTime[s]; " + str(self.scSolTime) + ";\n"))

        if (logFile == None):
            f.close()

    def calcAFCosts(self, sequ):
        cost = 0
        for i in sequ:
            cost += self.inst.setOfOrders[i].osPrice

        return cost

if __name__ == "__main__":
    instfile = "Resources\\tcmilk.txt"
    inst = TCMilkInstance(instfile)
    dima = DimaProvider(inst.setOfOrders)


    # generate solution to test
    for i in inst.setOfOrders:
        print(i)

    c0 = Column(0, [0,1], [0,4], 100, 1)
    c1 = Column(1, [0,2], [0,4], 200, 1)
    c2 = Column(2, [0, 1 ,2], [0,4,5], 300, 2)
    c3 = Column(3, [0,1,2,3], [0,4,5,6], 400, 3)


    setOfCols = [c0, c1, c2, c3]


    logging = True
    mrOnly = False
    wah = False

    solve = TCPVRPSetCover2(inst, dima, setOfCols)
    solve.run(logging, mrOnly, wah)
    solve.log()


