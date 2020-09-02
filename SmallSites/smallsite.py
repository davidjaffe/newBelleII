#!/usr/bin/env python
'''
parse GGUS_tickets.csv from Cedric
20200902
'''
#import math
import sys,os
import csv
import operator


#import datetime


class smallsite():
    def __init__(self):

        print 'smallsite.__init__'
        
        self.debug = 0

        self.csvfn = 'GGUS_tickets.csv'

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
    def tixBySite(self,Tix):
        '''
        produce table of number of tickets by site
        '''
        ntix = {}
        for site in Tix:
            ntix[site] = len(Tix[site])
        sorted_sites = sorted(ntix.items(), key=operator.itemgetter(1),reverse=True)
        for x in sorted_sites:
            print x[1],x[0]
        return
    def main(self):
        Tix = self.rdr()
        self.tixBySite(Tix)
        return
if __name__ == '__main__' :

    ss = smallsite()
    ss.main()
    
