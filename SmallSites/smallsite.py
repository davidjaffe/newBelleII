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

#import datetime


class smallsite():
    def __init__(self):

        print 'smallsite.__init__'
        
        self.debug = 0

        self.csvfn = 'GGUS_tickets.csv'

        self.resource_est = '/Users/djaffe/Documents/Belle II/Software_Computing/ResourceEstimates/20200616/ResourceEstimate-2020-06-16.xlsx'

        self.gridsites = 'GridSites_20200902.xlsx'

        self.noRDC = True
        self.invalidSite = ['']
        if self.noRDC: 
            self.invalidSite = ['','JP-KEK-CRC-02','BNL-Belle-II']
            print 'smallsite.__init__ Exclude Raw Data Centers from list of sites'
        self.invalidSubject = ['test']
        
        return
    def rdr(self):
        '''
        read in csv file
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
        for row in rdr:
            totRows += 1
            Site   = row[colidx['Site']]
            Type   = row[colidx['Type']]
            Subj   = row[colidx['Subject']]

            if self.validTicket(Site,Subj,Type):
                totTix += 1
                if Site not in Tix: Tix[Site] = []
                Tix[Site].append( Subj )
                if Site=='': print 'smallsite.rdr Blank site. Type,Subject',Type,Subj
                    

        f.close()
        print 'smallsite.rdr',totTix,'valid tickets out of',totRows,'tickets'

        return Tix
    def validTicket(self,Site,Subj,Type):
        ''' 
        return True if Site,Subj and Type are valid 
        '''
        for s in self.invalidSite:
            if Site==s: return False
                
        if Type=='USER': return False

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
        '''
        country = None
        gridS = self.gridS
        for c in gridS:
            for s in gridS[c]:
                if Site==s or Site in s or Site.split('-')[0] in s:  # exact match or Site contained in name
                    country = c
                    break
        
        if country is None:
            print 'smallsite.assignCtoS Try special treatment for Site',Site
            if 'INFN' in Site : country = 'Italy'
            if 'TW-'  in Site : country = 'Taiwan'
                
        return country
    def gridSites(self):
        '''
        return dict[country] = [site1,site2...]
        '''
        wb = xlrd.open_workbook(self.gridsites)
        sheet = wb.sheet_by_name('Sheet1')
        colC  = 0 # country name
        colS  = 1 # Site
        colGN = 2 # grid name
        gridS = {}
        for row in range(340):
            country = sheet.cell_value(row,colC)
            if country!='Country' and country!='':
                if country not in gridS: gridS[country] = []
                gn = sheet.cell_value(row,colGN)
                site = sheet.cell_value(row,colS)
                if self.debug>0 : print 'smallsite.gridSites country,site,gridname',country,site,gn
                gridS[country].append(gn)
        return gridS
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
        if self.debug>0 : print 'smallsite.getRE yearRow,yearCol,year',yearRow,yearCol,cell
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
    def justify(self,ntixC,RE,Year):
        '''
        Table of tickets/country and fraction disk/country
        '''
        sorted_RE = sorted(RE.items(), key=operator.itemgetter(1))
        sumDisk = 0.
        for country in RE:
            sumDisk += RE[country]
        
        print '{0:>8} {1:>8} {2:>8} {3}. Uses {4} resource estimate.'.format('Disk(PB)','Fraction','#tickets','Country',Year)
        for x in sorted_RE:
            country = str(x[0])
            disk = x[1]
            n = 0
            if country in ntixC: n = ntixC[country]
            print '{0:>8.3f} {1:>8.3f} {2:>8} {3}'.format(disk, disk/sumDisk,n,country)
        return            
    def main(self,Year=2021):
        self.gridS = self.gridSites()
        Tix = self.rdr()
        ntixC = self.tixBySite(Tix) # return number of tickets per country
        RE = self.getRE(Year=Year)   # resources per country
        self.justify(ntixC, RE,Year)

        return
if __name__ == '__main__' :

    ss = smallsite()
    ss.main()
    
