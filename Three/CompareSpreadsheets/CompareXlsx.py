#!/usr/bin/env python
'''
compare one sheet in two xlsx files, using pandas
20221223
20221228 Specialize to comparing Budget Model sheets

ref: https://stackoverflow.com/questions/37113173/compare-2-excel-files-using-python

'''
import sys,os
import math
# import xlrd
import numpy
import pandas as pd
import copy
import shutil
import datetime
import Logger # direct stdout to file & terminal 


class CompareXlsx():
    def __init__(self,debug=0,file1='/Users/djaffe/Documents/Belle II/Software_Computing/ResourceEstimates/20210902_fixPB/ResourceEstimate-2021-09-02-RawDataCenterPB dj.xlsx',file2='/Users/djaffe/Documents/Belle II/Software_Computing/ResourceEstimates/20210902_fixPB/ResourceEstimate-2021-09-02-RawDataCenterPB.xlsx',sheet='Budget Model'):

        self.debug = debug

        self.file1 = file1
        self.file2 = file2
        self.sheet = sheet

        self.now = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
        logfile = 'LOGS/' + self.now + '.log'
        sys.stdout = Logger.Logger(fn=logfile)
        print('CompareXlsx.__init__ Output directed to stdout and',logfile)
        
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

        ## fill RowNames from inclusive list of rows between LimitingRows
        ## require the second column of row to have content (not a Nan or zero length string)
        ## this requirement should avoid rows that are the sum of preceding rows based on idiosyncracy of Budget Model table
        for label in RowNames:
            i1,i2 = LimitingRows[label][0][1],LimitingRows[label][1][1]+1  # inclusive range
            for irow in range(i1,i2):
                name = ''
                names = []
                for icol,colName in enumerate(DS.columns):
                    cell = DS.iloc[irow,icol]
                    if cell==cell : # avoid nans
                        name += str(cell) + ' '
                        names.append( str(cell) )
                    else:
                        names.append( '' )
                if len(name)>0 and names[1]!='' : RowNames[label][irow] = name
                
            if self.debug > 1 : print('CompareXlsx.findLimitingRows label',label,'RowNames',RowNames[label])
            
        return LimitingRows, RowNames
    def compare(self,decks,LABEL=None):
        '''
        compare same sheet from two xlsx files specified in decks = [ [list1], [list2] ]
        list1 = [filename, favColumns, LimitingRows, RowNames]

        input LABEL can be used to comparison to a section of spreadsheet. 
        LimitingRows.keys contain the section names  

        only compare columns specified in favColumns that appear in both sheets

        only the first instance of a difference between row values for a given column header will be reported
        '''
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

        ## only compare columns that appear in both sheets
        colNames = sorted(list(set(favColumns[0].keys())&set(favColumns[1].keys())))  # common column names only

        print('\n',*['+' for x in range(120)],sep='')
        print('+++++ CompareXlsx.compare \n+++++ Compare files',File[0],File[1],' and list differences',self.now)
        for fn in File:
            if os.path.islink(fn) : print('+++++',fn,'is',os.path.realpath(fn))
        print('+++++ Designate column header by NAME and column numbers(counts from 0) in the two files: NAME(icol1,icol2)')
        print(*['=' for x in range(120)],sep='')

        if self.debug > 1 : print('CompareXlsx.compare DEBUG printout enabled for file comparison')
        
        for label in Labels:   ## section labels
            if self.debug > 1 : print('\n',label)
            printBuffer = '\n' + label + '\n'
            NoProblem = True
            badValues, badNames = 0, 0
            for colName in colNames:
                for icol1,icol2 in zip(favColumns[0][colName],favColumns[1][colName]):
                    header  = 'Column header ' + colName + '('+str(icol1)+','+str(icol2)+')'
                    for irow1,irow2 in zip(RowNames[0][label],RowNames[1][label]):
                        name1 = RowNames[0][label][irow1]
                        name2 = RowNames[1][label][irow2]
                        value1 = Frame[0].iloc[irow1,icol1]
                        value2 = Frame[1].iloc[irow2,icol2]
                        OK, words, okValue, okName = self.reportComparison(name1,value1,name2,value2,comparison='float')
                        if not okValue : badValues += 1
                        if not okName  : badNames  += 1
                        if (not OK) and (words not in printBuffer) :
                            NoProblem = False
                            if header is not None:
                                if self.debug > 1 : print(header)
                                printBuffer = self.addToBuffer(printBuffer,header)
                            header = None
                            if self.debug > 1 : print(words)
                            printBuffer = self.addToBuffer(printBuffer,words)
            if NoProblem :
                words = 'No problems found for '+label
                if self.debug > 1 : print(words)
                printBuffer = self.addToBuffer(printBuffer,words)
            else:
                words = '{} had {} instances of unequal values and {} instances of non-matching names'.format(label,badValues,badNames)
                if self.debug > 1 : print(words)
                printBuffer = self.addToBuffer(printBuffer,words)
            print(printBuffer)

        

        return
    def addToBuffer(self,printBuffer,newLine):
        '''
        add newLine to end of printBuffer unless newLine already exists in printBuffer
        return printBuffer
        '''
        if self.debug > 2 : print('CompareXlsx.addToBuffer Entry len(printBuffer)',len(printBuffer),'newLine',newLine)
        if newLine in printBuffer : return printBuffer
        printBuffer += newLine + '\n'
        if self.debug > 2 : print('CompareXlsx.addToBuffer Exit len(printBuffer)',len(printBuffer))
        return printBuffer
    def reportComparison(self,name1,value1,name2,value2,comparison='float',tolerance=1.):
        '''
        Inputs:
        name1,name2 are strings
        value1, value2 are ints, floats or strings
        comparison can be 'float' or 'str'
        tolerance is explained below

        REPORT issued if value1 != value2 or if name1!=name2 or if types don't match (int is converted to float for comparison)
        return False, string_with_report, okValue, okName
        where okValue = False if value1!=value2
              okName  = False if name1 !=name2

        NO REPORT if value1 and value2 are equal within tolerance and not nan, 
               OR if both value1 and value2 are NAN, 
               OR if comparison is float and value1 and value2 are str
        return True, '', okValue, okName
        

        '''
        
        okValue = True
        okName = name1==name2
        okType = (isinstance(value1, (int,float)) and isinstance(value2, (int,float))) or (type(value1)==type(value2))
            
        if not okType:
            pass
        elif type(value1) is str :
            okValue = value1==value2 or comparison=='float' 
        else : 
            okValue = (value1==value1 and abs(float(value2)-float(value1))<tolerance) or (value1!=value1 and value2!=value2)

        if okValue and okName and okType : return True,'',okValue,okName
            
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
                if not (math.isnan(value1) or math.isnan(value2) or value1==0. or value2==0.) :
                    rs += ' ratio {:.4f}'.format(value1/value2)
        if not okType: rs += ' Different types {} {}'.format( type(value1),type(value2))
        return False,rs,okValue,okName
    def compareRows(self,XL1,XL2,sheet,colRange,onlyDifferences=True,truncate=True):
        '''
        compare rows with same row labels for sheet in excel files XL1 and XL2 for column range colRange (a string,ie "A:E")
        
        Report differing (all) rows if onlyDifferences is True (false)
        Report rows appearing in only one of the files

        if truncate is True, long row labels are truncated to fit on the terminal screen
        '''
        if self.debug > 1 : print('CompareXlsx.compareRows Begin with debug output -------------')

        ## hrow and idxCol settings are specific to Risk Register sheets
        hrow = 1    # header row (count from 0)
        idxCol = 1  # unique row labels (count from 0)

        ### information useful for output (headers and terminal width)
        DS = pd.read_excel(XL1,sheet_name=sheet,usecols=colRange,header=hrow)
        headers = list(DS.head(0))
        big = 0
        for irow in range(len(DS)):
            if DS.iloc[irow,1]==DS.iloc[irow,1] : big = max(big,len(DS.iloc[irow,0]))
        termwidth = shutil.get_terminal_size()[0]
        if not truncate : termwidth = int(1.e4)
            
        DS1 = pd.read_excel(XL1,sheet_name=sheet,usecols=colRange,header=hrow,index_col=idxCol)
        DS2 = pd.read_excel(XL2,sheet_name=sheet,usecols=colRange,header=hrow,index_col=idxCol)

        if self.debug > 2 : print('headers',headers)

        if self.debug > 2 :
            print(XL1,len(DS1.index),DS1.index)
            print(XL2,len(DS2.index),DS2.index)

        # get common list of row names. and row names for list in only one file (uncommon)
        Rn1 = DS1.index
        Rn2 = DS2.index
        # remove nans
        rn1 = Rn1[Rn1.notnull()]
        rn2 = Rn2[Rn2.notnull()]
        # get list of common and uncommon row names
        common = (list(set(rn1)&set(rn2)))
        uncommon = list(set(rn1)-set(rn2))
        uncommon.extend( list(set(rn2)-set(rn1)) )
        if self.debug > 2 : print('uncommon',uncommon)

        # report common rows. use cMap to follow order of file1
        Rn1,Rn2 = list(Rn1),list(Rn2)
        commonMap = {}
        for rowlabel in common:
            i1 = Rn1.index(rowlabel)
            i2 = Rn2.index(rowlabel)
            commonMap[rowlabel] = [i1,i2]
            if self.debug > 2 : print('making commonMap: rowlabel',rowlabel,'i1,i2',i1,i2)
        cMap = {k:v for k,v in sorted(commonMap.items(), key=lambda item: item[1][1])}
        if self.debug > 2 : print('cMap',cMap)

        print('\nCompareXlsx.compareRows Comparison of common rows between input files')
        fmt = '{:>'+str(big)+'} {:} {:}'
        sz2 = termwidth-big-max(len(XL1),len(XL2))-5
        print(fmt.format(headers[0],headers[idxCol],''))
        nonIdentical = 0
        DS1 = pd.read_excel(XL1,sheet_name=sheet,header=hrow,usecols=colRange)#,nrows=1,skiprows=i1)
        DS2 = pd.read_excel(XL2,sheet_name=sheet,header=hrow,usecols=colRange)#,nrows=1,skiprows=i2)
        
        for rowlabel in cMap:
            i1,i2 = cMap[rowlabel]

            row1 = list(DS1.iloc[i1,0:])
            row2 = list(DS2.iloc[i2,0:])

            if self.debug > 2 : 
                print('row1',row1)
                print('row2',row2)

            identical = row1==row2
            words = 'is the same'
            if not identical :
                nonIdentical += 1
                words = 'DIFFERS'

            if not onlyDifferences or not identical :
                print(fmt.format(row1[0],rowlabel[:sz2],words))
                if self.debug > 0: 
                    print('  Differences of',XL1,'wrt',XL2,set(row1)-set(row2))
                    print('  Differences of',XL2,'wrt',XL1,set(row2)-set(row1))
        if onlyDifferences and nonIdentical==0: print('ALL ROWS IDENTICAL')

        ### list rows only listed in one of the two files. don't worry about order. 
        if len(uncommon)>0:
            print('\nCompareXlsx.compareRows List rows appearing in only one file')
            print(fmt.format(headers[0],headers[idxCol],''))
        for rowlabel in uncommon:
            i1,i2 = -1,-1
            if rowlabel in Rn1: i1,XL = Rn1.index(rowlabel),XL1
            if rowlabel in Rn2: i2,XL = Rn2.index(rowlabel),XL2
            if i1>-1 and i2>-1 : sys.exit('ERROR '+rowlabel+' is present in both files')
            if i1==-1 and i2==-1 : sys.exit('ERROR '+rowlabel+' does not appear in either file')
            DS = pd.read_excel(XL,sheet_name=sheet,header=hrow,usecols=colRange,nrows=1,skiprows=max(i1,i2))
            print(fmt.format(DS.columns[0],rowlabel[:sz2],XL))
            
        if self.debug > 1 : print('CompareXlsx.compareRows End ^^^^^^^^^^^^^^^^^^^^^^^')
        return
    def simple(self):
        '''
        simple row-by-row compare of sheet sheet for file1 and file2
        mainly designed for Risk Register
        '''
        colRange = 'A:N'
        file1 = self.file1
        file2 = self.file2
        sheet = self.sheet
        
        print('\nCompareXlsx.simple Compare all rows in columns',colRange,'for sheet',sheet,'for',file1,'and',file2)
        for fn in [file1,file2]:
                if os.path.islink(fn) : print('+++++',fn,'is',os.path.realpath(fn))
        self.compareRows(file1,file2,sheet,colRange)
        return
    def main(self):
        '''
        Compare specific row,columns in self.sheet of files self.file1 and self.file2.
        
        '''

        print('CompareXlsx.main First do setup for comparison')
        favColumns1 = self.findFavColumns(self.file1)
        favColumns2 = self.findFavColumns(self.file2)

        LimitingRows1, RowNames1 = self.findLimitingRows(self.file1)
        LimitingRows2, RowNames2 = self.findLimitingRows(self.file2)
        print('CompareXlsx.main Setup complete, begin comparison\n')

        decks = [ [self.file1,favColumns1, LimitingRows1, RowNames1], [self.file2, favColumns2, LimitingRows2, RowNames2] ]
        #self.compare(decks,LABEL='OverheadRates')
        self.compare(decks)



        return
if __name__ == '__main__':    
    debug = 0
    file1='/Users/djaffe/Documents/Belle II/Software_Computing/ResourceEstimates/20210902_fixPB/ResourceEstimate-2021-09-02-RawDataCenterPB dj.xlsx'
    file2='/Users/djaffe/Documents/Belle II/Software_Computing/ResourceEstimates/20210902_fixPB/ResourceEstimate-2021-09-02-RawDataCenterPB.xlsx'
    sheet='Budget Model'
    if len(sys.argv)==1:
        print('USAGE: python CompareXlsx.py [debug({})] [file1] [file2] [sheet({})]'.format(debug,sheet),'\n DEFAULT file1 =',file1,'\n DEFAULT file2 =',file2)
        print('NOTE: Simple comparison suitable for risk register is done if sheet != `Budget Model`')
        sys.exit('End of usage help')
    if len(sys.argv)>1 : debug = int(sys.argv[1])
    if len(sys.argv)>2 :
        file1 = sys.argv[2]
        file2 = sys.argv[3]
    if len(sys.argv)>4 :
        sheet = sys.argv[4]
    t = CompareXlsx(debug=debug,file1=file1,file2=file2,sheet=sheet)
    if sheet=='Budget Model' :
        t.main()
    else:
        t.simple()
