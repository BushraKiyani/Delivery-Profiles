# -------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      meyer
#
# Created:     28.05.2014
# Copyright:   (c) meyer 2014
# Licence:     <your licence>
# -------------------------------------------------------------------------------


import math


class Node(object):
    def __init__(self, intId, _extId, _x, _y, _st, _dem):
        self.x = _x
        self.y = _y
        self.intId = intId
        self.st = _st
        self.dem = _dem
        self.extId = _extId

    def toJson(self):
        return '{"locations_name" : "%i", "coord" : {"lat" : %f, "lon" : %f }}' % (self.extId, self.y, self.x)

    def __str__(self):
        return "id: %i \textId: %i \tx: %f \ty: %f \tdem: %f" % (self.intId, self.extId, self.x, self.y, self.dem)


class PVRPNode(Node):
    def __init__(self, intId, _extId, _x, _y, _st, _dem, _frequ):
        Node.__init__(self, intId, _extId, _x, _y, _st, _dem)
        self.frequ = _frequ


class PVRPTWNode(PVRPNode):
    def __init__(self, intId, _extId, _x, _y, _st, _dem, _frequ, _early, _late):
        PVRPNode.__init__(self, intId, _extId, _x, _y, _st, _dem, _frequ)
        self.early = _early
        self.late = _late
        return '{"locations_name" : "%i", "coord" : {"lat" : %f, "lon" : %f }, "frequ" : %i, "int_id" : %i, "dem" : %i, "twEarly" : %i, "twLate" : %i}' \
               % (self.extId, self.y, self.x, self.frequ, self.intId, self.dem, self.early, self.late)

class MRSNode(PVRPTWNode):
    def __init__(self, intId, _extId, _x, _y, _st, _dem, _frequ, _early, _late, _L):
        PVRPTWNode.__init__(self, intId, _extId, _x, _y, _st, _dem, _frequ, _early, _late)
        self.l = _L

    def toJson(self):
        return '{"locations_name" : "%i", "coord" : {"lat" : %f, "lon" : %f }, "frequ" : %i, "int_id" : %i, "dem" : %i, "l" : %i, "twEarly" : %i, "twLate" : %i}' \
               % (self.extId, self.y, self.x, self.frequ, self.intId, self.dem, self.l, self.early, self.late)

class TCMRSNode(PVRPTWNode):
    def __init__(self, intId, extId, x, y, st, dem, frequ, early, late, L, extName, extPLZ, osPrice, pat):
        PVRPTWNode.__init__(self, intId, extId, x, y, st, dem, frequ, early, late)
        self.l = L
        self.extPLZ = extPLZ
        self.extName = extName
        self.osPrice = osPrice
        self.pat = pat

    def toJson(self):
        return '{"locations_name" : "%i", "coord" : {"lat" : %f, "lon" : %f }, "frequ" : %i, "ext_name" : "%s","extPlz" :%s , "dem" : %i, "osPrice" : %.2f}' \
               % (self.extId, self.y, self.x, self.frequ, self.extName, self.extPLZ, self.dem, self.osPrice)


class DimaProvider(object):
    def __init__(self, _setOfNodes, _dimaFile=None):

        self.dimaFile = _dimaFile
        self.nodes = _setOfNodes

        self.dima = [[0.0 for i in range(len(self.nodes))] for j in range(len(self.nodes))] #leere arrays
        self.tima = [[0.0 for i in range(len(self.nodes))] for j in range(len(self.nodes))]

        if (self.nodes[0].x == None and self.dimaFile == None):
            print("Either coords for Euk or dimaFile necessary")
            exit(1)

        if (self.dimaFile != None): #Distanzmatrix verfügbar
            self.readDimaFile()
        else: #keine Distanzmatrix
            self.generateEukDimaAndTima()


    def getDist(self, i, j):
        return self.dima[i][j]

    def getTime(self, i, j):
        return self.tima[i][j]

    def generateEukDimaAndTima(self):
        for i in self.nodes:
            for j in self.nodes:
                dx = float(self.nodes[i.intId].x) - float(self.nodes[j.intId].x)
                dy = float(self.nodes[i.intId].y) - float(self.nodes[j.intId].y)
                self.dima[i.intId][j.intId] = math.sqrt(dx * dx + dy * dy)
                self.tima[i.intId][j.intId] = math.sqrt(dx * dx + dy * dy)

    def readDimaFile(self):
        print("Read Dima File")

        minId, maxId = self.getMinMaxExtId() #höchste und geringste ID um passendes array zu erstellen
        print(minId)
        print(maxId)
        rawDima, rawTima = self.generateRawDimaAndTima(minId, maxId) #rohMatrix erstellen
        self.setDimaAndTima(rawDima, rawTima) #Matrixeinheiten ändern und syncronisieren

    def getMinMaxExtId(self):
        fromId = []
        toId = []
        with open(self.dimaFile) as openfileobject:
            c = 0
            for line in openfileobject:
                if (c < 2):  # erst zwei Zeilen enthalten Header
                    c += 1
                else:
                    l = line.split(';')
                    fromId.append(int(l[0]))
                    toId.append(int(l[1]))

        minId = min(min(fromId), min(toId))
        maxId = max(max(fromId), max(toId))

        return minId, maxId

    def generateRawDimaAndTima(self, minId, maxId):
        rawDima = [[0.0 for i in range(maxId + minId+1)] for j in range(maxId + minId+1)]
        rawTima = [[0.0 for i in range(maxId + minId+1)] for j in range(maxId + minId+1)]

        print(len(rawTima))

        with open(self.dimaFile) as openfileobject:
            c = 0
            for line in openfileobject:
                if (c < 1):  # erst zwei Zeilen enthalten Header
                    c += 1
                else:
                    l = line.split(';')
                    rawDima[int(l[0])][int(l[1])] = float(l[2])
                    rawTima[int(l[0])][int(l[1])] = float(l[3])

        return rawDima, rawTima

    def setDimaAndTima(self, rawDima, rawTima):
        for i in self.nodes:
            for j in self.nodes:
                self.dima[i.intId][j.intId] = rawDima[i.extId][j.extId] #round(,0)/ 1000 in km und stunden
                self.tima[i.intId][j.intId] = rawTima[i.extId][j.extId] #round(,0)/ 60

        # ACHTUNG Hier mache ich die Dima und Tima Symmetrisch!!
        for i in range(len(self.dima)):
            for j in range(i + 1, len(self.dima)):
                self.dima[j][i] = self.dima[i][j]
                self.tima[j][i] = self.tima[i][j]

        print("dima")
        for d in self.dima:
            print(d)

        print("tima")
        for t in self.tima:
            print(t)



class MRSInstance(object):
    def __init__(self, instfile):
        self.file = instfile

        self.numOrders = 0
        self.numVeh = 0
        self.numDays = 0

        self.timeCap = 0
        self.volCap = 0

        self.setOfOrders = []
        self.numSupplierVisits = 0

        self.feasPattern = PVRPPattern()

        self.readInstFile()
        self.setNumOfSupplierVisits()

    def getMaxVolCap(self):
        return self.volCap

    def getMaxTimeCap(self):
        return self.timeCap

    def readInstFile(self):
        print("Read Inst File")
        with open(self.file) as openfileobject:
            c = 0
            currId = 0
            for line in openfileobject:
                l = line.split()
                if (c == 0):
                    instType = int(l[0])
                    self.numVeh = int(l[1])
                    self.numOrders = int(l[2])
                    self.numDays = int(l[3])

                    c += 1
                elif (c <= self.numDays):
                    self.volCap = int(l[1])
                    self.timeCap = int(l[0])
                    c += 1
                else:
                    id = int(l[0])
                    x = float(l[1])
                    y = float(l[2])
                    st = float(l[3])
                    dem = int(l[4])
                    f = int(l[5])
                    early = int(l[-3])
                    late = int(l[-2])
                    L = int(l[-1])
                    self.setOfOrders.append(MRSNode(currId, id, x, y, st, dem, f, early, late, L))
                    currId += 1

    def setNumOfSupplierVisits(self):
        for o in self.setOfOrders:
            self.numSupplierVisits += o.frequ

    def toJson(self):
        s1 = '"instanceType" : "MRS", "numDays" : %i, "numOrders" : %i, "numVeh" : %i, "orders" : [' \
            %(self.numDays, self.numOrders, self.numVeh)

        s2 = ', '.join(s.toJson() for s in self.setOfOrders) + '], '

        s3 = '"pattern" : ' + self.feasPattern.toJson(self.numDays)

        return '{' + s1 + s2 + s3 + '}'

class ApplyRoundingToMRSInstanceAndDima(object):

    def __init__(self, mrsInstance, dima, roundingFactor):
        self.i = mrsInstance
        self.d = dima
        self.r = roundingFactor

        self.applyRounding()

    def applyRounding(self):
        self.i.timeCap = int(self.i.timeCap * self.r + 0.5)

        for o in self.i.setOfOrders:
            o.early = int(o.early * self.r + 0.5)
            o.late = int(o.late * self.r + 0.5)
            if o.l != -1:
                o.l = int(o.l * self.r + 0.5)
            o.st = int(o.st * self.r + 0.5)

        for i in range(0, len(self.d.dima)):
            for j in range(0, len(self.d.dima)):
                self.d.dima[i][j] = int(self.d.dima[i][j] * self.r + 0.5)
                self.d.tima[i][j] = int(self.d.tima[i][j] * self.r + 0.5)

class Vehicle(object):
    def __init__(self, _id, _extId, _num, _volCap, _timeCap, _pricePerKm, _pricePerMinute, _percCharge):
        self.intId = _id
        self.extId = _extId
        self.num = _num
        self.volCap = _volCap
        self.timeCap = _timeCap
        self.pricePerKm = _pricePerKm
        self.pricePerMin = _pricePerMinute
        self.percCharge = _percCharge

    def __str__(self):
        s = "id: %i \textId: %i \tnum: %i \tvolCap: %f \ttimeCap: %f" % (
            self.intId, self.extId, self.num, self.volCap, self.timeCap)
        return s

    def toJson(self):
        return '{"intId" : %i, "extId" : %i, "volCap" : %i, "timeCap" : %i, "pricePerKm" : %f, "pricePerH" : %f, "percCharge" : %f, "num" : %i }' \
               % (self.intId, self.extId, self.volCap, self.timeCap, self.pricePerKm, (self.pricePerMin * 60),
                  self.percCharge, self.num)


class TCMilkInstance(object):
    def __init__(self, instfile): #Eine Durchlaufinsanz mit Fahrzeugtypenliste und Bestellungsliste
        self.file = instfile

        self.instType = 0

        self.numOrders = 0
        self.numVehTypes = 0
        self.numDays = 0

        self.timeCap = 0
        self.volCap = 0

        self.maxVolCap = 0
        self.maxTimeCap = 0

        self.setOfVehilceTypes = []
        self.setOfOrders = []

        self.feasPattern = PVRPPattern()

        self.readInstFile()
        self.setupMaxCap() #Grenzen auf Fahrzeugmaxima setzen

    def setupMaxCap(self):
        for i in self.setOfVehilceTypes:
            if (i.volCap > self.maxVolCap): self.maxVolCap = i.volCap
            if (i.timeCap > self.maxTimeCap): self.maxTimeCap = i.timeCap

        print("maxVol", self.maxVolCap)
        print("maxTime", self.maxTimeCap)

    def getMaxVolCap(self):
        return self.maxVolCap

    def getMaxTimeCap(self):
        return self.maxTimeCap

    def getKmCostOfVeh(self, typeId):
        return self.setOfVehilceTypes[typeId].pricePerKm

    def getMinCostOfVeh(self, typeId):
        return self.setOfVehilceTypes[typeId].pricePerMin

    def readInstFile(self):
        print("Read instfile")
        with open(self.file) as openfileobject:
            c = 0
            currId = 0
            for line in openfileobject:
                l = line.split("\t")
                print(l)
                if (c == 0): #Allgemeine Infos
                    self.instType = int(l[0])
                    self.numOrders = int(l[2])
                    self.numDays = int(l[3])
                    self.numVehTypes = int(l[1])

                    c += 1
                elif (c <= self.numVehTypes): #Fahrzeugtypenliste erstellen
                    self.setOfVehilceTypes.append(
                        Vehicle(c - 1, int(l[0]), int(l[1]), int(l[3]), int(l[2]), float(l[4]), float(l[5]),
                                float(l[6])))
                    #print("l1", int(l[2]))
                    c += 1
                else: #Kundenliste erstellen
                    intId = int(l[0])
                    extId = int(l[1])
                    extName = l[2]
                    extPlz = l[3]
                    x = float(l[4])
                    y = float(l[5])
                    dem = int(l[6]) #Nachfrage
                    st = float(l[7]) #Serviczeit
                    frequ = int(l[8]) #Bestellungen pro Woche
                    early = int(l[9])
                    late = int(l[10])
                    L = int(l[11]) #maximum arrival time difference - unwichtig
                    pat = int(l[12]) #Zulässige pattern??
                    osPrice = float(l[13]) #Kosten pro Lieferung
                    self.setOfOrders.append(
                        TCMRSNode(intId, extId, x, y, st, dem, frequ, early, late, L, extName, extPlz, osPrice, pat))

                    currId += 1


class PVRPPattern(object):
    def getFeasiblePattern(self, numDays):
        """

        :rtype: feas, indices, multiplierKANBAN
        """
        if (numDays == 2):
            feas = [[1, 0], [0, 1], [1, 1]]
            indices = {1: [0, 1], 2: [2]} #indices?
            multiplierKANBAN = [[2, 0], [0, 2], [1, 1]]#multiplerKanban?
            return feas, indices, multiplierKANBAN

        elif (numDays == 3):
            feas = [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [0, 1, 1], [1, 0, 1], [1, 1, 1]]
            indices = {1: [0, 1, 2], 2: [3, 4, 5], 3: [6]}
            multiplierKANBAN = [[3, 0, 0], [0, 3, 0], [0, 0, 3], [2, 1, 0], [0, 2, 1], [1, 0, 2], [1, 1, 1]]
            return feas, indices, multiplierKANBAN

        elif (numDays == 4):
            feas = [
                [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1],
                [1, 0, 1, 0], [0, 1, 0, 1],
                [1, 1, 1, 0], [1, 1, 0, 1], [1, 0, 1, 1], [0, 1, 1, 1],
                [1, 1, 1, 1]
            ]
            indices = {1: [0, 1, 2, 3], 2: [4, 5], 3: [6, 7, 8, 9], 4: [10]}
            multiplierKANBAN = [
                [4, 0, 0, 0], [0, 4, 0, 0], [0, 0, 4, 0], [0, 0, 0, 4],
                [2, 0, 2, 0], [0, 2, 0, 2],
                [2, 1, 1, 0], [1, 1, 0, 2], [1, 0, 2, 1], [0, 2, 1, 1],
                [1, 1, 1, 1]
            ]
            return feas, indices, multiplierKANBAN

        elif (numDays == 5):
            feas = [
                [1, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 1, 0], [0, 0, 0, 0, 1],
                [1, 0, 1, 0, 0], [0, 1, 0, 1, 0], [0, 0, 1, 0, 1], [1, 0, 0, 1, 0], [0, 1, 0, 0, 1],
                [0, 1, 0, 1, 1], [1, 0, 1, 0, 1], [1, 1, 0, 1, 0], [0, 1, 1, 0, 1], [1, 0, 1, 1, 0],
                [0, 1, 1, 1, 1], [1, 0, 1, 1, 1], [1, 1, 0, 1, 1], [1, 1, 1, 0, 1], [1, 1, 1, 1, 0],
                [1, 1, 1, 1, 1]
            ]
            indices = {1: [0, 1, 2, 3, 4], 2: [5, 6, 7, 8, 9], 3: [10, 11, 12, 13, 14], 4: [15, 16, 17, 18, 19],
                       5: [20]}
            multiplierKANBAN = [
                [5, 0, 0, 0, 0], [0, 5, 0, 0, 0], [0, 0, 5, 0, 0], [0, 0, 0, 5, 0], [0, 0, 0, 0, 5],
                [3, 0, 2, 0, 0], [0, 3, 0, 2, 0], [0, 0, 3, 0, 2], [2, 0, 0, 3, 0], [0, 2, 0, 0, 3],
                [0, 2, 0, 2, 1], [1, 0, 2, 0, 2], [2, 1, 0, 2, 0], [0, 2, 1, 0, 2], [2, 0, 2, 1, 0],
                [0, 1, 1, 1, 2], [1, 0, 2, 1, 1], [1, 1, 0, 2, 1], [1, 1, 1, 0, 2], [2, 1, 1, 1, 0],
                [1, 1, 1, 1, 1]
            ]
            return feas, indices, multiplierKANBAN

    def getDaysOfPat(self, numDays, index):
        f, i, m = self.getFeasiblePattern(numDays)
        pat = f[index]
        days = [] # days starting with 0
        for i, p in enumerate(pat):
            if p == 1:
                days.append(i)
        return days

    def toJson(self, numDays):
        feas, index, multi = self.getFeasiblePattern(numDays)
        a = []
        for d in range(0, numDays):
            for i in index[d+1]:
                pat = self.getDaysOfPat(numDays, i)
                p = ', '.join(str(i) for i in pat)
                s = '{ "id" : %i, "freq" : %i, "pat" : [%s]}' %(i, len(pat), p)
                a.append(s)
            s2 = ", ".join(i for i in a)
        return "[" + s2 + "]"


if __name__ == "__main__":

    pat = PVRPPattern()
    print(pat.getDaysOfPat(5, 2))

    print(pat.toJson(5))

    instfile = "Resources\MilkCordExample3.vrp"
    inst = MRSInstance(instfile)

    print(inst.toJson())
    print(inst.setOfOrders[2].toJson())

    instfile = "Resources\\tcmilk.txt"
    inst = TCMilkInstance(instfile)

    print("=========")

    # instfile = "C:/SVNRepositories/Diss2/AnalyseBoschData/TCMRSinst.txt"
    # inst = TCMilkInstance(instfile)
    #
    # veh = Vehicle(1, 1, 10, 20000, 840, 1.2, 1.7, 0.15)
    # print(veh)
    # print(veh.toJson())
    #
    # print(inst.setOfOrders[1].toJson())

    # dimaFile=None
    # dimaFile = "DimaExample25.txt"
    # #dimaFile = "C:/SVNRepositories/Diss2/AnalyseBoschData/Bewegungsdaten_dima.txt"
    #
    # dima = DimaProvider(inst.setOfOrders, dimaFile)
    # print(dima.getDist(0, 3))
    # print(dima.getTime(0, 3))
    #
    # print(inst.setOfOrders[0].toJson())
    #
    # data = inst.setOfOrders[0].toJson()
    #
    # import json
    #
    # print(json.dumps(data, indent=4, separators=(',', ': ')))
