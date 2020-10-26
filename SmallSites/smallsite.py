#!/usr/bin/env python
'''
parse GGUS_tickets.csv from Cedric
20200902
'''
#import math
import sys,os
import csv
import operator
import xlrd
import copy

#from collections import Counter

#import datetime


class smallsite():
    def __init__(self):

        print 'smallsite.__init__'
        
        self.debug = 0

        self.csvfn = 'GGUS_tickets.csv'

        self.resource_est = '/Users/djaffe/Documents/Belle II/Software_Computing/ResourceEstimates/20200616/ResourceEstimate-2020-06-16.xlsx'

        self.gridsites = 'GridSites_20200902.xlsx'

        self.noRDC = False
        self.invalidSite = ['']
        if self.noRDC: 
            self.invalidSite = ['','JP-KEK-CRC-02','BNL-Belle-II']
            print 'smallsite.__init__ Exclude Raw Data Centers from list of sites'
        self.invalidSubject = ['test']
        
        return
    def rdr(self):
        '''
        read in csv file of GGUS tickets
return dict[site] = [ subject1, subject2, ...]
        '''

        statusFails,countryFails = 0,0
        
        f = open(self.csvfn,'r')
        print 'smallsite.rdr Opened',self.csvfn
        rdr = csv.reader(f,delimiter=';')
        header = rdr.next()
        if self.debug > 0 : print 'smallsite.rdr First row',header
        colwords = ['Ticket-ID','Type', 'Site','Subject']
        colabr   = ['firstn','lastn','cat','inst','status','country','IR']
        colidx = {}
        for w in colwords:
            colidx[w] = header.index(w)
        Tix = {}
        totRows,totTix = 0,0
        allSites = []
        for row in rdr:
            totRows += 1
            Site   = row[colidx['Site']]
            Type   = row[colidx['Type']]
            Subj   = row[colidx['Subject']]

            allSites.append(Site)

                
            if self.validTicket(Site,Subj,Type):
                totTix += 1
                if Site not in Tix: Tix[Site] = []
                Tix[Site].append( Subj )
                if Site=='': print 'smallsite.rdr Blank site. Type,Subject',Type,Subj
                    

        f.close()
        print 'smallsite.rdr',totTix,'valid tickets out of',totRows,'tickets'

        uniqueSites = list(set(allSites))
        uniqueSites.sort()
        if self.debug>0: print 'smallsite.rdr list of unique sites ',uniqueSites
        noValidTicket = []
        for Site in uniqueSites:
            if Site not in Tix: noValidTicket.append(Site)
        if self.debug>0: print 'smallsite.rdr list of sites with no valid ticket',noValidTicket
        return Tix
    def uniqTix(self,Tix,RE):
        '''
        uniquely categorize GGUS tickets by subject content
        Paul's suggestion
        storage : 'file fail', 'transfer fail/error', 'file'
        service : 'amga', 'voms', 'fts', 'cvmfs', 'conditions fail' 
        job : 'pilot','job fail'
        other : everything else
        input Tix[Site] = [subject1, subject2, ...]
        input RE[Country] = PB of storage
        output to csv : tickets and fraction of total tickets
        '''

        debug_here = 0
        if debug_here > 0 : print 'smallsite.uniqTix RE',RE
        
        pb = {'storage' : ['storage', 'transfer_fail','transfer_error','file','access_fail','upload','download','i/o_fail','i/o_error','disk'],
                  'service' : ['install','amga', 'voms', 'fts', 'cvmfs', 'condition_fail','authorization_fail','connection_fail','expir','revision','certificate'],
                  'job' : ['job','pilot','submission_fail','submission_error'],
                  'other' : [''] 
                  }
        pb_order = ['service', 'job', 'storage', 'other']
        blanks   = [0 for x in range(len(pb_order))]

        pb_count = {} # categorized problems by site
        pb_byC   = {} # categorized problems by country
        totDisk = sum(RE.values())
        for country in RE:
            pb_byC[country] = [RE[country]/totDisk, country]
            pb_byC[country].extend( blanks )
        totTix = 0
        for Site in Tix:
            country = self.assignCtoS(Site)
            if debug_here > 1 : print 'smallsite.uniqTix Site,country',Site,country
            pb_count[Site] = [country,Site]
            Subj = copy.copy(Tix[Site])
            totTix += len(Subj)
            if debug_here>0: print '\nsmallsite.uniqTix Site,Subj',Site,Subj
            for pcat in pb_order:
                words = pb[pcat]
                n = 0
                if debug_here>1: print 'smallsite.uniqTix Site,pcat,words,Subj',Site,pcat,words,Subj
                for w in words:
                    w1,w2 = w,w
                    if '_' in w: w1,w2 = w.split('_')[0],w.split('_')[1]
                    for s in Subj[:]:
                        if debug_here>2: print 'smallsite.uniqTix Site,w,s,len(Subj)',Site,w,s,len(Subj)
                        sl = s.lower()
                        if w1 in sl and w2 in sl :
                            n += 1
                            Subj.remove(s)
                            if debug_here>1:print 'smallsite.uniqTix Site, REMOVE',s
                pb_count[Site].append( n )
                if debug_here>0: print 'smallsite.uniqTix Site,pcat,n,Subj',Site,pcat,n,Subj
            for i,n in enumerate(pb_count[Site]):
                if type(n) is int : pb_byC[country][i] += n
        if debug_here > 0:
            print 'smallsite.uniqTix pb_order',pb_order
            print 'smallsite.uniqTix pb_count',pb_count
            print 'smallsite.uniqTix pb_byC',pb_byC
        # prepare output for csv files
        
        # tickets/category per site
        header = ['Country','Site']
        header.extend(pb_order)
        data = [ header ]
        totpbs = 0
        for Site in pb_count:
            data.append( pb_count[Site] )
            totpbs += sum(pb_count[Site][2:])
        if totTix!=totpbs : sys.exit('smallsite.uniqTix ERROR totTix '+str(totTix)+' differs from totpbs '+str(totpbs))

        caption = []
        
        caption.append( [] )
        caption.append( ['Analysis of 2016-2020 GGUS tickets by Subject keywords'] )
        caption.append( ['Keyword or word pairs used to define exclusive categories: ' + ' '.join(pb_order)])
        for key in pb_order:
            caption.append( [ key + ' = ' + self.render(pb[key]) ] )
        data.extend( caption )
        fn = 'uniqTix_bySite.csv'
        self.writeCSV(fn,data)

        # tickets/category ordered by disk fraction/country
        sorted_RE = sorted(RE.items(), key=operator.itemgetter(1))
        header = ['Fraction','Site']
        header.extend(pb_order)
        data = [ header ]
        for x in sorted_RE:
            country = str(x[0])
            data.append(pb_byC[country])
        data.extend( caption )
        fn = 'uniqTix_byFraction.csv'
        self.writeCSV(fn,data)

        # fractional tickets/category ordered by disk fraction/country
        data = [ header ]
        for x in sorted_RE:
            country = str(x[0])
            L = pb_byC[country]
            newL = []
            for y in L:
                z = y
                if type(y) is int: z = float(y)/float(totTix)
                newL.append(z)
            data.append(newL)
        data.extend( caption )
        fn = 'uniqTixFraction_byFraction.csv'
        self.writeCSV(fn,data)
                    
        return
    def render(self,klist):
        '''
        return formatted list of keywords used in uniqTix given list
        '''
        l = []
        for w in klist:
            l.append( w.replace('_',' ') )
        line = ' / '.join(l)
        return line
    def tagTix(self,Tix,RE):
        '''
        try to sort and filter GGUS tickets by subject content
        input Tix[Site] = [subject1, subject2, ...]
        input RE[Country] = PB of storage
        output to csv
        list of words
        wordcount[site] = [ Site, count_word1, count_word2, ...]
        '''
        words = ['amga', 'voms', 'fts','cvmfs', 'pilot', 'file_fail', 'job_fail','condition_fail','transfer_fail','transfer_error','file','fail','']
        wordcount = {}
        for Site in Tix:
            wordcount[Site] = [Site]
            for w in words:
                w1,w2 = w,w
                if '_' in w: w1,w2 = w.split('_')[0],w.split('_')[1]
                n = 0
                for s in Tix[Site]:
                    sl = s.lower()
                    if w1 in sl and w2 in sl : n += 1
                wordcount[Site].append( n )

        
        if self.debug>0: print '\nsmallsite.tagTix Site wordcount',words
        header = ['Country','Site']
        words[-1] = 'Total'
        nw = []
        for w in words: nw.append(w.replace('_',' '))
        words = nw                                      
        header.extend(words)
        data = [ header ]
        for Site in sorted(wordcount):
            if self.debug>0: print Site,wordcount[Site]
            country = self.assignCtoS(Site)
            L = copy.copy( wordcount[Site] )
            L.insert(0,country)
            data.append( L )
        if self.debug>0: print ''
        descrip1 = ['Analysis of 2016-2020 GGUS tickets Subject by keyword(s) in column header']
        descrip2 = ['Note that keywords are not exclusive, so sum of row does not equal Total in rightmost column.']
        descrip3 = ['Leftmost columns are country and site names.']
        data.extend( [ [],descrip1, descrip2, descrip3 ] )
        # write csv file by site    
        if self.debug>1: print data
        fn = 'tagTix_bySite.csv'
        self.writeCSV(fn,data)

        # write csv file by country
        byC = {}
        for Site in wordcount:
            C = self.assignCtoS(Site)
            if C is not None: # no country for site 'CERN'
                C = str(C)
                if C not in byC :
                    byC[C] = wordcount[Site][1:]
                else:
                    byC[C] = [sum(x) for x in zip(byC[C],wordcount[Site][1:])]
        #print byC
        header = ['Country']
        header.extend(words)
        data = [ header ]
        for C in sorted(byC):
            L = copy.copy(byC[C])
            L.insert(0,C)
            #print L
            data.append( L )
        descrip4 = ['Leftmost column is country name.']
        data.extend( [ [],descrip1, descrip2, descrip4 ] )
        if self.debug>0: print data
        fn = 'tagTix_byCountry.csv'
        self.writeCSV(fn,data)
        
        # write csv file ordered by storage fraction
        sorted_RE = sorted(RE.items(), key=operator.itemgetter(1))
        sumDisk = 0.
        for country in RE:
            sumDisk += RE[country]
        nowords = ['' for x in words]
        header = ['Fraction','Country']
        header.extend(words)
        data = [ header ]
        for x in sorted_RE:
            country = self.fixCountry(str(x[0]))
            fraction = x[1]/sumDisk
            L = copy.copy(nowords)
            if country in byC: L = copy.copy(byC[country])
            #print 'country,L',country,L
            L.insert(0,'{0:.3f}'.format(fraction))
            L.insert(1,country)
            #print L
            data.append( L )
        descrip5 = ['Leftmost columns are disk storage fraction by 2021 pledge and country name.']
        data.extend( [ [],descrip1, descrip2, descrip5 ] )
        if self.debug>0: print data

        fn = 'tagTix_byFraction.csv'
        self.writeCSV(fn,data)


        return
    def writeCSV(self,fn,data):
        '''
        write csv file containing data
        '''
        f = open(fn,'w')
        with f:
            writer = csv.writer(f)
            writer.writerows(data)
        print 'smallsite.writeCSV Wrote',fn
        return
    def validTicket(self,Site,Subj,Type):
        ''' 
        return True if Site,Subj and Type are valid 
        '''
        for s in self.invalidSite:
            if Site==s: return False
                
        if Type=='USER': return False
        if Site=='CERN-PROD' : return False

        for s in self.invalidSubject:
            if Subj.lower()==s : return False

        return True
    def tixBySite(self,Tix,show=False):
        '''
        produce table of number of tickets by site and by country
        return dict[country] = ntickets
        '''
        ntix = {}
        ntixC= {}
        for site in Tix:
            ntix[site] = len(Tix[site])
        sorted_sites = sorted(ntix.items(), key=operator.itemgetter(1),reverse=True)
        if show : print '{0:>10} {1:>30} {2:>20}'.format('#tickets','Site','Country')
        for x in sorted_sites:
            Site = x[0]
            country = self.assignCtoS(Site)
            if show : print '{0:>10} {1:>30} {2:>10}'.format(x[1],Site,country)
            if country not in ntixC: ntixC[country] = 0
            ntixC[country] += x[1]
        if show : print '{0:>10} {1:>20}'.format('#tickets','Country')
        for country in ntixC:
            if show : print '{0:>10} {1:>20}'.format(ntixC[country],country)
        return ntixC
    def assignCtoS(self,Site):
        '''
        try to assign a country to each site
        First try to get country from dict[site] = country
        Then try to resolve based on dict[country] = [site1,site2,...]
        '''
        country = None

        debugHere = False
        
        gridStoC = self.gridStoC
        if Site in gridStoC :
            country = gridStoC[Site]
            if debugHere : print 'smallsite.assignCtoS 0th try Site,Country',Site,country
            return country
        
        gridS = self.gridS
        for c in gridS:
            for s in gridS[c]:
                if Site==s or Site in s or Site.split('-')[0] in s:  # exact match or Site contained in name
                    if debugHere : print 'smallsite.assignCtoS c,Site,s',c,Site,s
                    country = c
                    break
            if country is not None : break
        if debugHere : print 'smallsite.assignCtoS 1st try Site,Country',Site,country
        if country is None:
            if debugHere : print 'smallsite.assignCtoS Try special treatment for Site',Site
            if 'INFN' in Site : country = 'Italy'
            if 'TW-'  in Site : country = 'Taiwan'
                
        if debugHere : print 'smallsite.assignCtoS 2nd try Site,Country',Site,country
        return country
    def gridSites(self):
        '''
        process gridsites table
        note duplicates
        return 
           gridS = dict[country] = [site1,site2...]
           gridStoC = dict[site] = country
        '''
        wb = xlrd.open_workbook(self.gridsites)
        sheet = wb.sheet_by_name('Sheet1')
        colC  = 0 # country name
        colS  = 1 # Site
        colGN = 2 # grid name
        gridS = {}
        gridStoC = {}
        anyDup,acceptDup = False,True
        for row in range(340):
            country = self.clean(sheet.cell_value(row,colC))
            if country!='Country' and country!='':
                if country=='Czech Republic' : country = 'Czech'
                if country=='U.S.A.'         : country = 'USA'
                if country=='Japan'          : country = 'KEK'
                if country not in gridS: gridS[country] = []
                gn = self.clean(sheet.cell_value(row,colGN))
                site = self.clean(sheet.cell_value(row,colS))
                if self.debug>0 : print 'smallsite.gridSites country,site,gridname',country,site,gn
                if gn!='': ### NO BLANK GRID NAMES
                    gridS[country].append(gn)
                    if gn in gridStoC :
                        #print 'smallsites.gridSites: ERROR DUPLICATE? gridStoC[gn]=',gridStoC[gn],'gn',gn
                        anyDup = True
                    gridStoC[gn] = country
        if self.debug>0:
            print 'smallsite.gridSites gridS',gridS
            print 'smallsite.gridSites gridStoC',gridStoC
        if anyDup :
            if acceptDup: 
                print 'smallsites.gridSites WARNING Duplicates found'
            else:
                sys.exit('smallsites.gridSites ERROR Duplicates found')
        print 'smallsites.gridSites country, #sites, sites'
        noSites = []
        for country in sorted(gridS):
            print country,len(gridS[country]),gridS[country]
            if len(gridS[country])==0: noSites.append(country)
        print 'smallsites.gridSites Countries with no grid sites',', '.join(noSites)
                
        return gridS,gridStoC
    def clean(self,x):
        return str(x.replace(u'\xa0',''))
    def getRE(self,Year=2021,show=False):
        '''
        return dict[country] = PB of disk in Year

        Navigate to proper rows for countries and column for Year
        '''
        wb = xlrd.open_workbook(self.resource_est)
        sheet = wb.sheet_by_name('Total Cross-check')

        # find rows delimiting range of cells with country names
        # and the row with the year
        col = 0
        diskRow = None
        totalRow= None
        for row in range(100):
            cell = sheet.cell_value(row,col)
            if self.debug>1 : print 'smallsite.getRE row,col,cell',row,col,cell
            if cell=='Disk (PB)':
                if self.debug>0 : print 'smallsite.getRE Found row',row,cell
                diskRow = row
            if diskRow is not None and 'Total' in cell:
                if self.debug>0 : print 'smallsite.getRE Found row',row,cell
                totalRow = row
                break

        # find the column for the requested year
        yearRow = diskRow - 2
        yearCol = None
        for col in range(15):
            cell = sheet.cell_value(yearRow,col)
            if cell==Year:
                yearCol = col
                break
        cell = sheet.cell_value(yearRow,yearCol)
        if self.debug>1 : print 'smallsite.getRE yearRow,yearCol,year',yearRow,yearCol,cell
        # get country names and pledged disk(PB)
        RE = {}
        col = 0
        sumDisk = 0.
        for row in range(diskRow+1,totalRow):
            country = sheet.cell_value(row,col)
            disk    = sheet.cell_value(row,yearCol)
            RE[country] = disk
            sumDisk += disk
        if show : 
            print '{0:>8} {1:>8} {2} Year is {3}'.format('Disk(PB)','Fraction','Country',Year)
            sorted_RE = sorted(RE.items(), key=operator.itemgetter(1))
            for x in sorted_RE:
                country = x[0]
                disk = x[1]
                print '{0:>8.3f} {1:>8.3f} {2}'.format(disk,disk/sumDisk,country)
        return RE
    def readDowntimes(self,show=False):
        '''
        return DT[site] = [# of downtimes, days down]
        and DTC[country] = [total # downtimes, total days down]
        '''
        self.downtimefn = 'GOCDB_downtimes_B2_SE_since_1Jan2020_20200903.txt'
        f = open(self.downtimefn,'r')
        DT = {}
        DTC= {}
        for l in f:
            if l[0]!='#':
                s = l[:-1].split()
                fullsite,ndown,tdown = s
                site = fullsite.split('_')[0]
                DT[site] = [int(ndown),float(tdown)]
                C = self.assignCtoS(site)
                if C not in DTC: DTC[C] = [0, 0.]
                DTC[C][0] += int(ndown)
                DTC[C][1] += float(tdown)
        f.close()
        if show :
            print 'smallsite.readDownTimes: input file {3}\n {0:>10} {1:>10} {2}'.format('# down','days down','Site',self.downtimefn)
            for site in sorted(DT):
                ndown,tdown = DT[site]
                print '{0:>10} {1:>10.3f} {2}'.format(ndown,tdown,site)
            print '\n {0:>10} {1:>10} {2}'.format('# down','days down','Country')
            for country in sorted(DTC):
                ndown,tdown = DTC[country]
                print '{0:>10} {1:>10.3f} {2}'.format(ndown,tdown,country)
        if self.debug>0:
            print DT
            print DTC
                
        return DT,DTC
    def fixCountry(self,country):
        '''
        U.S.A. is same as USA
        Japan  is same as KEK
        '''
        C = country
        if country=='USA' : C = 'U.S.A.'
        if country=='KEK' : C = 'Japan'
        #if C!=country: print 'smallsite.fixCountry country,C',country,C
        return C
    def justify(self,ntixC,RE,DTC,Year):
        '''
        Table of tickets/country and fraction disk/country
        '''
        sorted_RE = sorted(RE.items(), key=operator.itemgetter(1))
        sumDisk = 0.
        for country in RE:
            sumDisk += RE[country]

        fn = 'justify.csv'
        f = open(fn,'w')
        
        line = '{0:>8}, {1:>8}, {2:>8}, {5:>8}, {6:>8}, {3}., Uses {4} resource estimate.'.format('Disk(PB)','Fraction','#tickets','Country',Year,'# down','days down')
        print line
        f.write(line+'\n')
        for x in sorted_RE:
            country = str(x[0])
            disk = x[1]
            n = 0
            C = self.fixCountry(country)
            if country in ntixC: n = ntixC[country]
            if C!=country and C in ntixC: n = ntixC[C]
            ndown,tdown = 0,0.
            if country in DTC: ndown,tdown = DTC[country]
            if C!=country and C in DTC : ndown,tdown = DTC[C]
            line = '{0:>8.3f}, {1:>8.3f}, {2:>8}, {4:>8}, {5:>8.3f}, {3}'.format(disk, disk/sumDisk,n,country,ndown,tdown)
            print line
            f.write(line+'\n')
        f.close()
        print 'smallsite.justify Wrote',fn
        return            
    def main(self,Year=2021):
        show = True
        self.gridS,self.gridStoC = self.gridSites()
        Tix = self.rdr()
        ntixC = self.tixBySite(Tix,show=show) # return number of tickets per country
        RE = self.getRE(Year=Year,show=show)   # resources per country
        DT,DTC = self.readDowntimes(show=show)
        self.tagTix(Tix,RE) # make some csv files
        self.uniqTix(Tix,RE) # uniquely categorize problems
        self.justify(ntixC, RE, DTC, Year)

        return
if __name__ == '__main__' :

    ss = smallsite()
    ss.main()
    
