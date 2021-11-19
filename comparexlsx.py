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
    def __init__(self,debug=0,file1='/Users/djaffe/Documents/Belle II/Software_Computing/ResourceEstimates/20210902_fixPB/ResourceEstimate-2021-09-02-RawDataCenterPB dj.xlsx',file2='/Users/djaffe/Documents/Belle II/Software_Computing/ResourceEstimates/20210902_fixPB/ResourceEstimate-2021-09-02-RawDataCenterPB.xlsx'):

        self.file1 = file1
        self.file2 = file2

        self.debug = debug
        
        return
    def main(self):
        rb1 = xlrd.open_workbook(self.file1)
        sn1 = rb1.sheet_names()
        rb2 = xlrd.open_workbook(self.file2)
        sn2 = rb2.sheet_names()
        print 'comparexlsx Compare files\n',self.file1,'\nand\n',self.file2,'\n'

        foundOne = False
        s1,s2 = rb1.nsheets,rb2.nsheets
        if self.debug > 0 : print 'comparexlsx.main # sheets',s1,s2
        if s1 != s2 : print 'comparexlsx.main DIFFERENT NUMBER OF SHEETS',s1,s2
        for isheet in range(min(s1,s2)):
        
            sheet1 = rb1.sheet_by_index(isheet)
            sheet2 = rb2.sheet_by_index(isheet)

            name1  = sn1[isheet]
            name2  = sn2[isheet]
            namewords = 'name:'+name1
            if name1!=name2 : namewords = 'name1:'+name1+' name2:'+name2
            
            differ = False
            words  = ''
            n1,n2 = sheet1.nrows, sheet2.nrows
            if n1!=n2 :
                differ = True
                words = 'Different # of rows {} {}'.format(n1,n2)
            if self.debug > 0 : print 'comparexlsx.main Sheet#',isheet,namewords,'compare # rows',n1,n2
            for rownum in range(min(n1,n2)):
                r1 = sheet1.row_values(rownum)
                r2 = sheet2.row_values(rownum)

                for colnum, (c1,c2) in enumerate(zip(r1,r2)):
                    if c1 != c2:
                        differ = True
                        if self.debug > 0 :
                            colname = self.num_to_excel_col(colnum+1)
                            print '{}{} : {} != {}'.format(colname,rownum+1, c1, c2)

            if differ : foundOne = True
            if not differ:
                if self.debug > 0 : print 'comparexlsx.main Sheet',isheet,' identical'
            else:
                print 'comparexlsx.main SHEET',isheet,namewords,'NOT IDENTICAL',words
        if foundOne : print 'comparexlsx.main FOUND DIFFERENCES BETWEEN INPUT FILES'
        return
    def num_to_excel_col(self,n):
        ''' https://stackoverflow.com/questions/42176498/repeating-letters-like-excel-columns '''
        if n < 1:
            raise ValueError("Number must be positive")
        result = ""
        while True:
            if n > 26:
                n, r = divmod(n - 1, 26)
                result = chr(r + ord('A')) + result
            else:
                return chr(n + ord('A') - 1) + result


if __name__ == '__main__':
    debug = 0
    file1='/Users/djaffe/Documents/Belle II/Software_Computing/ResourceEstimates/20210902_fixPB/ResourceEstimate-2021-09-02-RawDataCenterPB dj.xlsx'
    file2='/Users/djaffe/Documents/Belle II/Software_Computing/ResourceEstimates/20210902_fixPB/ResourceEstimate-2021-09-02-RawDataCenterPB.xlsx'
    if len(sys.argv)>1 : debug = int(sys.argv[1])
    if len(sys.argv)>2 :
        file1 = sys.argv[2]
        file2 = sys.argv[3]
    t = comparexlsx(debug=debug,file1=file1,file2=file2)
    t.main()
