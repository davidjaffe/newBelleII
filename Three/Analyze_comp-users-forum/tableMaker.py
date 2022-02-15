#!/usr/bin/env python
'''
make tables suitable for text and latex

moved from analyzeCUF on 20220210

20220210
'''
import sys,os


class tableMaker():
    def __init__(self):
        print('tableMaker.__init__ Completed')
        return
    def pieTable(self,freq, persons, caption=None):
        '''
        take input frequency (integers) for each person and create input for tableMaker to produce table
        with form of row:  Ni   fi  name_i, 
        where 
        Ni = # of instances for person i
        fi = Ni/sum(Ni)

        sorted with greatest frequency at the top
        '''
        headers = ['Instances','Fraction']
        FMT     = ['d','.3f']
        rows, rowlabels = [],[]
        Ntot = sum(freq)
        fsum = 0.
        for Ni,pi in sorted(zip(freq,persons),reverse=True):
            fi = float(Ni)/float(Ntot)
            fsum += fi
            rows.append( [Ni, fi] )
            rowlabels.append( pi )
        rows.append( [Ntot, fsum] )
        rowlabels.append( 'Total')
        self.tablePrintBoth(headers,rows,rowlabels,caption=caption,FMT=FMT)
        return
    def tablePrintBoth(self,headers,rows,rowlabels,integers=False,caption=None,FMT=None):
        '''
        wrapper around tableMaker to make and print latex and non-latex tables
        '''
        for latex in [True, False]:
            table = self.tableMaker(headers,rows,rowlabels,integers=integers,caption=caption,latex=latex,FMT=FMT)
            print(table)
        return
    def tableMaker(self,headers,rows,rowlabels,integers=False,caption=None,latex=False,FMT=None):
        '''
        return table, suitable to print, given headers, rows and row labels
        headers = list of header titles with length NH = [h1, h2, ..., hNH]
        rows = list of lists with each row of length NH = [ [a1, a2, ..., aNH], ... [z1, z2, ..., zNH] ] 
        rowlabels = list of row labels with length = # of rows
        
        if latex = True, then print latex-compatible table

        if FMT is a list, then the input integers is IGNORED and the fields for each column are taken
        from FMT

        '''
        ## define latex variables(if needed), formats for header, row
        latexAlign, latexReturn = '', ''
        if latex : latexAlign, latexReturn  = ' & ', '\\\ ' # gives \\, trailing space is required
        
        fprec = '.1f'
        if integers : fprec = 'd'

        if type(FMT) is list and len(FMT)!=len(headers) :
            sys.exit('tableMaker.tableMaker ERROR Input len(FMT)=' + str(len(FMT)) + ' is not the same as len(headers)=' + str(len(headers)))
            
            
        hfmt = ''  # header format
        ffmt = ''  # row format
        for i,h in enumerate(headers):
            if type(FMT) is list : fprec = FMT[i]
            fm = '{:'+fprec+'}'

            L = len(h)
            for r in rows:
                L = max(L,len(fm.format(r[i])))
            hfmt += '{'+str(i)+':>'+str(L)+'} '
            if i<len(headers) : hfmt += latexAlign
            ffmt += '{'+str(i)+':>'+str(L)+fprec+'} '
            ffmt += latexAlign
        i += 1
        ffmt += ' {'+str(i)+'} '

        # begin creating table
        table = ''
        if latex :
            ncol = 1 + len(headers)
            table += '\\begin{tabular}{'
            for i in range(len(headers)): table += 'c '
            table += '| l } \n'
        if caption is not None :
            if latex :
                table += '\\multicolumn{'+str(ncol)+'}{c}{'+caption+'}' + latexReturn + '\n'
            else:
                table += caption + '\n'
        table += hfmt.format(*headers)
        table += latexReturn 
        table += '\n'
        for ir,r in enumerate(rows):
            Q = [x for x in r]
            Q.append(rowlabels[ir])
            table += ffmt.format(*Q) + latexReturn + '\n'
        if latex : table += '\\end{tabular} \n'
            
        return table
if __name__ == '__main__' :
    
    testTableMaker1 = False
    if testTableMaker1 :
        headers = ['pigs', 'monkeys', 'sheep']
        rows = [ [50427,88,219], [73, 102, 12], [129, 11, 512] ]
        rowlabels = ['Fred`s farm','Mary`s house','At college']
        tM = tableMaker()
        latex = False
        table = tM.tableMaker(headers,rows,rowlabels,integers=True,caption='Here is a test table!!',latex=latex)
        print(table)
        latex = True
        table = tM.tableMaker(headers,rows,rowlabels,integers=True,caption='Here is a LaTeX table!!',latex=latex)
        print(table)
        sys.exit('done testing tableMaker1')

    testTableMaker2 = True
    if testTableMaker2 :
        freq = [5,12,7,9,4,10,8]
        persons = ['Nate', 'Andy','Sara', 'Betty', 'Sunej', 'Tom', 'Anwar']
        caption = 'This is a test for the pie table'
        tM = tableMaker()
        tM.pieTable(freq,persons,caption=caption)
        sys.exit('done with tableMaker2 test of pieTable')
