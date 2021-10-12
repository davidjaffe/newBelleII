#!/usr/bin/env python
'''
compare two xlsx files
20211011

ref: https://stackoverflow.com/questions/37113173/compare-2-excel-files-using-python
'''
import sys
import math
import xlrd
import numpy

import datetime


class comparexlsx():
    def __init__(self,debug=0):

        self.file1 = '/Users/djaffe/Documents/Belle II/Software_Computing/ResourceEstimates/20210902_fixPB/ResourceEstimate-2021-09-02-RawDataCenterPB dj.xlsx'
        self.file2 = '/Users/djaffe/Documents/Belle II/Software_Computing/ResourceEstimates/20210902_fixPB/ResourceEstimate-2021-09-02-RawDataCenterPB.xlsx'

        self.debug = debug
        
        return
    def main(self):
        rb1 = xlrd.open_workbook(self.file1)
        rb2 = xlrd.open_workbook(self.file2)
        print 'comparexlsx Compare files\n',self.file1,'\nand\n',self.file2

        foundOne = False
        s1,s2 = rb1.nsheets,rb2.nsheets
        if self.debug > 0 : print 'comparexlsx.main # sheets',s1,s2
        if s1 != s2 : print 'comparexlsx.main DIFFERENT NUMBER OF SHEETS',s1,s2
        for isheet in range(min(s1,s2)):
        
            sheet1 = rb1.sheet_by_index(isheet)
            sheet2 = rb2.sheet_by_index(isheet)

            differ = False
            words  = ''
            n1,n2 = sheet1.nrows, sheet2.nrows
            if n1!=n2 :
                differ = True
                words = 'Different # of rows {} {}'.format(n1,n2)
            if self.debug > 0 : print 'comparexlsx.main Sheet#',isheet,'compare # rows',n1,n2
            for rownum in range(min(n1,n2)):
                r1 = sheet1.row_values(rownum)
                r2 = sheet2.row_values(rownum)

                for colnum, (c1,c2) in enumerate(zip(r1,r2)):
                    if c1 != c2:
                        differ = True
                        if self.debug > 0 : print 'Row {} Col {} : {} != {}'.format(rownum+1,colnum+1, c1, c2)

            if differ : foundOne = True
            if not differ:
                if self.debug > 0 : print 'comparexlsx.main Sheet',isheet,' identical'
            else:
                print 'comparexlsx.main SHEET',isheet,'NOT IDENTICAL',words
        if foundOne : print 'comparexlsx.main FOUND DIFFERENCES BETWEEN INPUT FILES'
        return
if __name__ == '__main__':
    debug = 0
    if len(sys.argv)>1 : debug = int(sys.argv[1])
    t = comparexlsx(debug=debug)
    t.main()
