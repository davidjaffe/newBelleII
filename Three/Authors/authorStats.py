#!/usr/bin/env python
'''
compile, examine stats related to authors and institutions reviewing Belle II manuscripts

20220901
'''
#import math
import sys,os



#import matplotlib.pyplot as plt
import numpy


class authorStats():
    def __init__(self,internal=False):
        self.debug = 0

        self.dataFile = 'reviewData.txt'

        print('authorStats.__init__ completed')
        return
    def reader(self,fn):
        '''
        parse input file to extract info
        return pub # and reviewing institutions 
        '''
        f = open(fn,'r')
        print('authorStats.reader Opened',fn)
        prevLine = None
        pubNum = None
        pubInfo = {}
        for line in f:
            if 'B2Note' in line[:6]:
                if prevLine is None: sys.exit('authorStats.reader ERROR No previous line. Current line '+line[:-1])
                pubNum = int(prevLine)
            if 'Inst Reviews:' in line:
                j = len('Inst Reviews:')
                insts = [x.strip() for x in line[j+1:-1].strip('\t').split(',')]
                if pubNum is None : sys.exit('authorStats.reader ERROR pubNum is None. line '+line[:-1])
                pubInfo[pubNum] = insts
            prevLine = line
        if self.debug > 1 : print('authorStats.reader pubInfo',pubInfo)
        return pubInfo
    def processStats(self,pubInfo):
        '''
        some stats on the publication info
        '''
        allRevInst = []
        for pubNum in pubInfo:
            allRevInst.extend( pubInfo[pubNum] )
        totalInst = len(allRevInst)
        totalPubs = len(pubInfo)
        uniqInst = [a for a in set(allRevInst)]
        totalUniqInst = len(uniqInst)
        instFreq = {} # instFreq[inst] = freq
        freqShow = {} # freqShow[freq] = list of insts with that freq
        maxFreq = -1
        for inst in uniqInst:
            freq = allRevInst.count(inst)

            if inst in instFreq: sys.exit('authorStats.processStats ERROR inst already in dict ' + inst)
            instFreq[inst] = freq
            if self.debug > 1 : print('authorStats.processStats',inst,freq)
            if freq not in freqShow : freqShow[freq] = []
            freqShow[freq].append( inst )
            maxFreq = max(freq,maxFreq)
        s = dict(sorted(instFreq.items(), key=lambda item: item[1]))
        print('authorStats.processStats Sorted by frequency')
        for inst in s:
            print(s[inst],inst.strip())
        print('authorStats.processStats Institution frequency')
        for freq in range(maxFreq+1):
            if freq in freqShow: print(freq,','.join(sorted(freqShow[freq])))

        print(totalPubs,'total pubs reviewed by',totalInst,'institutions or  {:.2f} insts/pub. There are {} unique institution.'.format(totalInst/totalPubs,totalUniqInst))

        self.expected(totalPubs,uniqInst,totalInst/totalPubs)
                
        return
    def fillFreqShow(self,uniqInst,LIST):
        '''
        fill freqShow = dict = freqShow[freq] = list of institutions with frequency freq
        '''
        freqShow = {}
        for inst in uniqInst:
            freq = LIST.count(inst)
            if freq not in freqShow : freqShow[freq] = []
            freqShow[freq].append(inst)
        return freqShow
    def expected(self,nPubs,uniqInst,instPerPub):
        '''
        calculate expected frequency distribution assuming nPubs total publications 
        with reviewed by instPerPub instititons assigned to each publication.
        Draw institutions from uniqInst list of institutions
        '''
        nExpt = 1000
        grandFreq = {}
        for freq in range(nPubs+1):
            grandFreq[freq] = 0
        for i in range(nExpt):
            whole = []
            for p in range(nPubs):
                r = self.select(uniqInst, int(instPerPub) )
                whole.extend(r)
            freqShow = self.fillFreqShow(uniqInst,whole)

            for freq in freqShow:
                nold = grandFreq[freq]
                n = len(freqShow[freq])
                grandFreq[freq] = nold + n

        print('authorStats.expected For',nExpt,'expts, frequency/inst assuming',int(instPerPub),'institutions must review each pub')
        tot = 0
        for freq in grandFreq: tot += grandFreq[freq]
        print('{:>8} {:>8} {:>12}'.format('Freq','Number','Probability'))
        for freq in grandFreq:
            if grandFreq[freq]>0: print('{:>8} {:>8} {:>12.4f}'.format(freq,grandFreq[freq],(grandFreq[freq])/float(tot)))
        return
    def select(self,list,n):
        '''
        return n unique items from list without replacement
        '''
        if self.debug>2: print('authorStats.select n',n,'list',list)
        return numpy.random.choice(list,n,replace=False)
    def main(self):
        pubInfo = self.reader(self.dataFile)
        self.processStats(pubInfo)
        return
if __name__ == '__main__' :
    ss = authorStats()
    ss.main()

        
