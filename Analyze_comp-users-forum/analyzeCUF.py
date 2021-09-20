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
        
        self.debug = 0 

        self.DATA_DIR = 'DATA/'

        self.MLname = 'comp-users-forum'
        
        self.msgOrder= None    # messages in proper numerical order
        
        return
    def getArchive(self):
        '''
        return ordered list of files in archive and ordered list of message numbers
        use sorted to make sure DATA/comp-users-forum_2021-07/10 is after DATA/comp-users-forum_2021-07/2
        '''
        files = glob.glob(self.DATA_DIR + '*/*')
        files.sort()
        f = sorted(files, key=lambda X : X.split('_')[1].split('/')[0]+str(float(X.split('/')[2])/10000))
        msgOrder = []
        for fn in f:
            msgN = self.getMessageN(fn)
            msgOrder.append(msgN)
        return f,msgOrder
    def filter(self,line,favorites):
        '''
        return keyword,key2 if line satisfies requirements in dict favorites[keyword], key2 is keyword as found
        otherwise return None,None

        dict :  {keyword : [required index,required string1,...,directive]}
        where directive can be 'lastLowerN' where N is the number of characters 
        at the end of the string to be checked for a match as lower case
        '''
        for key in favorites:
            key2 = key
            i,n = 1,0
            if 'lastLower' in favorites[key][-1]: n = int(favorites[key][-1][-1])
            found = key2 in line
            while not found and i<=n:
                key2 = key2[:-i] + key2[-i:].lower()
                found = key2 in line
                i += 1
            OK = found

            if OK:
                OK = line.index(key2)==favorites[key][0]
                if OK:
                    for s in favorites[key][1:-1]:
                        if self.debug > 2 : print 'analyzeCUF.filter s,line[:-1]',s,line[:-1]
                        OK = OK and (s in line)
            if OK:
                if self.debug > 2 : print 'analyzeCUF.filter key,line[:-1]',key,line[:-1]
                return key,key2
        return None,None
    def getMessageN(self,fn):
        '''
        extract message number from file name fn
        '''
        i = fn.index(self.MLname) + len(self.MLname) + 1
        archive = fn[i:]   # = yyyy-mm/msg#
        return archive
    def cleanSubject(self,subject):
        '''
        clean up subject line by removing every speck of dirt
        at some point the "[comp-users-forum]" inserted in every subject was 
        changed to "[comp-users-forum:nnnn]" where nnnn is the sequential message number.
        clean this up, too.
        '''
        ml = '['+self.MLname+']'
        dirt = [ml, '[SPAM]', 'Re:', 'Fwd:']

        
        s = subject
        for speck in dirt:
            s = s.replace(speck,'')

        mll = '['+self.MLname+':'
        mlr = ']'
        i1,i2 = len(s),0
        if mll in s: i1 = s.index(mll)
        if mlr in s: i2 = s.index(mlr)
        if i2>i1 : s = s[:max(i1-1,0)] + s[i2+1:]
            
        s = s.strip()
        if self.debug > 2 : print 'analyzeCUF.cleanSubject Original subject',subject,'Final subject',s
        return s
    def processFiles(self,files):
        '''
        process files. Each file is one entry in the archive.
        collect threads in dict. Threads[archive0] = [Subject0,[(archive0,msgid0,irt0), (archive1,msgid1,irt1) ,...] ]
        where archive0 is the message identifier of the form yyyy-mm/N for message#N,
        msgid0 = Message-Id0 = Message-Id for archive0. Subsequent messages with Message-Id in References are part of the thread
        irt0 = In-Response-To for archive0
        Subject0    = Subject for archive0

        References for processing
        Thread identification: https://www.mhonarc.org/MHonArc/doc/faq/threads.html
        '''

        favorites = {'Subject:' : [0, self.MLname,'noRequirement'],
                         'References:' : [0,'noRequirement'],
                         'In-Reply-To:': [0,'noRequirement'],
                         'Message-ID:' : [0,'lastLower3'],
                         } # {keyword : [required index,required string1]}
        jref = {}
        for j,key in enumerate(sorted(favorites)): jref[key] = j

        ignoreAfterThis = ['Begin forwarded message:']

        favPerFile = {} # favPerFile[archive] = [ {key1:instances1}, {key2:instances2},...] where key1 is a key in favorites and instances are the number of instances of the key in the file referenced by archive
        favInFile  = {} # favPerFile[archive] = [ {key1:content1}, {key2:content2} ] same as favPerFile except content is recorded for the first instance of key
        Threads = {}
        
        for fn in files:
            archive = self.getMessageN(fn) # = yyyy-mm/msg#
            if self.debug > 0 : print 'analyzeCUF.processFiles archive',archive
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
                    key,key2 = self.filter(line,favorites)
                    if key is not None:
                        
                        if archive not in favPerFile:
                            favPerFile[archive] = [{K:0} for K in sorted(favorites)]
                            favInFile[archive]  = [{K:''} for K in sorted(favorites)]
                            favPerFile[archive][jref[key]][key] += 1

                        content = line[:-1].replace(key2,'').lstrip()
                        while iline<last and lines[iline+1][0]==' ':
                            iline += 1
                            content += lines[iline][:-1]

                        content = content.strip() # remove leading and trailing spaces
                        j = jref[key]
                        if favInFile[archive][j][key]=='' : favInFile[archive][j][key] = content
                            
                        if self.debug > 1:
                            print 'analyzeCUF.processFiles archive,key,content,`content`',archive,key,content,`content`
                        
                    iline += 1
            
            if archive in favPerFile:
                if self.debug > 2 :
                    print 'analyzeCUF.processFiles archive,favPerFile[archive]',archive,favPerFile[archive]
                    print 'analyzeCUF.processFiles archive,favInFile[archive]',archive,favInFile[archive]
            else:
                print 'analyzeCUF.processFiles WARNING archive',archive,'No favorites found'

        # establish threads
            ref     = favInFile[archive][jref['References:']]['References:']
            subject = favInFile[archive][jref['Subject:']]['Subject:']
            msgid   = favInFile[archive][jref['Message-ID:']]['Message-ID:']
            irt     = favInFile[archive][jref['In-Reply-To:']]['In-Reply-To:']

            arch0 = self.locateRef(Threads,irt,ref,archive,subject)
            if arch0 is None:    # could not find reference or irt, so make this first message in a thread
                Threads[archive] = [subject, [(archive,msgid,irt)] ]
            elif arch0 not in Threads:
                sys.exit('analyzeCUF:processFiles ERROR arch0 '+arch0+' not in Threads')
            else:
                Threads[arch0][1].append( (archive,msgid,irt) )

        ### report on threads
        print '\nanalyzeCUF.processFiles   REPORT ON THREADS +++++++++++++++++++++++++++++++++++++++'
        print 'Total files',len(files),'Total threads',len(Threads)
        threadOrder = []
        ThreadSubjects = {}
        for archive in self.msgOrder:
            if archive in Threads:
                threadOrder.append(archive)
                subject = Threads[archive][0]
                subject = self.cleanSubject(subject)
                ThreadSubjects[archive] = subject

                if subject=='' or subject==' ':
                    print archive,'Subject',Threads[archive][0],'has weird clean subject',subject
                
                alist = [a[0] for a in Threads[archive][1] ]   # list of message in archive
                sep   = [self.msgOrder.index(a[0]) for a in Threads[archive][1] ] # indices of message in archive in list
                span  = max(sep) - min(sep)  # #messages between last,first message in thread
                tlen = len(alist)  # total length of thread
                
                if self.debug >-1 : print 'Thread',archive,'subject',subject,'length',tlen,'span',span,'entries',alist
                if self.debug > 0 : print 'Thread',archive,'Contents',Threads[archive]

        ### look for threads with identical 'clean' subjects
        print '\nanalyzeCUF.processFiles Check threads for identical or similar subjects'
        dupThreads = []
        dupIsNextThread = []
        for i,archive in enumerate(threadOrder):
            if archive in ThreadSubjects:
                s1 = ThreadSubjects[archive]
                dups,sims = [],[]
                sdups, ssims = [],[]
                
                for j,a in enumerate(threadOrder[i+1:]):
                    if a not in dupThreads:
                        if a!=archive:
                            s2 = ThreadSubjects[a]
                            if s1==s2 :
                                if a not in dupThreads: dupThreads.append(a)
                                if j==0: dupIsNextThread.append(a)
                                dups.append(a)
                                sdups.append(s2)
                            if len(s1)>0 and len(s2)>0 and (s1 in s2 or s2 in s1) :
                                sims.append(a)
                                ssims.append(s2)
                if len(dups)>0 or (len(sims)>0 and self.debug>1) :
                    print archive,s1,'has',len(dups),'identical threads:',dups,sdups,'and',len(sims),'similar threads',sims,ssims
        print 'analyzeCUF.processFiles Found',len(dupThreads),'duplicates among',len(threadOrder),'threads.',len(dupIsNextThread),'of these duplicates are the NEXT thread'
             
        return
    def locateRef(self,Threads,irt,ref,archive,subj):
        '''
        return key of Threads such that msgid of Threads[key] is found in irt (=In-Response-To), 
        if nothing in irt, then try ref (=References)
        archive is the message identifier that contains ref
        check if there are multiple keys that satisfy this requirement

        Threads[archive0] = [Subject0,[(archive0,msgid0,irt0), (archive1,msgid1,irt1) ,...] ]
        '''
        if self.debug > 1 : print 'analyzeCUF.locateRef: inputs archive, subj, irt, ref',archive, subj, irt, ref

        irtMatchedKeys = []
        refMatchedKeys = []
        keysInSearch   = []
        for key in self.msgOrder: # 
            if key in Threads:
                keysInSearch.append(key)
                for tupl in Threads[key][1]:
                    archN,msgidN,irtN = tupl
                    if msgidN in irt:
                        if key not in irtMatchedKeys: irtMatchedKeys.append(key)
                    if msgidN in ref:
                        if key not in refMatchedKeys: refMatchedKeys.append(key)
        if self.debug > 2 : print 'analyzeCUF.locateRef: keysInSearch',keysInSearch
        
        matchedKeys = irtMatchedKeys
        matchby = ('irt',irt)
        if len(matchedKeys)==0:
            matchedKeys = refMatchedKeys
            matchby = ('ref',ref)
                        
        L = len(matchedKeys)
        if L==0:
            if self.debug > 0 : print 'analyzeCUF.locateRef NO MATCH archive,irt,ref',archive,irt,ref
            key = None
        elif L==1:
            key = matchedKeys[0]
        else:
            w,x = matchby
            if self.debug > 0 : 
                print 'analyzeCUF.locateRef',L,'matches for archive,subj,',w,',(key,msgid) pairs',archive,subj,x,'matching keys follow:'
                print 'analyzeCUF.locateRef matchedKeys',matchedKeys
            key = matchedKeys[0]
        return key
    def main(self):
        '''
        main module for analysis
        '''
        files,msgOrder = self.getArchive()
        self.msgOrder = msgOrder
        if self.debug > 2 : print 'analyzeCUF.main self.msgOrder',self.msgOrder
        self.processFiles(files)
if __name__ == '__main__' :

    ss = analyzeCUF()
    ss.main()
    
