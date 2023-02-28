#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      meyer
#
# Created:     30.06.2014
# Copyright:   (c) meyer 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

class StringUtils(object):

    def concatWithSemic(self, sequ):
        s = ""
        for i in sequ:
            s += (str(i) + "; ")

        return s

    def concatWithSemicolon(self, listToLog, s):
        if (isinstance(listToLog[0], list)):
            return self.concatWithSemicolon(listToLog[0], s)
        else:
            s += (str(listToLog[0]) + ';')
            listToLog = listToLog[1:]

            if (listToLog):
                return self.concatWithSemicolon(listToLog, s)
            else:
                return s

    def concatWithSemicolon2(self, listToLog, s):
        if (isinstance(listToLog[0], list)):
            self.concatWithSemicolon2(listToLog[0],s)
            if (len(listToLog)>1):
                self.concatWithSemicolon2(listToLog[1:],s)

        else:
            s += (str(listToLog[0]))

            if (listToLog[1:]):
                self.concatWithSemicolon2(listToLog[1:], s)
            else:
                print(s)



if __name__ == '__main__':

    strUtils = StringUtils()
    l = [1,2, [4,5,['kk',0.777,"hello Welt"]],[0.99998]]

    print(strUtils.concatWithSemicolon2(l, ""))




