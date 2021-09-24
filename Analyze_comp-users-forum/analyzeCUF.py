#!/usr/bin/env python
'''
analyze archive information from comp-users-forum
20210916
'''
#import math
import sys,os
import glob
import matplotlib.pyplot as plt
import numpy

import extractMsg   # extracts the email message from a file

#import operator

#import copy

#from collections import Counter

import datetime


class analyzeCUF():
    def __init__(self,debug=0,plotToFile=False):

        
        self.debug = debug
        self.plotToFile = plotToFile
        print 'analyzeCUF.__init__ debug',self.debug,'plotToFile',self.plotToFile

        self.extractMsg = extractMsg.extractMsg()

        self.figDir = 'FIGURES'

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
    def getMonth(self,s):
        '''
        return yyyy-mm = year and month of message specified by input string s
        '''
        y = s
        if self.MLname in y:
            y = self.getMessage(y)
        if '/' in y:
            i = y.index('/')
            y = y[:i]
        return y
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
    def getSpan(self,a1,a2):
        '''
        return span between two messages with keys a1, a2
        if a1 or a2 is not a valid key, print an error message and
        return -1 
        '''
        i1,i2 = -2,-1
        hdr = 'analyzeCUF.getSPAN ERROR'
        words = ''
        if a1 in self.msgOrder :
            i1 = self.msgOrder.index(a1)
        else:
            words += ' {} is not a valid message key.'.format(a1)
        if a2 in self.msgOrder :
            i2 = self.msgOrder.index(a2)
        else:
            words += ' {} is not a valid message key.'.format(a2)
        if len(words)>0 :
            print hdr,words
            return -1

        return abs(i1-i2)
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

        # establish threads.
        # first step is to use metadata (Message-id, References and In-Reply-To) to create threads.
        # second step is to merge neighboring threads with identical subjects
            ref     = favInFile[archive][jref['References:']]['References:']
            subject = favInFile[archive][jref['Subject:']]['Subject:']
            msgid   = favInFile[archive][jref['Message-ID:']]['Message-ID:']
            irt     = favInFile[archive][jref['In-Reply-To:']]['In-Reply-To:']

        ## 'clean' the subject line, this removes superfluous information in the subject.
        ## Note that cleaning can yield a zero-length string for the subject
            subject = self.cleanSubject(subject)

            arch0 = self.locateRef(Threads,irt,ref,archive,subject)
            if arch0 is None:    # could not find reference or irt, so make this first message in a thread
                Threads[archive] = [subject, [(archive,msgid,irt)] ]
            elif arch0 not in Threads:
                sys.exit('analyzeCUF:processFiles ERROR arch0 '+arch0+' not in Threads')
            else:
                Threads[arch0][1].append( (archive,msgid,irt) )

        ### try to merge neighboring threads with identical subjects
        Threads = self.mergeNeighbors(Threads)
        ### now merge interleaved threads
        Threads = self.mergeInterleaved(Threads)
                
        ### report on threads
        print '\nanalyzeCUF.processFiles   REPORT ON THREADS +++++++++++++++++++++++++++++++++++++++'
        print 'Total files',len(files),'Total threads',len(Threads)
        threadOrder = []
        ThreadSubjects = {}
        for archive in self.msgOrder:
            if archive in Threads:
                threadOrder.append(archive)
                subject = Threads[archive][0]
                ThreadSubjects[archive] = subject

                if subject=='' or subject==' ':
                    print archive,'Subject',Threads[archive][0],'has weird clean subject',subject
                
                alist = [a[0] for a in Threads[archive][1] ]   # list of message in archive
                span  =self.getSpan(alist[0],alist[-1])  # #messages between last,first message in thread
                tlen = len(alist)  # total length of thread
                
                if self.debug >-1 : print 'Thread',archive,'subject',subject,'length',tlen,'span',span,'entries',alist
                if self.debug > 0 : print 'Thread',archive,'Contents',Threads[archive]

        ### look for threads with identical 'clean' subjects
        print '\nanalyzeCUF.processFiles Check threads for identical',
        if self.debug>1: print 'or similar',
        print 'subjects. Span is the number of messages between the first message of two threads.'
        dupThreads = []
        dupIsNextThread = []
        for i,archive in enumerate(threadOrder):
            if archive in ThreadSubjects:
                s1 = ThreadSubjects[archive]
                dups,sims,dupspan = [],[],[]    # archive or message numbers of duplicates, similar, span between duplicate threads
                sdups, ssims = [],[] # subject of duplicates, similar messages
                
                for j,a in enumerate(threadOrder[i+1:]):
                    if a not in dupThreads:
                        if a!=archive:
                            s2 = ThreadSubjects[a]
                            if s1==s2 :
                                if a not in dupThreads: dupThreads.append(a)
                                if j==0: dupIsNextThread.append(a)
                                dups.append(a)
                                sdups.append(s2)
                                dupspan.append( self.getSpan(archive,a) )
                            if len(s1)>0 and len(s2)>0 and (s1 in s2 or s2 in s1) :
                                sims.append(a)
                                ssims.append(s2)
                if len(dups)>0 or (len(sims)>0 and self.debug>1) :
                    #print archive,dups,dupspan
                    words = '{0} {1} has {2} identical threads(span):'.format(archive,s1,len(dups))
                    fmt = " {}({}),"
                    for w1,w2 in zip(dups,dupspan): words += fmt.format(w1,w2)
                    if self.debug>1:
                        fmt  = ("{:>"+str(max([len(q) for q in sims])+1)+"}")*len(sims)
                        words += 'and {0} similar threads:' + fmt.format(*sims)
                        fmt  = ("{:>"+str(max([len(q) for q in ssims])+1)+"}")*len(ssims)
                        words += fmt.format(*ssims)
                    print words
                    #print archive,s1,'has',len(dups),'identical threads:',dups,sdups,'and',len(sims),'similar threads',sims,ssims
        print 'analyzeCUF.processFiles Found',len(dupThreads),'duplicates among',len(threadOrder),'threads.',len(dupIsNextThread),'of these duplicates are the NEXT thread'
             
        return Threads
    def analyzeThreads(self,Threads):
        '''
        analyze of dict Threads

        Threads[archive0] = [Subject0,[(archive0,msgid0,irt0), (archive1,msgid1,irt1) ,...] ]

        Number of message per thread
        Span of messages in thread
        Threads per month
        '''
        nFiles = self.nFiles # total number of messages in archive
        nThreads = len(Threads) # total number of threads among messages
        print '\nanalyzeCUF.analyzeThreads',nFiles,'total messages in archive with',nThreads,'threads identified'
        
        # list threads by subject, alphabetically
        print '\nanalyzeCUF.analyzeThreads list of threads by subject, alphabetically'
        for aT in sorted(Threads.items(), key=lambda v: v[1][0]):
            key = aT[0]
            Subject = Threads[key][0]
            print key,Subject
        
        msgPerT = [] # number of messages per thread
        spanPerT= [] # span of messages in thread
        tPerM   = {} # threads per month
        
        for archive in self.msgOrder:
            if archive in Threads:
                ym = self.getMonth(archive)
                if ym not in tPerM : tPerM[ym] = 0
                tPerM[ym] += 1
                msgIds = [x[0] for x in Threads[archive][1]]
                msgPerT.append( len(msgIds) )
                span = self.getSpan( msgIds[0],msgIds[-1] )
                spanPerT.append( span )

        # histograms
        for A,label in zip([msgPerT,spanPerT], ['Messages per thread', 'Span of messages in threads']):
            x1 = 0.5
            nbin = max(A)+1
            x2 = float(nbin) + x1
            Y = numpy.array(A)
            plt.hist(Y,nbin, range=[x1,x2] )
            plt.xlabel(label)
            median, mean, std, mx = numpy.median(Y), numpy.mean(Y), numpy.std(Y), numpy.max(Y)
            title = 'Median={:.2f}, Mean={:.2f}, stddev={:.2f}, max={:.2f}'.format(median,mean,std,mx)
            plt.title(title)
            print 'analyzeCUF.analyzeThreads',label,title

            plt.grid()
            self.showOrPlot(label)

        # plots
        title = 'Threads per month'
        x,y = [],[]
        xlims = [ sorted(tPerM)[0], sorted(tPerM)[-1] ]
        xlims[0] = xlims[0][:5]+'01'
        xlims[1] = xlims[1][:5]+'12'
        dtlims = [datetime.datetime.strptime(q,'%Y-%m') for q in xlims]
        for ym in sorted(tPerM):
            y.append( tPerM[ym] )
            dt = datetime.datetime.strptime(ym,'%Y-%m') # YYYY-MM
            x.append( dt )
        ax = plt.subplot(111)
        ax.bar(x,y)
        ax.set_xlim(dtlims)

        ax.xaxis_date()
        ax.set_title(title)
        ax.figure.autofmt_xdate(rotation=80)
        plt.grid()
        
        self.showOrPlot(title)
        
        
                
        return
    def mergeInterleaved(self,Threads):
        '''
        return dict newThreads with interleaved threads with identical subjects merged

        Let Li = list of message numbers from Thread Ti with Lij as the jth message in list Li, 
        then T1 is interleaved with T2, if L10< L2j < L1n for 0<=j<len(L2)

        Threads[archive0] = [Subject0,[(archive0,msgid0,irt0), (archive1,msgid1,irt1) ,...] ]

        Use 2 step procedure. 
        First loop through threads in order to create all the merged threads, 
        then add all the original threads that did not need to be merged
        '''
        newThreads = {}
        badThreads = []
        for i,a1 in enumerate(self.msgOrder):
            if a1 in Threads:
                S1 = Threads[a1][0]
                limits = []
                for j in [0,-1]:  # get index of first,last message number
                    A = Threads[a1][1][j][0]
                    if A in self.msgOrder:
                        jx = self.msgOrder.index(A)
                    else:
                        print 'analyzeCUF.mergeInterleaved ERROR j,A',j,A,'not in self.msgOrder for a1,Threads[a1]',a1,Threads[a1]
                        jx = 0
                    limits.append(jx)
                for a2 in self.msgOrder[i+1:]:
                    if a2 in Threads:
                        S2 = Threads[a2][0]
                        if S2==S1:
                            jx = self.msgOrder.index(a2)
                            A0 = Threads[a1][1][0][0]
                            An = Threads[a1][1][-1][0]
                            if self.debug > 2 : print 'analyzeCUF.mergeInterleaved a1,S1,limits,A0,An,a2,jx',a1,S1,limits,A0,An,a2,jx,'Interleaved=',limits[0]<jx<limits[1]
                            if limits[0]<jx<limits[1]:
                                if a1 in newThreads: print 'analyzeCUF.mergeInterleaved ERROR Overwriting newThreads for key',a1
                                newThreads[a1] = Threads[a1]
                                newThreads[a1][1].extend( Threads[a2][1] )
                                badThreads.append( a2 )
        if self.debug > 2 : print 'analyzeCUF.mergeInterleaved badThreads',badThreads,'keys in newThreads',[key for key in sorted(newThreads)]
        for a1 in Threads:
            if a1 not in badThreads and a1 not in newThreads: newThreads[a1] = Threads[a1]
        print 'analyzeCUF.mergeInterleaved',len(Threads),'input Threads,',len(newThreads),'output Threads, so',len(badThreads),'were merged.'
        return newThreads
    def mergeNeighbors(self,Threads):
        '''
        return dict newThreads with neighboring threads with identical subjects merged

        Threads[archive0] = [Subject0,[(archive0,msgid0,irt0), (archive1,msgid1,irt1) ,...] ]
        '''
        newThreads = {}
        lastA,lastSubject = None,None
        for archive in self.msgOrder:
            if archive in Threads:
                if self.debug > 2 : print 'ananlyzeCUF.mergeNeighbors archive,lastA',archive,lastA
                Subject = Threads[archive][0]
                if lastA is None:
                    newThreads[archive] = Threads[archive]
                else:
                    if lastSubject==Subject:
                        newThreads[lastA][1].extend( Threads[archive][1] )
                    else:
                        newThreads[archive] = Threads[archive]
                lastA = archive
                lastSubject = Subject
        print 'analyzeCUF.mergeNeighbors',len(Threads),'initial threads and',len(newThreads),'after merge. So',len(Threads)-len(newThreads),'were merged.'
        return newThreads                        
    def locateRef(self,Threads,irt,ref,archive,subj):
        '''
        return key of Threads such that msgid of Threads[key] is found in irt (=In-Response-To), 
        if nothing in irt, then try ref (=References)
        archive is the message identifier that contains ref
        check if there are multiple keys that satisfy this requirement.
        Note that input subj is only used for print statements and not or locating the reference of the input message. 

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

    def showOrPlot(self,words):
        '''
        show plot interactively or put it in a file

        and clear plot after showing or drawing
        '''

        if self.plotToFile:
            filename = self.titleAsFilename(words)
            pdf = self.figDir + '/' + filename + '.pdf'
            plt.savefig(pdf)
            print 'analyzeCUF.showOrPlot Wrote',pdf
            plt.close() # avoid runtime warning?
        else:
            plt.show()
        plt.clf()
        return
    def titleAsFilename(self,title):
        '''
        return ascii suitable for use as a filename
        list of characters to be replaced is taken from https://stackoverflow.com/questions/4814040/allowed-characters-in-filename
        '''
        r = {'_': [' ', ',',  '\\', '/', ':', '"', '<', '>', '|'], 'x': ['*']}
        filename = title
        filename = ' '.join(filename.split()) # substitutes single whitespace for multiple whitespace
        for new in r:
            for old in r[new]:
                if old in filename : filename = filename.replace(old,new)
        return filename    
    def main(self):
        '''
        main module for analysis
        '''
        files,msgOrder = self.getArchive()
        self.msgOrder = msgOrder
        self.nFiles   = len(files)
        if self.debug > 2 : print 'analyzeCUF.main self.msgOrder',self.msgOrder
        Threads = self.processFiles(files)
        self.analyzeThreads(Threads)
if __name__ == '__main__' :

    debug = -1
    plotToFile = False

    if len(sys.argv)>1 :
        w = sys.argv[1]
        if 'help' in w.lower():
            print 'USAGE:    python analyzeCUF.py [debug] [plotToFile] '
            print 'DEFAULTS: python analyzeCUF.py',debug,plotToFile
            sys.exit('help was provided. use it')
    if len(sys.argv)>1 : debug = int(sys.argv[1])
    if len(sys.argv)>2 : plotToFile = bool(sys.argv[2])
    
    aCUF = analyzeCUF(debug=debug,plotToFile=plotToFile)
    aCUF.main()
    
