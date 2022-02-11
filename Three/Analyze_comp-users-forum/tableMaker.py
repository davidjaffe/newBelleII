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
    
        
        self.debug = debug
        self.plotToFile = plotToFile

        now = datetime.datetime.now()
    def tableMaker(self,headers,rows,rowlabels,integers=False,caption=None,latex=False):
        '''
        return table, suitable to print, given headers, rows and row labels
        headers = list of header titles with length NH = [h1, h2, ..., hNH]
        rows = list of lists with each row of length NH = [ [a1, a2, ..., aNH], ... [z1, z2, ..., zNH] ] 
        rowlabels = list of row labels with length = # of rows
        
        if latex = True, then print latex-compatible table

        '''
        ## define latex variables(if needed), formats for header, row
        latexAlign, latexReturn = '', ''
        if latex : latexAlign, latexReturn  = ' & ', '\\\ ' # gives \\, trailing space is required
        
        fprec = '.1f'
        if integers : fprec = 'd'
        hfmt = ''  # header format
        ffmt = ''  # row format
        fm = '{:'+fprec+'}'
        for i,h in enumerate(headers):
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
    
    testTableMaker = True
    if testTableMaker :
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
        sys.exit('done testing tableMaker')
