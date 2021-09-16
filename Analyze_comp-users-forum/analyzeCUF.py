#!/usr/bin/env python
'''
analyze archive information from comp-users-forum
20210916
'''
#import math
import sys,os
import glob
#import csv
#import operator
#import xlrd
#import copy


#from collections import Counter

#import datetime


class analyzeCUF():
    def __init__(self):

        print 'analyzeCUF.__init__'
        
        self.debug = 0 + 1

        self.DATA_DIR = 'DATA/'

        self.MLname = 'comp-users-forum'
        
        self.archive = None
        
        return
    def getArchive(self):
        '''
        return ordered list of files in archive
        use sorted to make sure DATA/comp-users-forum_2021-07/10 is after DATA/comp-users-forum_2021-07/2
        '''
        files = glob.glob(self.DATA_DIR + '*/*')
        files.sort()
        f = sorted(files, key=lambda X : X.split('_')[1].split('/')[0]+str(float(X.split('/')[2])/10000))
        return f
    def filter(self,line,favorites):
        '''
        return keyword if line satisfies requirements in dict favorites[keyword]
        otherwise return None

        dict :  {keyword : [required index,required string1]}

        '''
        for key in favorites:
            OK = key in line
            if OK:
                OK = line.index(key)==favorites[key][0]
                if OK:
                    for s in favorites[key][1:]:
                        #print 'analyzeCUF.filter s,line[:-1]',s,line[:-1]
                        OK = OK and (s in line)
            if OK: return key
        return None
    def processFiles(self,files):
        '''
        process files. Each file is one entry in the archive
        '''

        favorites = {'Subject:' : [0, self.MLname]} # {keyword : [required index,required string1]}

        ignoreAfterThis = ['Begin forwarded message:']
        
        for fn in files:
            i = fn.index(self.MLname) + len(self.MLname) + 1
            archive = fn[i:]
            f = open(fn,'r')
            lines = f.readlines()
            f.close()
            
            last = len(lines)
            iline = 0
            while iline<last:
                line = lines[iline]
                if any([(s in line) for s in ignoreAfterThis]) :
                    iline = last
                else:
                    key = self.filter(line,favorites)
                    if key is not None:
                        nextline = ''
                        if iline<last:
                            iline += 1
                            nextline = lines[iline][:-1]
                        if self.debug > 0:
                            print 'analyzeCUF.processFiles archive,line[:-1]',archive,line[:-1],nextline
                    iline += 1
            
                                
                        
        return
    def main(self):
        '''
        main module for analysis
        '''
        files = self.getArchive()
        self.processFiles(files)
if __name__ == '__main__' :

    ss = analyzeCUF()
    ss.main()
    
