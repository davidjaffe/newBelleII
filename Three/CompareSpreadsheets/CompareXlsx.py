#!/usr/bin/env python
'''
compare one sheet in two xlsx files, using pandas
20221223

ref: https://stackoverflow.com/questions/37113173/compare-2-excel-files-using-python

'''
import sys
import math
import xlrd
import numpy
import pandas as pd
import copy

import datetime


class CompareXlsx():
    def __init__(self,debug=0,file1='/Users/djaffe/Documents/Belle II/Software_Computing/ResourceEstimates/20210902_fixPB/ResourceEstimate-2021-09-02-RawDataCenterPB dj.xlsx',file2='/Users/djaffe/Documents/Belle II/Software_Computing/ResourceEstimates/20210902_fixPB/ResourceEstimate-2021-09-02-RawDataCenterPB.xlsx',sheet='Budget Model'):

        self.debug = debug

        self.file1 = file1
        self.file2 = file2
        self.sheet = sheet

        self.LimitingRowsAllowedColumns = "A,B"
        self.LimitingRowLabels = ['DirectCosts', 'IndirectCosts', 'Labor', 'OverheadRates']
        self.LimitingRows = { 'DirectCosts' :  [ ['DESCRIPTION', None] , ['TOTAL DIRECT COSTS', None] ],
                              'IndirectCosts': [ ['Electric Distributed (Electric Power Burden)', None] , ['TOTAL PROGRAM COSTS', None] ],
                              'Labor':         [ ['Band', None] , ['TECH4', None] ],
                              'OverheadRates': [ ['Overhead Rates', None] , ['Desired contingency rate', None] ]
                                  }
        self.favColumns ={'FY'+str(fy):[] for fy in range(22,27+1)}
        if self.debug > 1 : print('CompareXlsx.__init__ self.favColumns',self.favColumns)
        self.rowForColHeaders = 1
        
            

        
        return
    def findFavColumns(self,XLfile):
        '''
        return column labels corresponding to favorite column headers in row self.rowForColHeaders in input excle file XLfile
        '''
        DS = pd.read_excel(XLfile,sheet_name=self.sheet)
        print('CompareXlxs.findFavColumns Input file',XLfile)
        irow = self.rowForColHeaders
        
        favColumns = copy.deepcopy( self.favColumns) 

        for icol in range(len(DS.columns)):
            word = DS.iloc[irow,icol]
            if type(word) is str:
                if word in favColumns:
                    favColumns[word].append(icol)
                    if self.debug > 1 : print(icol,word,favColumns[word])
                    
        print('CommpareXlxs.findFavColumns favColumns',favColumns)
        if self.debug > 0 : 
            for key in favColumns:
                print('CompareXlxs.findFavColumns key',key,': ',end='')
                for icol in favColumns[key]: print(DS.iloc[irow,icol],',',end='')
                print()
            
        return favColumns
    def findLimitingRows(self,XLfile):
        '''
        return upper and lower limiting rows in sheet self.sheet of excel file XLfile using pandas, restricting
        search to self.LimitingRowsAllowedColumns.

        also return names of rows from the upper to lower limit (inclusive)

        exit with error if limiting row cannot be found
        '''
        DS = pd.read_excel(XLfile,sheet_name=self.sheet,usecols=self.LimitingRowsAllowedColumns)
        print('CompareXlsx.findLimitingRows Input file',XLfile)

        RowNames = {}
        LimitingRows = copy.deepcopy( self.LimitingRows )
        Failed = False
        
        for label in self.LimitingRowLabels:
            RowNames[label] = {}
            topRowKeyword,topRow = LimitingRows[label][0]
            botRowKeyword,botRow = LimitingRows[label][1]
            for icol,colName in enumerate(DS.columns):
                if self.debug > 2 : print('icol',icol,'colName',colName,'len(DS[colName])',len(DS[colName]))
                for i,cell in enumerate(DS[colName]):
                    if self.debug > 2 : print('icol',icol,'irow',i,'cell',cell,'topRowKeyword,topRow',topRowKeyword,topRow)
                    if topRow is None:
                        if topRowKeyword in str(cell): topRow = i
                    if botRow is None:
                        if botRowKeyword in str(cell): botRow = i
                        if self.debug > 1 : print('icol',icol,botRowKeyword,'row',i,'cell',cell,'str(cell)',str(cell),'botRow',botRow)
            LimitingRows[label][0][1] = topRow
            LimitingRows[label][1][1] = botRow
            if topRow is None or botRow is None : Failed = True
            print('CompareXlsx.findLimitingRows Limits for RowLabel',label,topRowKeyword,topRow,botRowKeyword,botRow)
            
        if Failed :
            print('CompareXlsx.findLimitingRows LimitingRows',LimitingRows)
            sys.exit('CompareXlsx.findLimitingRows ERROR Failed to find some or all KEYWORDS')

        for label in RowNames:
            i1,i2 = LimitingRows[label][0][1],LimitingRows[label][1][1]+1
            for irow in range(i1,i2):
                name = ''
                for icol,colName in enumerate(DS.columns):
                    cell = DS.iloc[irow,icol]
                    if cell==cell : # avoid nans
                        name += str(cell) + ' '
                if len(name)>0 : RowNames[label][irow] = name
                
            if self.debug > 1 : print('CompareXlsx.findLimitingRows label',label,'RowNames',RowNames[label])
            
        return LimitingRows, RowNames
    def compare(self,decks,LABEL=None):


        File, favColumns, LimitingRows, RowNames, Frame = [],[],[],[],[]
        for deck in decks:
            File.append(deck[0])
            Frame.append( pd.read_excel(deck[0],sheet_name=self.sheet) )
            favColumns.append(deck[1])
            LimitingRows.append(deck[2])
            RowNames.append(deck[3])

        Labels = [x for x in self.LimitingRowLabels]
        if LABEL is not None:
            if LABEL not in self.LimitingRowLabels : sys.exit('CompareXlsx.compare ERROR INPUT LABEL ' + LABEL)
            Labels = [LABEL]
        colNames = list(set(favColumns[0].keys())&set(favColumns[1].keys()))  # common column names only

        print('CompareXlsx.compare \nCompare files',File[0],File[1])
        
        for label in Labels:
            print('\n',label)
            NoProblem = True
            for colName in colNames:
                header  = 'Column header ' + colName
                for icol1,icol2 in zip(favColumns[0][colName],favColumns[1][colName]):
                    for irow1,irow2 in zip(RowNames[0][label],RowNames[1][label]):
                        name1 = RowNames[0][label][irow1]
                        name2 = RowNames[1][label][irow2]
                        value1 = Frame[0].iloc[irow1,icol1]
                        value2 = Frame[1].iloc[irow2,icol2]
                        OK, words = self.reportComparison(name1,value1,name2,value2,comparison='float')
                        if not OK :
                            NoProblem = False
                            if header is not None: print(header)
                            header = None
                            print(words)
            if NoProblem : print('No problems found for',label)

        

        return
    def reportComparison(self,name1,value1,name2,value2,comparison='float',tolerance=1.):
        '''
        Inputs:
        name1,name2 are strings
        value1, value2 are ints, floats or strings
        comparison can be 'float' or 'str'
        tolerance is explained below

        REPORT issued if value1 != value2 or if name1!=name2 or if types don't match (int is converted to float for comparison)

        NO REPORT if value1 and value2 are equal within tolerance and not nan, 
               OR if both value1 and value2 are NAN, 
               OR if comparison is float and value1 and value2 are str

        '''

        
        okValue, okName = True, name1==name2

        okType = (isinstance(value1, (int,float)) and isinstance(value2, (int,float))) or (type(value1)==type(value2))
            
        if not okType:
            pass
        elif type(value1) is str :
            okValue = value1==value2 or comparison=='float' 
        else : 
            okValue = (value1==value1 and abs(float(value2)-float(value1))<tolerance) or (value1!=value1 and value2!=value2)


        if okValue and okName and okType : return True,''
        rs = ''
        if okName :
            rs = name1
        else:
            rs = ' Non-matching names `'+name1+'` and `'+name2+'`'
        if not okValue:
            if type(value1) is str:
                rs += ' Unequal values ' + value1 + ' ' + value2
            else:
                rs += ' Unequal values {:.0f} {:.0f}'.format(value1,value2)
        if not okType: rs += ' Different types {} {}'.format( type(value1),type(value2))
        return False,rs

    def main(self):

        favColumns1 = self.findFavColumns(self.file1)
        favColumns2 = self.findFavColumns(self.file2)

        LimitingRows1, RowNames1 = self.findLimitingRows(self.file1)
        LimitingRows2, RowNames2 = self.findLimitingRows(self.file2)

        decks = [ [self.file1,favColumns1, LimitingRows1, RowNames1], [self.file2, favColumns2, LimitingRows2, RowNames2] ]
        self.compare(decks,LABEL='OverheadRates')
        self.compare(decks)



        return
if __name__ == '__main__':
    debug = 0
    file1='/Users/djaffe/Documents/Belle II/Software_Computing/ResourceEstimates/20210902_fixPB/ResourceEstimate-2021-09-02-RawDataCenterPB dj.xlsx'
    file2='/Users/djaffe/Documents/Belle II/Software_Computing/ResourceEstimates/20210902_fixPB/ResourceEstimate-2021-09-02-RawDataCenterPB.xlsx'
    sheet='Budget Model'
    if len(sys.argv)>1 : debug = int(sys.argv[1])
    if len(sys.argv)>2 :
        file1 = sys.argv[2]
        file2 = sys.argv[3]
    if len(sys.argv)>4 :
        sheet = sys.argv[4]
    t = CompareXlsx(debug=debug,file1=file1,file2=file2,sheet=sheet)
    t.main()
