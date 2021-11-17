#!/usr/bin/env python
'''
analyze archive information from comp-users-forum

base initial analysis on mimicing results in Michel's
https://indico.belle2.org/event/4490/contributions/23141/attachments/11560/17627/userAnalysis_b2gm_jun2021.pdf

20210916
'''
import sys,os
import glob
import matplotlib.pyplot as plt
import numpy

import extractMsg   # extracts the email message from a file
import issues_keyphrases  # classifies threads based on subject and message content
import mpl_interface # interface to mathplotlib
import Logger # direct stdout to file & terminal

import email

import datetime


class analyzeCUF():
    def __init__(self,debug=0,plotToFile=False):
        
        self.debug = debug
        self.plotToFile = plotToFile

        now = datetime.datetime.now()
        self.now = now.strftime('%Y%m%dT%H%M%S')

        parentDir = 'JOBS/'+self.now
        dirs = [parentDir]
        self.figDir = parentDir  + '/FIGURES'
        self.logDir = parentDir
        dirs.append( self.figDir)
        dirs.append( self.logDir)

        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)
                print 'analyzeCUF.__init__ create directory',d

        lf = self.logDir + '/logfile.log'
        sys.stdout = Logger.Logger(fn=lf)
        print 'analyzeCUF.__init__ Output directed to stdout and',lf


        print 'analyzeCUF.__init__ debug',self.debug,'plotToFile',self.plotToFile,'now',self.now

        self.extractMsg = extractMsg.extractMsg(debug=debug)
        self.issues_keyphrases = issues_keyphrases.issues_keyphrases(debug=debug,now=self.now)
        self.mpl_interface = mpl_interface.mpl_interface()

        self.DATA_DIR = 'DATA/'

        self.MLname = 'comp-users-forum'
        
        self.msgOrder= None    # messages in proper numerical order

        self.ADB = {} # Address DataBase ADB[ad0] = [ [ad0,name0], [ad1,name1], ...]

        # prime address database with persons with problematic address,name combos
        self.ADB['jvbennet@olemiss.edu'] =  [
            ['jvbennet@olemiss.edu', 'jvbennet'],
            ['jvbennet@olemiss.edu', 'Jake V Bennett'],
            ['jvbennett@cmu.edu', 'Jake Bennett'],
            ['jbennett@phy.olemiss.edu', 'Jake Bennett']]
        self.ADB['mattb@post.kek.jp'] =  [
            ['mattb@post.kek.jp', 'Matt Barrett'], 
            ['matthew.barrett2@wayne.edu', 'Matthew Barrett']]
        self.ADB['racha.cheaib@desy.de'] =  [
            ['racha.cheaib@desy.de', 'RachaWork'],
            ['racha.chouiab@mail.mcgill.ca', 'Racha Chouiab, Miss'],
            ['rcheaib@olemiss.edu', 'rcheaib'],
            ['rcheaib@phas.ubc.ca', 'Cheaib, Racha'],
            ['rachac@mail.ubc.ca', 'Cheaib, Racha']]
        self.ADB['sam.cunliffe@desy.de'] =[
            ['sam.cunliffe@desy.de', 'Sam Cunliffe'],
            ['samuel.cunliffe@pnnl.gov', 'Cunliffe, Samuel T']]
        self.ADB['kato@hepl.phys.nagoya-u.ac.jp'] = [
            ['kato@hepl.phys.nagoya-u.ac.jp', 'Yuji Kato'],
            ['kato@hepl.phys.nagoya-u.ac.jp', ''],
            ['kato@hepl.phys.nagoya-u.ac.jp', 'Yuji kato'],
            ['katouyuuji@gmail.com', '=?UTF-8?B?5Yqg6Jek5oKg5Y+4?=']]

        
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

        ref:
        https://stackoverflow.com/questions/8270092/remove-all-whitespace-in-a-string
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
            
        s = " ".join(s.split())
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
    def getAddr(self,whoFrom):
        '''
        return email address and name from contents of email 'From' field 
        example: if usual content is 'Name <name@place>', then return name@place, Name

        '''
        if '<' not in whoFrom:
            if '@' in whoFrom:
                ad = whoFrom.strip()
                name = ad
            else:
                sys.exit('analyzeCUF.getAddr INVALID CONTENT From='+whoFrom)
        else:
            s = whoFrom.split('<')
            ad = s[1].replace('>','')
            name = s[0].replace('"','').strip()
        return ad,name
    def fillADB(self,whoFrom):
        '''
        fill address database and return best email address based on content of 'From' field
        best email address is the first email address encountered for a user with multiple 'From' field content
        self.ADB = {} is the Address DataBase where
        self.ADB[ad0] = [ [ad0,name0], [ad1,name1], ...]
        ad0,name0 = first address,name encountered
        ad1,name1 = second address,name encountered

        when trying to associate different whoFrom content, 
        require a match of the addresses or the names or the part of the address before '@'
        '''
        adOut = None # should get assigned below
        ad,name = self.getAddr(whoFrom)
        adB = ad.split('@')[0]
        if self.debug > 2 : print 'analyzeCUF.fillADB input whoFrom,ad,name,adB',whoFrom,ad,name,adB,'len(self.ADB)',len(self.ADB)
        if ad in self.ADB:
            adOut = ad
            found = False
            for pair in self.ADB[ad]:
                adX,nameX = pair
                if adX==ad and nameX==name : found = True
            if not found: self.ADB[ad].append( [ad,name] )
        else:
            done = False
            for key in self.ADB:
                new = []
                for pair in self.ADB[key]:
                    adX,nameX = pair
                    if adX==ad or adX.split('@')[0]==adB or nameX==name:
                        adOut = key
                        new.append( [ad,name] )
                        done = True
                        break

                if done:
                    if len(new)>0 and new[0] not in self.ADB[key]: self.ADB[key].extend( new )
                    break
            if not done:
                adOut = ad
                if ad not in self.ADB : self.ADB[ad] = [ [ad,name] ]
        if adOut is None:
            print 'analyzeCUF.fillADB ERROR adOut',adOut,'whoFrom',whoFrom,'ad,name',ad,name,'self.ADB follows\n',self.ADB
            sys.exit('analyzeCUF.fillADB ERROR adOut in None')
        if self.debug > 2 : print 'analyzeCUF.fillADB output whoFrom,adOut',whoFrom,adOut,'len(self.ADB)',len(self.ADB)
        return adOut
    def reportADB(self):
        '''
        write contents of ADB to terminal
        '''
        print '\nanalyzeCUF.reportADB Contents of Address DataBase'
        for key in sorted(self.ADB):
            print key,self.ADB[key]
        print '\n'
        return
    def threadIdentifiers(self,fn):
        '''
        return dict threadIds from email filename fn

        According to Thread identification: https://www.mhonarc.org/MHonArc/doc/faq/threads.html,
         The References field is normally utilized by news software, 
         while In-Reply-To is normally utilized be e-mail software.
        '''
        IRT = 'In-Reply-To'
        REF = 'References'
        blank = ''
        identifiers = ['Subject',IRT,'Message-id',REF,'From']
        threadIds = {}
        f = open(fn,'r')
        msg = email.message_from_file(f)
        f.close()
        for key in identifiers:
            threadIds[key] = blank
            if key in msg:
                words = msg[key]
                if key=='Subject': words = self.cleanSubject(msg[key])
                threadIds[key] = words
        threadHead = (threadIds[IRT] is blank) and (threadIds[REF] is blank)
        return threadIds,threadHead
    def buildThreads(self,files):
        '''
        do a better job of building threads from ordered list of files

        Define start of thread as a message that has no In-Reply-To or References field.

        Threads[archive0] = [Subject0,[(archive0,msgid0,irt0,from0), (archive1,msgid1,irt1,from1) ,...] ]
        '''
        

        Threads = {}
        

        for fn in files:
            fileIds,threadStart = self.threadIdentifiers(fn)
            archive = self.getMessageN(fn) # = yyyy-mm/msg#
            Subject = fileIds['Subject']
            msgid   = fileIds['Message-id']
            irt     = fileIds['In-Reply-To']
            whoFrom = fileIds['From']
            whoFrom = self.fillADB(whoFrom) 
            ref     = fileIds['References']
            if  threadStart :
                Threads[archive] = [fileIds['Subject'], [(archive,msgid,irt,whoFrom)]]
            else:
                key = self.findParent(archive,fileIds, Threads)
                if key is None:
                    self.debug = 1
                    key = self.locateRef(Threads, irt,ref,archive,Subject)
                    self.debug = 0

                if key is None :
                    Threads[archive] = [Subject, [ (archive,msgid,irt,whoFrom) ] ]
                elif key not in Threads:
                    sys.exit('analyzeCUF:buildThreads ERROR arch0 '+arch0+' not in Threads')
                else:
                    Threads[key][1].append( (archive,msgid,irt,whoFrom) )

        
        return
    def findParent(self,archive,fileIds, Threads):
        '''
        Return key of Threads that is parent of archive,fileIds;
        else return NOne

        Assign msg identified by archive and fileIds to thread in Threads

        if parent Message-id is in (daughter In-Reply-To list or daughter References list) and 
        parent Subject is in daughter subject, then assign daughter to parent

        '''
        dautSubject = fileIds['Subject']
        dautIRT     = fileIds['In-Reply-To']
        dautREF     = fileIds['References']
        dautFrom    = fileIds['From']
        dautMsgid   = fileIds['Message-id']
        daughter = (archive, dautMsgid, dautIRT, dautFrom )
        
        for key in Threads:
            parentSubject = Threads[key][0]
            parentMsgid   = Threads[key][1][0][1] # = [(archive0,msgid0,irt0,from0), (archive1,msgid1,irt1,from1) ,...]
            if parentMsgid in dautIRT or parentMsgid in dautREF:
                if self.matchSubjects(parentSubject,dautSubject):
                    Threads[key][1].append( daughter )
                    status = 0
                    return key 
                
        return None
        
    def matchSubjects(self,parentSubject,dautSubject):
        '''
        return True if parentSubject and dautSubject match

        match = parentSubject in dautSubject
        OR
        match = partial match of pS and dS when bogus string in both pS and dS
        '''
        if parentSubject in dautSubject : return True
            
        bogus = '?='
        if bogus in parentSubject and bogus in dautSubject:
            jp,jd = parentSubject.index(bogus), dautSubject.index(bogus)
            if jp>=len(parentSubject)/2 and jd>=len(dautSubject)/2 :
                if parentSubject[:jp] in dautSubject[:jd]: return True
                    
        return False
    def processFiles(self,files):
        '''
        process files. Each file is one entry in the archive.
        collect threads in dict. 
        Threads[archive0] = [Subject0,[(archive0,msgid0,irt0,from0), (archive1,msgid1,irt1,from1) ,...] ]
        where archive0 is the message identifier of the form yyyy-mm/N for message#N,
        msgid0 = Message-Id0 = Message-Id for archive0. Subsequent messages with Message-Id in References are part of the thread
        irt0 = In-Response-To for archive0
        Subject0    = Subject for archive0
        from0 = From for archive0

        References for processing
        Thread identification: https://www.mhonarc.org/MHonArc/doc/faq/threads.html
        '''

        # define favorite keys and instructions
        # jref[key] is the index of key in order of sorted keys
        favorites = {'Subject' : [0, self.MLname,'noRequirement'],
                         'References' : [0,'noRequirement'],
                         'In-Reply-To': [0,'noRequirement'],
                         'Message-ID' : [0,'lastLower3'],
                         'From' : [0,'noRequirement']
                         } # {keyword : [required index,required string1]}
        jref = {}
        for j,key in enumerate(sorted(favorites)):
            jref[key] = j


        ignoreAfterThis = ['Begin forwarded message:']


        favInFile  = {} # favInFile[archive] = [ {key1:content1}, {key2:content2} ] same as key1 is a key in favorites and content is recorded for the first instance of key
        Threads = {}
        
        for fn in files:
            archive = self.getMessageN(fn) # = yyyy-mm/msg#
            if self.debug > 0 : print 'analyzeCUF.processFiles archive',archive
            f = open(fn,'r')
            msg = email.message_from_file(f)
            f.close()

            if self.debug > 1 : print 'analyzerCUF.processFiles archive',archive,'msg.keys()',msg.keys()

            for key in favorites:
                favLow = key.lower()
                for msgKey in msg.keys():
                    if msgKey.lower() == favLow:
                        content = msg[msgKey]
                        content = content.strip() # remove leading and trailing spaces
                        
                        if archive not in favInFile: # initialization of dicts, increment favInFile
                            favInFile[archive]  = [{K:''} for K in sorted(favorites)]

                        j = jref[key]
                        if favInFile[archive][j][key]=='' : favInFile[archive][j][key] = content
            
            if archive in favInFile:
                if self.debug > 2 :
                    print 'analyzeCUF.processFiles archive,favInFile[archive]',archive,favInFile[archive]
            else:
                print 'analyzeCUF.processFiles WARNING archive',archive,'No favorites found'

        # establish threads.
        # first step is to use metadata (Message-id, References and In-Reply-To) to create threads.
        # as part of first step, create a database of email addresses and names from the 'From' content of each message. alter the 'From' content to be an email address. Try to make the email address unique by tracking all addresses used by the same individual. 
        # second step is to merge neighboring threads with identical subjects
        
            ref     = favInFile[archive][jref['References']]['References']
            subject = favInFile[archive][jref['Subject']]['Subject']
            msgid   = favInFile[archive][jref['Message-ID']]['Message-ID']
            irt     = favInFile[archive][jref['In-Reply-To']]['In-Reply-To']
            whoFrom = wF0 = favInFile[archive][jref['From']]['From']
            whoFrom = wF1 = self.fillADB(whoFrom)
            if self.debug>2 and wF0!=wF1 :
                print 'analyzeCUF.processFiles initial whoFrom',wF0,'final whoFrom',wF1

        ## 'clean' the subject line, this removes superfluous information in the subject.
        ## Note that cleaning can yield a zero-length string for the subject
            subject = self.cleanSubject(subject)

            arch0 = self.locateRef(Threads,irt,ref,archive,subject)
            if arch0 is None:    # could not find reference or irt, so make this first message in a thread
                Threads[archive] = [subject, [(archive,msgid,irt,whoFrom)] ]
            elif arch0 not in Threads:
                sys.exit('analyzeCUF:processFiles ERROR arch0 '+arch0+' not in Threads')
            else:
                Threads[arch0][1].append( (archive,msgid,irt,whoFrom) )

        ### report address database?
        if self.debug > 1 : self.reportADB()
                
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
    def getArchiveList(self,archive,Threads):
        '''
        return archiveList = list of archives in Threads[archive]
        '''
        archiveList = None
        if archive in Threads:
            archiveList = [x[0] for x in Threads[archive][1]]
        else:
            print 'analyzeCUF.getArchiveList WARNING archive',archive,'is not a Thread key'
        return archiveList
    def analyzeThreads(self,Threads,issues,issueOrder,issueUnique,thread_issues,archiveDates):
        '''
        analyze dict Threads

        Threads[archive0] = [Subject0,[(archive0,msgid0,irt0,from0), (archive1,msgid1,irt1,from1) ,...] ]
        issues = {}         # {issue: [archive0, archive1, ...] } = list of threads for this issue
        issueOrder = list with issue names in order of analysis
        issueUnique= list of booleans, entry is true if issue is `Unique`
        thread_issues = {}  # {archive0: [issue1, issue2]} = how many issues assigned to each thread?
        archiveDates[archive] = date as datetime object 


        Number of message per thread
        Span of messages in thread
        Threads per month
        '''
        nFiles = self.nFiles # total number of messages in archive
        nThreads = len(Threads) # total number of threads among messages
        print '\nanalyzeCUF.analyzeThreads',nFiles,'total messages in archive with',nThreads,'threads identified'

        listThreads = False
        if listThreads : 
            # list threads by subject, alphabetically
            print '\nanalyzeCUF.analyzeThreads list of threads by subject, alphabetically'
            fn = 'threads'
            nwrite = 0
            f = open(fn,'w')
            for aT in sorted(Threads.items(), key=lambda v: v[1][0]):
                key = aT[0]
                Subject = Threads[key][0]
                words = '{} {}'.format(key,Subject)
                print words
                f.write(words+'\n')
                nwrite += 1
            f.close()
            print '\nanalyzeCUF.analyzeThreads Wrote',nwrite,'thread subjects to file',fn

        ### issue vs issue
        Ni = len(issueOrder)
        IvI = []
        for i in range(Ni): IvI.append( [0. for j in range(Ni)] )
        tot, above, below = 0,0,0
        for archive in thread_issues:
            iss = thread_issues[archive]
            i = issueOrder.index( iss[0] )
            IvI[i][i] += 1
            tot += 1
            if len(iss)>=2:
                j = issueOrder.index( iss[1] )
                IvI[j][j] += 1
                IvI[j][i] += 1
                above += 1
            if len(iss)==3:
                k = issueOrder.index( iss[2] )
                IvI[k][k] += 1
                IvI[i][k] += 1
                below += 1
        x = y = numpy.arange(Ni+1)
        z = numpy.array(IvI)
        xlabels = ylabels = issueOrder
        title = 'Issue vs issue. Diagonal=all, above=doubles, below=triples'
        Title = self.mpl_interface.plot2d(x,y,z,xlabels=xlabels,ylabels=ylabels,title=title,colorbar=True)
        self.showOrPlot(Title)
        print '\nanalyzeCUF.analyzeThreads',Title,'all,above,below',tot,above, below
            
        # issues by year
        # plot normed number of issues/year and issues/all years vs year 
        # and number of issues/year vs year (normed and unnormed)
        # and normed number of non-unique issues/year and issues/all years vs year
        # and normed, un-normed non-Annoucement issues/year, etc.
        # also report # issues/year in a table
        nonUniqueOrder,issueOrderNoAnnouncement = [],[]
        for I,issue in enumerate(issueOrder):
            if not issueUnique[I] : nonUniqueOrder.append(issue)
            if issue!=self.issues_keyphrases.announcementsName : issueOrderNoAnnouncement.append(issue)
                
        if self.debug > 2 :
            print '\nanalyzeCUF.analyzeThreads issues',issues
            print ' ',[str(issue)+' '+str(len(issues[issue])) for issue in issues]
        years = []
        for issue in issues:
            for archive in issues[issue]:
                year = archive[:4]
                if year not in years: years.append( year )
        years.append('AllYears')
        years = sorted(years)
        if self.debug > 2 : print 'analyzeCUF;analyzeThreads years',years
        iByY = {} # {year: [N(issue0), N(issue1), ...}
        for year in years:
            iByY[year] = [0 for issue in issueOrder]

        for I,issue in enumerate(issueOrder):
            for archive in issues[issue]:
                year = archive[:4]
                iByY[year][I] += 1
                iByY['AllYears'][I] += 1

        rows = []
        for I,issue in enumerate(issueOrder):
            onerow = []
            for year in years:
                onerow.append( iByY[year][I] )
            rows.append( onerow )
        table = self.tableMaker(years,rows,issueOrder,integers=True,caption='Number of issues by year')
        print table

        if self.debug > 2 : print 'analyzeCUF.analyzeThreads iByY',iByY

        for words,order in zip(['All ','Non-unique ','All but Announcements'],[issueOrder, nonUniqueOrder,issueOrderNoAnnouncement]):
            if self.debug > 1 : print '\nNumber of issues by year\n',' '.join(years),'Issue'
            Y = []
            Yy= []
            for I,issue in enumerate(order):
                NperY = []
                NperYy= []
                for year in years:
                    NperY.append( iByY[year][I] )
                    if year!='AllYears': NperYy.append( iByY[year][I] )
                if self.debug > 1 : print ' '.join(str(x) for x in NperY),issue
                Y.extend( NperY )
                Yy.extend( NperYy )
            X = numpy.array( years )
            Y = numpy.array( Y )
            Yy= numpy.array( Yy )
            Y = numpy.reshape( Y, (len(order), len(years)) )
            Yy= numpy.reshape( Yy, (len(order), len(years)-1) )
            Title = self.mpl_interface.stackedBarChart(Y,years,order,words+'Issues',norm=True)
            self.showOrPlot(Title)
            Title = self.mpl_interface.stackedBarChart(Yy,years[:-1],order,words+'Issues by year',norm=False)
            self.showOrPlot(Title)
            Title = self.mpl_interface.stackedBarChart(Yy,years[:-1],order,words+'Issues by year',norm=True)
            self.showOrPlot(Title)
        
        
        # analyze thread by reporter and responder by year
        # first 'From' is reporter, second 'From' is responder
        print '\nanalyzeCUF.analyzeThreads by reporter and responder'
        Reporters, Responders = {}, {}
        for archive in self.msgOrder:
            if archive in Threads:
                year = archive[:4]
                whoFrom = []
                for tupl in Threads[archive][1]:
                    whoFrom.append(tupl[3])
                rep,res = None,None
                if len(whoFrom)>0: rep = whoFrom[0]
                if len(whoFrom)>1: res = whoFrom[1]
                if year not in Reporters: Reporters[year], Responders[year]= [],[]
                Reporters[year].append(rep)
                Responders[year].append(res)
                if self.debug > 1 : print 'analyzeCUF.analyzeThreads archive',archive,'whoFrom',whoFrom
                if self.debug > 1 : print 'analyzeCUF.analyzeThreads archive',archive,'Reporter,Responder',rep,res
        if self.debug > 1 : print 'analyzeCUF.analyzeThreads Reporters',Reporters
        if self.debug > 1 : print 'analyzeCUF.analyzeThreads Responders',Responders

        ## create pie charts of reporters and responders per year
        ## reporters, responders identified by name in name@address
        ## allow 'None' as a possible reporter or responder
        dictReporters, dictResponders = {},{}
        for year in Reporters:
            dictReporters[year] = {i:Reporters[year].count(i) for i in Reporters[year]}
            dictResponders[year]= {i:Responders[year].count(i) for i in Responders[year]}
        for year in sorted(dictReporters):
            for name,DICT in zip(['Reporters','Responders'], [dictReporters,dictResponders] ):
                title = '{} {}'.format(name,year)
                counts,labels = [],[]
                for k,v in sorted(DICT[year].items(), key=lambda x:x[1]):
                    if k is not None:
                        label = k
                        if '@' in k: label = k.split('@')[0]
                        labels.append(label)
                        counts.append(v)
                    else:
                        labels.append( 'None' )
                        counts.append(v)
                plt.pie(counts,labels=labels)
                plt.axis('equal')
                plt.title(title,loc='left')
                self.showOrPlot(title)
            
            if self.debug > 1 :
                print 'analyzeCUF.analyzeThreads year',year,'dictReporters[year]',sorted(dictReporters[year].items(), key=lambda x:x[1], reverse=True)
                for k,v in sorted(dictReporters[year].items(), key=lambda x:x[1], reverse=True): print k,v
                print 'analyzeCUF.analyzeThreads year',year,'dictResponders[year]',sorted(dictResponders[year].items(), key=lambda x:x[1], reverse=True)
                for k,v in sorted(dictResponders[year].items(), key=lambda x:x[1], reverse=True): print k,v
        
        
        msgPerT    = [] # number of messages per thread
        spanPerT   = [] # span of messages in thread
        deltaTPerT = [] # time difference between earliest and latest message in thread
        dTPerT     = {x:[] for x in issueOrder} # dTPerT[issue] = [time difference between earliest, lastest msg in thread by issue, multiple issues/thread allowed
        niName = 'no issue'
        dTPerT[niName] = []
        aPerT      = [] # archive associated with previous lists
        tPerM   = {} # threads per month

        
        for archive in self.msgOrder:
            if archive in Threads:
                ym = self.getMonth(archive)
                if ym not in tPerM : tPerM[ym] = 0
                tPerM[ym] += 1 
                msgIds = [x[0] for x in Threads[archive][1]] # msgIds aka archive
                msgTime= [archiveDates[q] for q in msgIds]
                deltaT = (max(msgTime) - min(msgTime)).total_seconds()/60./60./24.# time difference in days
                deltaTPerT.append( deltaT )
                if archive not in thread_issues: # how does this happen
                    print 'analyzeCUF.analyzeThreads WARNING archive',archive,'not in thread_issues for Thread subject',Threads[archive][0]
                    dTPerT[niName].append( deltaT )
                else:
                    for issue in thread_issues[archive]:
                        dTPerT[issue].append( deltaT )
                msgPerT.append( len(msgIds) )
                span = self.getSpan( msgIds[0],msgIds[-1] )
                spanPerT.append( span )
                aPerT.append( archive )

        # print archive, deltaT for N largest deltaT
        N = 5
        dtLabel = 'Days between earliest and latest message in thread'
        print '\nanalyzeCUF.analyzeThreads Threads with the',N,'largest deltaT=',dtLabel
        for dt in sorted(deltaTPerT)[-N:]:
            i = deltaTPerT.index(dt)
            archive = aPerT[i]
            span    = spanPerT[i]
            nmsg    = msgPerT[i]
            fdt = '{:.2f}'.format(dt)
            print 'analyzeCUF.analyzeThreads archive,deltaT(days),span,nmsg',archive,fdt,span,nmsg
            archiveList = self.getArchiveList(archive,Threads)
            self.writeMsgs(archiveList,output='Thread_'+archive.replace('/','_')+'deltaT_'+fdt)
        print ''

        # histograms
        dtMax = None
        for A,label in zip([msgPerT,spanPerT,deltaTPerT], ['Messages per thread', 'Span of messages in threads',dtLabel]):
            x1 = 0.5
            nbin = max(A)+1
            x2 = float(nbin) + x1
            if 'Days' in label :
                x1 = 0.
                nbin = 100.
                x2 = max(A)+10.
                if label==dtLabel : dtMax = x2
            Y = numpy.array(A)
            median, mean, std, mx = numpy.median(Y), numpy.mean(Y), numpy.std(Y), numpy.max(Y)
            title = 'Median={:.2f}, Mean={:.2f}, stddev={:.2f}, max={:.2f}'.format(median,mean,std,mx)
            Title = self.mpl_interface.histo(Y,x1,x2,dx=1.,xlabel=label,title=title,grid=True)
            print 'analyzeCUF.analyzeThreads',label,title
            self.showOrPlot(label)
            
        # histograms for each issue
        for issue in dTPerT:
            A = dTPerT[issue]
            if len(A)>0:
                label = 'Days btwn earliest,latest msg in thread for '+issue
                x1 = 0.
                nbin = 100.
                x2 = dtMax
                Y = numpy.array(A)
                median, mean, std, mx = numpy.median(Y), numpy.mean(Y), numpy.std(Y), numpy.max(Y)
                title = 'Median={:.2f}, Mean={:.2f}, stddev={:.2f}, max={:.2f}'.format(median,mean,std,mx)
                Title = self.mpl_interface.histo(Y,x1,x2,dx=1.,xlabel=label,title=title,grid=True)
                print 'analyzeCUF.analyzeThreads',label,title
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
    def analyzeGridIssues(self,grid_issues,archiveDates):
        '''
        analyze dict grid_issues[site] = [archive0, archive1, ... archiveN]
        using dict archiveDates[archive] = date as datetime object

        plot site vs date for grid_issues
        plot country vs date for grid_issues
        plot date distribution of grid_issues
        '''
        
        colors = ['red','green','blue']
        markers= ['o','s','x']

        title = 'Grid issues  Site vs Date'
        fig,ax = plt.subplots(1)
        fig.autofmt_xdate(rotation=45,ha='right')
        desort = sorted(grid_issues.items(), key=lambda x: len(x[1]), reverse=True)
        descending = [q[0] for q in desort]
        #print 'descending',descending
        for iy,site in enumerate(descending):
            if len(grid_issues[site])>0 : 
                x,y = [],[]
                for archive in grid_issues[site]:
                    x.append( archiveDates[archive] )
                    y.append( float(iy) )
                plt.plot(x,y,color=colors[iy%3],marker=markers[iy%3])

        plt.ylim(-1.,len(descending)+1)
        yt = [float(q)+0.5 for q in range(len(descending))]
        plt.yticks(yt, descending)
        plt.xlim(datetime.datetime(2017,1,1),datetime.datetime(2022,1,1))
        plt.title(title)
##        plt.gca().set_aspect(5) ### tall narrow plot

        plt.grid()
        self.showOrPlot(title)


        title = 'Grid issues Country vs Date'
        fig,ax = plt.subplots(1)
        fig.autofmt_xdate(rotation=45,ha='right')
        byCountry = {}
        countries = sorted(list(set([q[-2:] for q in descending])))
        for c in countries: byCountry[c] = []
        for site in grid_issues:
            c = site[-2:]
            byCountry[c].extend( grid_issues[site] )
        for iy,country in enumerate(countries):
            if len(byCountry[country])>0 :
                x,y = [],[]
                for archive in byCountry[country]:
                    x.append( archiveDates[archive] )
                    y.append( float(iy) )
                plt.plot(x,y,color=colors[iy%3],marker=markers[iy%3])
        plt.ylim(0.,len(countries)+1)
        yt = [float(q)+0.5 for q in range(len(countries))]
        plt.yticks(yt, countries)
        plt.xlim(datetime.datetime(2017,1,1),datetime.datetime(2022,1,1))
        plt.title(title)

        plt.grid()
        self.showOrPlot(title)

        title = 'Grid issues vs Date (by month)'
        fig,ax = plt.subplots(1)
        fig.autofmt_xdate(rotation=45,ha='right')
        iByM = {}
        for site in grid_issues:
            for archive in grid_issues[site]:
                ym = self.getMonth(archive)
                if ym not in iByM: iByM[ym] = 0
                iByM[ym] += 1
                
        x,y = [],[]
        for ym in sorted(iByM):
            y.append( iByM[ym] )
            dt = datetime.datetime.strptime(ym,'%Y-%m') # YYYY-MM
            x.append( dt )

        dtlims = [datetime.datetime(2017,1,1),datetime.datetime(2022,1,1)]
        ax = plt.subplot(111)
        ax.bar(x,y)
        ax.set_xlim(dtlims)

        ax.xaxis_date()
        ax.set_title(title)
        ax.figure.autofmt_xdate(rotation=80)
        plt.grid()
        self.showOrPlot(title)

        return
    def correlateGrid(self,grid_issues, issues, issueOrder, issueUnique):
        '''
        correlate grid_issues with classification of all issues

        Output:
         grid_issues[site] = [archive0, ...] after removing sites correlated with unique issues

        Inputs:
        grid_issues[site] = [archive0, archive1, ... archiveN]
        issues = {}         # {issue: [archive0, archive1, ...] } = list of threads for this issue
        issueOrder = list with issue names in order of analysis
        issueUnique = list same order as issueOrder with True if thread can only be assigned to this issue

        SI[archive] = [site, [issue0, issue1, ...] ]
        '''

        SI = {}
        for site in grid_issues:
            for gar in grid_issues[site]:
                for issue in issues:
                    if gar in issues[issue] :
                        if gar not in site: SI[gar] = [site, []]
                        SI[gar][1].append( issue )
        print '\nanalyzeCUF.correlateGrid'
        output_grid_issues = {}
        for issue,unique in zip(issueOrder,issueUnique):
            if self.debug > 2 : print 'analyzeCUF.correlateGrid issue,unique',issue,unique
            if not unique:
                for archive in SI:
                    site,LIST = SI[archive]
                    if issue in LIST:
                        if site not in output_grid_issues: output_grid_issues[site] = []
                        output_grid_issues[site].append( archive )
                        print archive, site, ', '.join(LIST)
                        
        return output_grid_issues
 
    def mergeInterleaved(self,Threads):
        '''
        return dict newThreads with interleaved threads with identical subjects merged

        Let Li = list of message numbers from Thread Ti with Lij as the jth message in list Li, 
        then T1 is interleaved with T2, if L10< L2j < L1n for 0<=j<len(L2)

        Threads[archive0] = [Subject0,[(archive0,msgid0,irt0,from0), (archive1,msgid1,irt1,from1) ,...] ]

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
                            A0 = Threads[a1][1][0][0]   # archive for first entry in thread
                            An = Threads[a1][1][-1][0]  # archive for last entry in thread
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

        Threads[archive0] = [Subject0,[(archive0,msgid0,irt0,from0), (archive1,msgid1,irt1,from1) ,...] ]
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

        Threads[archive0] = [Subject0,[(archive0,msgid0,irt0,from0), (archive1,msgid1,irt1,from1) ,...] ]

        '''
        if self.debug > 1 : print 'analyzeCUF.locateRef: inputs archive, subj, irt, ref',archive, subj, irt, ref

        irtMatchedKeys = []
        refMatchedKeys = []
        keysInSearch   = []
        for key in self.msgOrder: # 
            if key in Threads:
                keysInSearch.append(key)
                for tupl in Threads[key][1]:
                    archN,msgidN,irtN,fromN = tupl
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
            if self.debug > 0 : print 'analyzeCUF.locateRef NO MATCH archive,subj,irt,ref,subj',archive,subj,irt,ref
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
    def writeMsgs(self,archiveList,output='msgs_to_study.log'):
        '''
        get email messages for a list of archive and write them to output
        '''
        
        logFile = self.logDir + '/' + output
        ufn = open(logFile,'w')
        print '\nanalyzeCUF.writeMsgs Write messages to',logFile
        for archive in archiveList:
            text = self.extractMsg.getText(archive,input='archive')
            ufn.write('\n\n ===========> Message from '+archive+'\n')
            ufn.write(text)
        ufn.close()
        return
    def showOrPlot(self,words):
        '''
        show plot interactively or put it in a pdf and png file

        and clear plot after showing or drawing
        '''

        if self.plotToFile:
            filename = self.titleAsFilename(words)
            pdf = self.figDir + '/' + filename + '.pdf'
            png = pdf.replace('.pdf','.png')
            plt.savefig(pdf)
            plt.savefig(png)
            print 'analyzeCUF.showOrPlot Wrote',pdf,png
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
    def tableMaker(self,headers,rows,rowlabels,integers=False,caption=None):
        '''
        return table, suitable to print, given headers, rows and row labels
        headers = list of header titles with length NH = [h1, h2, ..., hNH]
        rows = list of lists with each row of length NH = [ [a1, a2, ..., aNH], ... [z1, z2, ..., zNH] ] 
        rowlabels = list of row labels with length = # of rows
        
        '''
        fprec = '.1f'
        if integers : fprec = 'd'
        hfmt = ''
        ffmt = ''
        fm = '{:'+fprec+'}'
        for i,h in enumerate(headers):
            L = len(h)
            for r in rows:
                L = max(L,len(fm.format(r[i])))
            hfmt += '{'+str(i)+':>'+str(L)+'} '
            ffmt += '{'+str(i)+':>'+str(L)+fprec+'} '
        i += 1
        ffmt += ' {'+str(i)+'} '
        table = ''
        if caption is not None : table += caption + '\n'
        table += hfmt.format(*headers)
        table += '\n'
        for ir,r in enumerate(rows):
            Q = [x for x in r]
            Q.append(rowlabels[ir])
            table += ffmt.format(*Q) + '\n'

        return table
    def writeGridIssues(self,grid_issues):
        '''
        write grid issue messages to a file for human analysis
        '''
        A = []
        for site in grid_issues:
            A.extend(grid_issues[site])
        A = list(set(A))
        self.writeMsgs(A,output='grid_issues.log')
        return
    def main(self):
        '''
        main module for analysis
        
        get gridSiteNames = list of all grid sites found in all messages
        get archiveDates  = dict[archive] = date of message

        get Threads = recreate threads from list of files with messages

        classify Threads into issues
        analyze the Threads

        get all grid sites with issues from threads
        analyze the grid sites issues
        '''
        files,msgOrder = self.getArchive()
        self.msgOrder = msgOrder
        self.nFiles   = len(files)
        gridSiteNames = self.extractMsg.gridSites(files=files)
        archiveDates  = self.extractMsg.getArchiveDates(files)
        if self.debug > 2 : print 'analyzeCUF.main self.msgOrder',self.msgOrder
            
        Threads = self.processFiles(files)
        
        
        issues,issueOrder,issueUnique, thread_issues = self.issues_keyphrases.classifyThreads(Threads)
        self.analyzeThreads(Threads,issues,issueOrder,issueUnique,thread_issues,archiveDates)

        grid_issues = self.issues_keyphrases.gridIssues(Threads,gridSiteNames)
        grid_issues = self.correlateGrid(grid_issues, issues, issueOrder, issueUnique)
        self.writeGridIssues(grid_issues)
        self.analyzeGridIssues(grid_issues,archiveDates)

        return
if __name__ == '__main__' :
    testBuildThreads = False
    if testBuildThreads :
        aCUF = analyzeCUF()
        files, aCUF.msgOrder = aCUF.getArchive()
        aCUF.buildThreads(files)
        sys.exit('done testing buildThreads')

    
    testTableMaker = False
    if testTableMaker :
        headers = ['pigs', 'monkeys', 'sheep']
        rows = [ [50427,88,219], [73, 102, 12], [129, 11, 512] ]
        rowlabels = ['Fred`s farm','Mary`s house','At college']
        aCUF = analyzeCUF()
        table = aCUF.tableMaker(headers,rows,rowlabels,integers=True,caption='Here is a test table!!')
        print table
        sys.exit('done testing tableMaker')
    

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
    
