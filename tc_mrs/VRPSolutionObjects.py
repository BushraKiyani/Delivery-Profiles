# -------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      meyer
#
# Created:     17.06.2014
# Copyright:   (c) meyer 2014
# Licence:     <your licence>
# -------------------------------------------------------------------------------


from tc_mrs.VRPInstanceObjects import *
from tc_mrs.StringUtils import *


class Column(object):
    def __init__(self, _id, _sequ, _sos, _dist, _vol):
        self.id = _id
        self.sequ = _sequ
        self.sos = _sos
        self.dist = _dist  # in km!!!!
        self.vol = _vol

    def __str__(self):
        s = ' '.join(str(s) for s in self.sequ)
        s2 = ' '.join(str(s) for s in self.sos)
        return "id: %i \tdist: %i \tdur: %i \tvol: %f \tsequ: %s \tsos: %s" % (self.id, self.dist, self.sos[-1], self.vol, s, s2)

    def toJson(self, inst):
        col = 'var t%i={"id" : %i, "dist" : %f, "dur" : %f, "vol" : %f, "nodes" : ' % (
        self.id, self.id, self.dist, self.sos[-1], self.vol)
        for i in range(len(self.sequ)):
            order = inst.setOfOrders[self.sequ[i]]
            if (i == 0):
                col += ('[p' + str(order.intId) + ", ")
            elif (i == len(self.sequ) - 1):
                col += ('p' + str(order.intId) + ']}')
            else:
                col += ('p' + str(order.intId) + ", p" + str(order.intId) + ", ")

        return col


class Tour(Column):
    def __init__(self, inst, dima, tourId, col, vehTypeId):
        Column.__init__(self, col.id, col.sequ, col.sos, col.dist, col.vol)
        self.inst = inst
        self.tourId = tourId
        self.vehTypeId = vehTypeId
        self.tourCost = (self.inst.setOfVehilceTypes[vehTypeId].pricePerKm * col.dist + \
                         self.inst.setOfVehilceTypes[vehTypeId].pricePerMin * col.sos[-1]) * \
                        (self.inst.setOfVehilceTypes[vehTypeId].percCharge + 1)
        self.volUtil = float(col.vol) / float(self.inst.setOfVehilceTypes[self.vehTypeId].volCap)
        self.timeUtil = float(col.sos[-1]) / float(self.inst.setOfVehilceTypes[self.vehTypeId].timeCap)
        self.costPerKm = float(self.tourCost) / float(col.dist)
        self.costPerH = (float(self.tourCost) / float(col.sos[-1])) * 60.0
        self.afAltCost = sum([self.inst.setOfOrders[i].osPrice for i in self.sequ])

    def toJson(self):
        tour = 'var t%i={"id" : %i, "colId" : %i, "dist" : %.2f, "cost" : %.2f, "dur" : %.2f, "timeUtil" : %.2f, "vol" : %f, "volUtil" : %.2f, "vehType" : %i, "costKm" : %.2f, "costH" : %.2f, "altAfCost" : %.2f, "nodes" : ' \
               % (self.tourId, self.tourId, self.id, self.dist, self.tourCost, self.sos[-1], self.timeUtil, self.vol,
                  self.volUtil, self.vehTypeId, self.costPerKm, self.costPerH, self.afAltCost)
        for i in range(len(self.sequ)):
            order = self.inst.setOfOrders[self.sequ[i]]
            if (i == 0):
                tour += ('[p' + str(order.intId) + ", ")
            elif (i == len(self.sequ) - 1):
                tour += ('p' + str(order.intId) + ']}')
            else:
                tour += ('p' + str(order.intId) + ", p" + str(order.intId) + ", ")
        tour += ";\n"
        return tour

    def logHeader(self):
        s = "tourId; vehTypeId;time;dist;vol;cost;timeUtil;volUtil;afAltCost;costPerH;costPerKm;sequIntId;sequExtId;\n"
        return s

    def log(self):
        su = StringUtils()
        sequExtId = []
        for i in self.sequ:
            sequExtId.append(self.inst.setOfOrders[i].extId)

        toLog = [self.tourId, self.vehTypeId, self.sos[-1], self.dist, self.vol, self.tourCost, self.timeUtil,
                 self.volUtil, self.afAltCost, self.costPerH, self.costPerKm, self.sequ, sequExtId]
        return su.concatWithSemic(toLog)


class TCMilkNodeStats(object):
    def __init__(self, inst, dima, intOrderId, vehTypes):
        self.inst = inst
        self.dima = dima
        self.order = self.inst.setOfOrders[intOrderId]
        self.dist = self.dima.getDist(self.order.intId, 0)
        self.time = self.dima.getTime(self.order.intId, 0) + self.order.st + self.inst.setOfOrders[0].st

        self.exclMrPrices = []
        self.ps = []

        self.vehTypes = vehTypes

        for v in self.inst.setOfVehilceTypes:

            if (self.inst.setOfOrders[intOrderId].dem < v.volCap and self.time < v.timeCap):
                emrp = (float(self.dist) * v.pricePerKm + float(self.time) * v.pricePerMin) * (v.percCharge + 1)
                self.exclMrPrices.append(emrp)
                self.ps.append(self.order.osPrice / emrp)
            else:
                self.exclMrPrices.append(-1)
                self.ps.append(0)

    def logHeader(self):
        s = "intId; extId; extName; extPLZ; frequ; dem; afPrice; dist; time;"
        for i in range(0, len(self.inst.setOfVehilceTypes)):
            s += "exclMrPrices(veh%i); " % (i)
        for i in range(0, len(self.inst.setOfVehilceTypes)):
            s += "p(veh%i); " % i
        for i in range(0, len(self.inst.setOfVehilceTypes)):
            s += "veh%i; " % i
        s += "af;\n"
        return s

    def log(self):
        su = StringUtils()
        order = self.order
        toLog = [order.intId, order.extId, order.extName, order.extPLZ, order.frequ,
                 order.dem, order.osPrice, self.dist, self.time]

        vehTyp = [0 for i in range(0, len(self.inst.setOfVehilceTypes))]
        for i in self.vehTypes:
            vehTyp[i] = 1

        if (sum(vehTyp) == 0):
            vehTyp.append(1)
        else:
            vehTyp.append(0)

        logs = su.concatWithSemic(toLog) + su.concatWithSemic(self.exclMrPrices) + \
               su.concatWithSemic(self.ps) + su.concatWithSemic(vehTyp)

        return logs


class TCMRSSolution(object):
    def __init__(self, inst, dima):
        self.inst = inst
        self.dima = dima

        self.dictOfMilkRuns = []  # objects of array are of type column
        self.setOfAfNodes = []  # objects of array are of type TCMilkNode

        self.mrLocs = []
        self.afLocs = []

        self.objValue = 0

        self.dictSolStats = {}

    def setSolution(self, dictOfMilkRuns, setOfAfNodes, objValue):
        self.dictOfMilkRuns = dictOfMilkRuns
        self.setOfAfNodes = setOfAfNodes
        self.objValue = objValue

        ts = []
        for d in dictOfMilkRuns.keys():
            [ts.extend(t.sequ) for t in self.dictOfMilkRuns[d]]  # concat all tours
        [self.mrLocs.append(i) for i in ts if not i in self.mrLocs]  # delete duplicates

        for order in self.inst.setOfOrders:
            if (order.intId not in self.mrLocs):
                self.afLocs.append(order.intId)

        self.checkSol()

        self.orderStats = []

        self.calcOrderStats()

    def checkSol(self):
        print("TODO evtl. Zielfunktion pruefen")
        print("TODO evtl. Zeitfenster pruefen")
        print("TODO hier muss geprueft werden, ob alle Nodes aus inst in der Loesung auftauchen")

    def log(self, logFile=None):
        if (logFile == None):
            f = open("logSol.txt", 'w+')
        else:
            f = logFile

        self.calcSolStats()
        self.logSolStats(f)

        f.write(self.orderStats[0].logHeader())
        for o in self.orderStats:
            f.write(o.log() + '\n')

        c = 0
        for d in sorted(self.dictOfMilkRuns.keys()):
            for t in self.dictOfMilkRuns[d]:
                if (c == 0):
                    f.write("day; " + t.logHeader())
                c += 1
                s = d + '; ' + t.log() + '\n'
                f.write(s)

        if (logFile == None):
            f.close()

    def calcSolStats(self):
        numAfOrders = len(self.afLocs)
        numMrOrders = len(self.mrLocs)

        self.dictSolStats['numAfOrders'] = numAfOrders
        self.dictSolStats['numMrOrders'] = numMrOrders

        self.dictSolStats['numAfOrdersPerc'] = float(numAfOrders) / float(numAfOrders + numMrOrders)
        self.dictSolStats['numMrOrdersPerc'] = float(numMrOrders) / float(numAfOrders + numMrOrders)

        afVol = 0
        for i in self.afLocs:
            afVol += (self.inst.setOfOrders[i].dem * self.inst.setOfOrders[i].frequ)

        mrVol = 0
        for i in self.mrLocs:
            mrVol += (self.inst.setOfOrders[i].dem * self.inst.setOfOrders[i].frequ)

        pMr = [max(self.orderStats[i - 1].ps) for i in self.mrLocs if i != 0]
        pAf = [max(self.orderStats[i - 1].ps) for i in self.afLocs if i != 0]

        if (len(pMr) > 0):
            self.dictSolStats['avgMrP'] = float(sum(pMr)) / float(len(pMr))
            self.dictSolStats['maxMrP'] = max(pMr)
        else:
            self.dictSolStats['avgMrP'] = 0
            self.dictSolStats['maxMrP'] = 0
        if (len(pAf) > 0):
            self.dictSolStats['avgAfP'] = float(sum(pAf)) / float(len(pAf))
        else:
            self.dictSolStats['avgAfP'] = 0

        p = pMr + pAf
        self.dictSolStats['avgP'] = float(sum(p)) / float(len(p))
        self.dictSolStats['maxP'] = max(p)

        self.dictSolStats['afVol'] = afVol
        self.dictSolStats['mrVol'] = mrVol
        self.dictSolStats['totVol'] = afVol + mrVol

        self.dictSolStats['afVolPerc'] = float(afVol) / float(afVol + mrVol)
        self.dictSolStats['mrVolPerc'] = float(mrVol) / float(afVol + mrVol)

        numAfStops = 0
        afCost = 0
        for i in self.afLocs:
            order = self.inst.setOfOrders[i]
            afCost += (order.osPrice * order.frequ)
            numAfStops += order.frequ

        self.dictSolStats['afCost'] = afCost
        self.dictSolStats['numAfStops'] = numAfStops

        numMrStops = 0
        altMrAfCost = 0
        for i in self.mrLocs:
            order = self.inst.setOfOrders[i]
            numMrStops += order.frequ
            altMrAfCost += (order.osPrice * order.frequ)

        self.dictSolStats['numMrStops'] = numMrStops
        self.dictSolStats['altMrAfCost'] = altMrAfCost

        self.dictSolStats['numMrStopsPerc'] = float(numMrStops) / float(numMrStops + numAfStops)
        self.dictSolStats['numAfStopsPerc'] = float(numAfStops) / float(numMrStops + numAfStops)

        mrCost = 0
        sumMrVolUtil = 0
        sumMrTimeUtil = 0
        numOfTours = 0
        for d in self.dictOfMilkRuns.keys():
            for t in self.dictOfMilkRuns[d]:
                numOfTours += 1
                mrCost += t.tourCost
                sumMrTimeUtil += t.timeUtil
                sumMrVolUtil += t.volUtil

        self.dictSolStats['mrCost'] = mrCost
        self.dictSolStats['totCost'] = mrCost + afCost
        self.dictSolStats['numOfTours'] = numOfTours

        if (numOfTours > 0):
            self.dictSolStats['avgMrVolUtil'] = sumMrVolUtil / float(numOfTours)
            self.dictSolStats['avgMrTimeUtil'] = sumMrTimeUtil / float(numOfTours)
        else:
            self.dictSolStats['avgMrVolUtil'] = 0
            self.dictSolStats['avgMrTimeUtil'] = 0

        self.dictSolStats['mrCostPerc'] = float(mrCost) / float(mrCost + afCost)
        self.dictSolStats['afCostPerc'] = float(afCost) / float(mrCost + afCost)

        pureAfSolCost = altMrAfCost + afCost

        self.dictSolStats['pureAfSolCost'] = pureAfSolCost

        totalDiff = pureAfSolCost - (afCost + mrCost)
        diffPerc = float(totalDiff) / float(afCost + mrCost)

        self.dictSolStats['totalDiff'] = pureAfSolCost - (afCost + mrCost)
        self.dictSolStats['diffPerc'] = diffPerc

    def logSolStats(self, file):
        toLog = ['numOfTours', 'numMrOrders', 'numAfOrders', 'numMrOrdersPerc',
                 'numAfOrdersPerc', 'numMrStops', 'numAfStops', 'numMrStopsPerc',
                 'numAfStopsPerc', 'totCost', 'mrCost', 'afCost', 'mrCostPerc', 'afCostPerc',
                 'altMrAfCost', 'pureAfSolCost', 'totalDiff', 'diffPerc',
                 'avgMrTimeUtil', 'avgMrVolUtil', 'afVol', 'afVolPerc',
                 'mrVol', 'mrVolPerc', 'totVol', 'avgP', 'maxP', 'avgMrP', 'avgAfP'
                 ]

        for k in toLog:
            self.writeLogLine(file, k)

    def writeLogLine(self, file, key):
        s = (str(key) + "; " + str(self.dictSolStats[key]) + '\n')
        file.write(s)

    def calcOrderStats(self):
        for o in range(1, len(self.inst.setOfOrders)):
            self.orderStats.append(TCMilkNodeStats(self.inst, self.dima, o, self.getVehicleId(o)))

    def getVehicleId(self, orderIntId):
        if (orderIntId in self.afLocs):
            return []
        vehIds = []
        for d in self.dictOfMilkRuns.keys():
            for t in self.dictOfMilkRuns[d]:
                if (orderIntId in t.sequ):
                    vehIds.append(t.vehTypeId)
        vehIds.sort()
        ret = [vehIds[0]]
        for i in range(1, len(vehIds)):
            if (vehIds[i] != ret[-1]):
                ret.append(vehIds[i])

        return ret

    def toJson(self):
        return self.createString()

    def createString(self):
        vars = self.createLocVars()
        mrLocs = self.createMRLocs()
        afLocs = self.createAFLocs()

        mRTours = self.createMrTours()

        lines = self.createMrLines()

        linesDays = self.createLayersOfLines()

        vehInfo = self.createVehicleInfo()

        s = " ".join([vars, mrLocs, afLocs, mRTours, lines, linesDays, vehInfo]) + "\n"
        return s

    def createVehicleInfo(self):
        s = "\nvar vehicles=["

        for v in self.inst.setOfVehilceTypes:
            s += v.toJson() + ", "

        s = s[:-2]
        s += "];\n"
        return s

    def createLayersOfLines(self):
        linesDays = "\nvar layersDays=["
        for d in sorted(self.dictOfMilkRuns.keys()):
            linesDays += ("{ 'name' : " + "'" + str(d) + "'" + ", 'lines' : lines_" + d + "}, ")

        linesDays = linesDays[:-2]
        linesDays += "];\n"
        return linesDays

    def createMrLines(self):
        lines = ""
        for d in self.dictOfMilkRuns.keys():
            lines += ("var lines_" + d + "=[")
            for j in range(0, len(self.dictOfMilkRuns[d])):
                sol = self.dictOfMilkRuns[d][j]
                if (j != len(self.dictOfMilkRuns[d]) - 1):
                    lines += ('t%i, ' % sol.tourId)
                else:
                    lines += ('t%i];\n' % sol.tourId)

            if (len(self.dictOfMilkRuns[d]) == 0):
                lines += '];\n'
        return lines

    def createMrTours(self):
        allMFTours = []
        toursAllDays = []
        for d in self.dictOfMilkRuns.keys():
            for t in self.dictOfMilkRuns[d]:
                if (t not in toursAllDays):
                    toursAllDays.append(t)
                    allMFTours.append(t.toJson())

        mRTours = " ".join(allMFTours) + "\n"
        return mRTours

    def createLocVars(self):
        variables = "\n\n"
        for order in self.inst.setOfOrders:
            v = 'var p' + str(order.intId) + '=' + order.toJson() + '; \n'
            variables += v
        return variables

    def createMRLocs(self):
        tourStops2 = self.mrLocs
        locs = "\n\nvar locationsMR=["
        for i in range(0, len(tourStops2)):
            order = self.inst.setOfOrders[tourStops2[i]]
            locs += ('p' + str(order.intId))
            if (i == len(tourStops2) - 1):
                locs += ('];\n')
            else:
                locs += (', ')

        if (len(tourStops2) == 0):
            locs += '];\n'

        return locs

    def createAFLocs(self):
        tourStops2 = self.afLocs
        locs = "\n\nvar locationsAF=["
        for i in range(0, len(tourStops2)):
            order = self.inst.setOfOrders[tourStops2[i]]
            locs += ('p' + str(order.intId))
            if (i == len(tourStops2) - 1):
                locs += ('];\n')
            else:
                locs += (', ')

        if (len(tourStops2) == 0):
            locs += '];\n'

        return locs

    def createHtmlSolutionFile(self, toFile="C:/SVNRepositories/LogVizCheckOut/trunk/widget/src/bosch_map_widget5.html"):
        content = self.readHtmlPartsAndJoinWithStrings()
        text_file = open(toFile, "w")
        text_file.write(content)
        text_file.close()

    def readHtmlPartsAndJoinWithStrings(self):
        first = "C:/SVNRepositories/LogVizCheckOut/trunk/widget/src/part1.txt"
        sec = "C:/SVNRepositories/LogVizCheckOut/trunk/widget/src/part2.txt"
        with open(first) as openfileobject:
            contFirst = openfileobject.read()

        with open(sec) as openfileobject:
            contSec = openfileobject.read()

        s = self.createString()

        contFirst += s
        contFirst += contSec

        return contFirst


if __name__ == '__main__':

    instfile = "C:/SVNRepositories/Diss2/AnalyseBoschData/TCMRSinst_small.txt"
    inst = TCMilkInstance(instfile)

    dimaFile = "C:/SVNRepositories/Diss2/AnalyseBoschData/Bewegungsdaten_dima.txt"

    dima = DimaProvider(inst.setOfOrders, dimaFile)
    tcsol = TCMRSSolution(inst, dima)

    # generate solution to test
    for i in inst.setOfOrders:
        print(i)

    c1 = Column(0, [0, 1, 3], [0, 4, 500], 100, 18000)
    c2 = Column(1, [0, 2], [0, 4, 500], 100, 18000)
    c3 = Column(2, [0, 2], [0, 500], 100, 18000)

    t1 = Tour(inst, dima, 0, c1, 0)
    t2 = Tour(inst, dima, 1, c2, 1)
    t3 = Tour(inst, dima, 2, c3, 0)

    dictOfTours = {"day1": [t3], "day2": [t1, t2]}

    setOfAforders = []
    for i in range(5, len(inst.setOfOrders)):
        setOfAforders.append(inst.setOfOrders[i])

    tcsol.setSolution(dictOfTours, setOfAforders, 20)
    tcsol.log()

    # tcsol.createHtmlSolutionFile()

    # print(t1.toJson())
