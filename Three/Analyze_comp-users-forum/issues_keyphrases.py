#!/usr/bin/env python
'''
define issues and key words and phrases for analysis of comp-users-forum threads

20210924
'''
#import math
import sys,os,re
import glob
import email, base64
import numpy
import matplotlib.pyplot as plt
import extractMsg
import itertools
import tableMaker


class issues_keyphrases():
    def __init__(self,debug=0,now='groundhogday',prefix=None):
        self.debug = debug
        self.now = now

        ## used by getWords
        ignoreThese = ['Belle']
        self.ignoreThese = [x.lower() for x in ignoreThese]


        self.extractMsg = extractMsg.extractMsg(prefix=prefix)
        self.tableMaker = tableMaker.tableMaker()

        Udir = 'UNCLASSIFIED/'
        if not os.path.exists(Udir) : os.makedirs(Udir) 
        self.UNCLASSIFIED_LOG = Udir + self.now + '.log'
        
        print('issues_keyphrases.__init__ completed')
        return
    def define(self,report=True):
        '''
        return idict = dictionary defining issues with requirements systems and actions
        and idictOrder = order that issues are to be applied
        idict[issue] = [ [ systems, actions ], [ phrase1, phrase2, ... ] ] 
        
        systems = list of systems in Subject
        actions = list of actions in Subject
        phraseN = list of phrases in email text, phraseN must precede phraseN+1 in text
                NOTE THAT ONLY EMAIL TEXT OF FIRST MESSAGE IN THREAD IS SCRUTINIZED
        case is ignored

        if report==True, then report definitions

        20220210 Revise and add some criteria based on Michel's analyses presented at the 39th,40th and 41st B2GMs
        20220419 Further revisions to reduce the number of unclassified threads

 
        '''
        idict = {}
        idictOrder = []

        self.announcementsName = name = 'Announcements'
        systems = ['Distributed Computing', 'BelleDIRAC', 'DIRAC', 'KEKCC', 'network',
                       'VOMS membership','Please use gbasf2','Call for volunteer',
                       'Integration of BelleDIRAC','gbasf2 tutorial','Coming gbasf2','Release',
                       'Singularity recipe','Draft of','Unscheduled','AMGA',
                       'Conditions Database',
                       'Downtime', 'Removal of','Change of Mailing List','Refrain from'   ]
        actions = ['intervention','to be down','shutdown', 'downtime','timeout', 'update',
                       'restart', 'security patch', 'release', 'is down','Please use gbasf2',
                       'test of','with Rucio','feedback','follow-up',
                       'migration to Rucio','available on',
                       'Singularity recipe','proceedings','power cut','not available',
                       'access GPFS',
                       'grid services', 'from grid use','Configuration','GNN-based Flavor Tagger on grid']
        phrase1 = ['Dear collaborators','Dear computing users', 'Hello everyone', 'Dear Grid Users',
                       'Dear gbasf2 users', 'Dear * colleagues','Dear all * gbasf2',
                       'Dear all * required','Dear all * workaround','to check the change of "From:" line',
                       'CNAF outage * over', 'issue * Rucio server']
        UNIQUE = True
        idict[name] = [ [systems, actions], [ phrase1 ], UNIQUE ]
        idictOrder.append(name)

        name = 'Queries'
        systems = ['How to','module','Running on','To run on','How can I','Question','On Hold','Justice for','Not finding']
        actions = ['use','save','delet','on the grid','dataset','full data proc 10','reschedul','grid-users','MC data']
        phrase1 = ['How can','Is there a * way','Is it possible','I need to understand','Does anyone know','Can anyone comment',
                       'what I can do if', 'Is there anyway to get * files', 'wondering why','Is there * a way',
                       'wondering if * a way','I wonder if there * a way','wondering if I',
                       'Is there any method',
                       'Is there a command', 'how to fix','What is the correct method',
                       'How do I do','there is something missing * script','Please tell me how to', 
                       'Is it fine * to run',
                       'What does * indicate', 'Could you help','like to know * possible',
                       'I have * question',
                       'Could * help me',
                       'Could * hint',
                       'trying to submit  jobs * message that I get',
                       'I am not sure this * correct place',' I am not sure if this * correct place',
                       'when I try * gb2',
                       'like to confirm * ignored','questions.belle2.org','development of gbasf2',
                       'not sure if this is the right place to ask','give me some suggestion',
                       'Is there  a new * version','How is * calculated',
                       'what I am doing wrong. Could you please',
                       'would like to use * interface',
                       'would like to know * status',
                       'not familiar with why jobs become "Killed"', 
                       'my own hack','what * recommended procedure','do you have * suggest',
                       'gbasf2 * wanted to check', 'I see the following interesting effect',
                       'my understanding * analysts were encouraged', 
                       'run gbasf2 with patched basf2']
        UNIQUE = True
        idict[name] = [ [systems, actions], [ phrase1 ], UNIQUE ]
        idictOrder.append(name)
        

        name = 'Proxy/VOMS'
        systems = ['VOMS', 'proxy', 'Certificate','PEM', 'Problem', 'Registration','Outdated']
        actions= ['Error', 'fail', 'unable', '_init','not register', 'expired','could not add','initializing proxy','CRLs']
        phrase1 = ['gb2_proxy_init * Error: Operation not permitted']
        UNIQUE = True
        idict[name] = [ [systems, actions], [ phrase1 ], UNIQUE ]
        idictOrder.append(name)

        name = 'Downloading files'
        UNIQUE = False
        systems = ['Download','Cannot get files','files stuck', 'Replicas']
        actions = ['fail',"can't",'cannot','error','unable','problem','slow','grid','files','issues','jobs',
                       'from LCG','stuck at', 'signal MC','timeout','takes hours', 'stuck']
        phrase1 = ['trying to download * error','unable to retrieve * output','gb2_ds_get * crash',
                       "don't get rescheduled * download",'download * from the grid','error when download',
                       'trying to download * too long','download output * empty','files * size 0',
                       'Maximum input file size exceeds limit',
                       'output file * not download','gbs2_ds_get * re-download']
        idict[name] = [ [systems, actions], [ phrase1 ], UNIQUE ]
        idictOrder.append(name)        

        name = 'Failed jobs'
        UNIQUE = False
        systems = ['Jobs','Job failing','Grid Job','project failure','to run','Projects','Unknown error','Premature Dispatching','SSLTimeout','Maximum of','Application Finished With']
        actions= ['fail', 'error','crash','Exited','reschedul* reached','incomplete']
        phrase1 = ['job * failed','job * failing',
                       'maximum * reschedul','max no *reschedul','maximum number of resch',
                       'scouting to fail','receiv* job failure']
        idict[name] = [ [systems, actions], [ phrase1 ], UNIQUE ]
        idictOrder.append(name)

        name = 'Jobs in waiting/stuck'
        UNIQUE = False
        systems = ['Jobs']
        actions = ['waiting','stall','too long','stuck in Completed status','stuck on Completed','zero running','hit rescheduling limit']
        phrase1 = ['stuck * Pilot Agent', 'running on the grid * more than','jobs * stalled',
                       'jobs * stuck','job * stuck','job suck * status',
                       'project * still waiting','Waiting for Scout Job Completion',
                       'job * in "Waiting"','jobs * running very slowly',
                       'submit * ago','jobs * no sign of activity','have 0 running jobs * jobs waiting', 
                       'drop in the number of jobs running','No * jobs are running','just 1 job is running currently',
                       'file transfers * stuck']
        idict[name] = [ [systems, actions], [ phrase1 ], UNIQUE ]
        idictOrder.append(name)

        name = 'Input data unavailable'
        UNIQUE = False
        systems = ['Input data', 'datasets'] 
        actions= ['not available', 'error on', 'disappear']
        phrase1 = ['Input data not available' , 'fail * Input data resolution','job * Input data resolution' ]
        idict[name] = [ [systems, actions], [ phrase1 ], UNIQUE ]
        idictOrder.append(name)

        name = 'Submitting jobs'
        UNIQUE = False
        systems = ['submit', 'submission', 'reschedule']
        actions= ['cannot','troubles','problem','Resubmit','not show','environment','How to','fail','collections','unable','error']
        phrase1 = ['trouble submitting jobs','issue submitting jobs','difficult * submitting jobs',
                       'on the grid * error','to the GRID * error',
                       'submitted several jobs * wrong', 
                       'submit a job * not allowed',
                       'workload-management server * down']
        idict[name] = [ [systems, actions], [ phrase1 ], UNIQUE ]
        idictOrder.append(name)

        name = 'Installing gbasf2'
        UNIQUE = False
        systems = ['gbasf2','light-2106-rhea']
        actions= [
            'install','Problems updating','setting up','issue','help',
            'unable to setup','updating error','not available at LCG']
        phrase1 = ['some trouble * gb2_check_release', 'unable to install gbasf2','error * basf2 not found', 
                       'update gbasf * error message']
        idict[name] = [ [systems, actions], [ phrase1 ], UNIQUE ]
        idictOrder.append(name)

        name = 'Deleting files'
        UNIQUE = False
        systems = ['delete','deleting']
        actions= ['file']
        phrase1 = ['not able * remove director','like to remove * old projects']
        idict[name] = [ [systems, actions], [ phrase1 ], UNIQUE ]
        idictOrder.append(name)
        
        #name =  'Register output'
        #systems = []
        #actions= []
        #phrase1 = []
        #idict[name] = [ [systems, actions], [ phrase1 ], UNIQUE ]
        #idictOrder.append(name)


        name = 'Bug report'
        UNIQUE = False
        systems = ['belle2.org','MC generation','TypeError','gb2_',
                       'Wildcard','BelleDIRAC job monitor','Production','verification failed', 'gbasf2 commands',
                       'file larger', 'produced skim','Conditions DataBase', 'Signal MC','wrong Ecm','list_all_collections',
                       'RucioFileCatalog interface']
        actions = ['system error','wrong mass',' --','crash', 'broken', 'larger than 5GB', 'larger than 5 GB', 
                    'fails','wrong number of files','failed', 'failing', 'not working','unable to access',
                    'Problem parsing payload', 'dataset missing', 'wrong Ecm in bucket', 'error']
        phrase1 = ['problem connecting * at KEK', 'feature of gbasf2 * stop working',
                    'trouble running * FEI',
                    'try to reschedule * following error:',
                    'FileCatalog error', 
                    'now deprecate','dirac portal * Bad gateway',
                    "Can't load RucioFileCatalogClient",
                    'error * rucio list',
                    'limit on the allowed number of characters','Project is too long (max', 
                    'gb2_ds_ * error', 'gb2_ds_ * strange',
                    'strange status * job',
                    'Rescheduling * many times',
                    'skim job * files are so large',
                    'cannot * output error','am trying * error','troubles log * KEKCC',
                    'dataset searcher * no results']
        idict[name] = [ [systems, actions], [ phrase1 ], UNIQUE ]
        idictOrder.append(name)

        ### check for overlap between classification schemes
        print('\nissues_keyphrases.define Check for overlap between classification schemes')
        originalDebug = self.debug
        #self.debug = 3
        nOverlaps = 0
        for i1, name1 in enumerate(idictOrder):
            sys1,act1 = idict[name1][0]
            for Subject in [a + ' ' + b for a,b in itertools.product(sys1,act1)]:
                if self.debug > 2 : print('i1,name1,Subject',i1,name1,Subject)
                for i2 in range(i1+1,len(idictOrder)):
                    name2 = idictOrder[i2]
                    Reqmts = idict[name2][0]
                    if self.findN(Subject,Reqmts):
                        print('Subject overlap: issue#',i1,name1,'Subject','`'+Subject+'`','overlaps issue#',i2,name2)
                        nOverlaps += 1
                
            phr1      = idict[name1][1][0]
            if type(phr1) is not list: sys.exit('ERROR phr1 is '+str(type(phr1)))
            if self.debug > 2 : print('phr1',phr1)
            for p1 in phr1:
                for i2 in range(i1+1,len(idictOrder)):
                    name2 = idictOrder[i2]
                    phr2 = idict[name2][1]
                    if type(phr2) is not list: sys.exit('ERROR phr2 is '+str(type(phr2)))                    
                    if self.debug > 2 : print('i1,name1,p1',i1,name1,p1,'i2,name2,phr2',i2,name2,phr2)
                    if self.findN(p1,phr2):
                        print('Message overlap: issue#',i1,name1,'p1','`'+p1+'`','overlaps issue#',i2,name2)
                        nOverlaps += 1
        if nOverlaps==0:
            print('issues_keyphrases.define NO OVERLAPS FOUND')
        else:
            print('issues_keyphrases.define Found',nOverlaps,'overlaps')
        self.debug = originalDebug

        
        ### Informative output
        for iname, name in enumerate(idictOrder):
            Unique = idict[name][2]
            if Unique :
                print('issues_keyphrases.define Classification of issue#',iname,name,'is UNIQUE.', \
                'It supersedes subsequent issues.')
        if report:
            print('\nissues_keyphrases.define Issue definitions.\n Email subject classification uses `systems` and `actions`.\n Email text classification uses `phrases`.')
            for iname, name in enumerate(idictOrder):
                u = 'not unique'
                if idict[name][2] : u = 'UNIQUE'
                print('\nDefinition of issue#',iname,name,'is',u)
                systems,actions = idict[name][0]
                print('systems: `'+'` `'.join(systems)+'`')
                print('actions: `'+'` `'.join(actions)+'`')
                phrases = idict[name][1][0]
                print('phrases: `'+'` `'.join(phrases)+'`')
            print('')

            print('\nissues_keyphrase.define Latex-compatible table for issue definitions')
            for iname,name in enumerate(idictOrder):
                print('{0} & {1} & {2} \\\ '.format(iname,idict[name][2],name))
            print('')
      

            

        
        return idict,idictOrder
    def gridIssues(self,Threads,gridSiteNames):
        '''
        return grid_issues[site] = [archive0, archive1, ...]
        where site is the lower case name of a grid site  and archiveI is a thread that mentions that site.

        First check if message can be parsed to extract names of failed grid sites, 
        if that returns a null list, then check subject text.

        Multiple sites can be mentioned in a single thread
        '''
        grid_issues = {}
        sitenames = [x.lower() for x in gridSiteNames]
        for site in sitenames: grid_issues[site] = []
        for key in Threads:
            Subject = Threads[key][0]
            text = self.extractMsg.getText(key,input='archive')
            badSites = self.parseGridMsg(text,sitenames)
            if len(badSites)>0:
                for site in badSites :
                    if key not in grid_issues[site]: grid_issues[site].append(key)
            else:
                Sandt = Subject.lower() 
                for site in sitenames:
                    if site in Sandt:
                        if key not in grid_issues[site]: grid_issues[site].append(key)
        desort = sorted(list(grid_issues.items()), key=lambda x: len(x[1]), reverse=True)
        descending = [q[0] for q in desort]
        if self.debug > 0:
            print('\nissues_keyphrase.grid_issues in descending order of threads/site')
            for site in descending:
                print(site,len(grid_issues[site]),grid_issues[site])
        return grid_issues
    def parseGridMsg(self,msg,sitenames):
        '''
        return BadSites = list of lower case names of sites identified with failures in input msg.

        Treat the case of gb2_project_analysis explicitly

        For example below, BadSites = ['LGC.CNAF.it']
Done (74)
   Execution Complete (74)
     Done (74)
        ARC.SIGNET.si  :   6
        LCG.CESNET.cz  :   7
        LCG.DESY.de    :  18
        LCG.KEK2.jp    :   2
        LCG.KIT.de     :  17
        LCG.Napoli.it  :   7
        OSG.BNL.us     :  17
Failed (15)
   Application Finished With Errors (15)
     RuntimeError("basf2helper.py Exited With Status 254",) (15)
        LCG.CNAF.it    :  15

        '''
        badSites = []
        cr = [q.start() for q in re.finditer('\n',msg)]

        ### identify relevant section by 'nFailed' with subsequent lines that start with blanks
        sF = 'Failed'
        tbl= '   '
        for I,i in enumerate(cr):
            if msg[i+1:i+1+len(sF)]==sF:
                if self.debug > 2 : print('issues_keyphrases.parseGridMsg i',i,'msg[i:i+10]',msg[i:i+10])
                if self.debug > 2 : print('issues_keyphrases.parseGridMsg cr[I+1:len(cr)-2]',cr[I+1:len(cr)-2])
                J = I+1
                while J<len(cr)-2:
                    j = cr[J]
                    if self.debug > 2 : print('issues_keyphrase.parseGridMsg j',j,'msg[j+1:j+10]',msg[j+1:j+10])
                    if msg[j+1:j+1+len(tbl)]==tbl:
                        k = cr[J+1]
                        name = msg[j:k].strip().split()[0]
                        if self.extractMsg.validSiteName(name):
                            if name not in badSites: badSites.append( name )
                    if msg[j+1]!=' ':
                        break
                    J += 1
                    
        ### search line-by-line for line containing grid site name but not string 'banned'
        if len(badSites)==0:
            for i1,i2 in zip(cr[:-1],cr[1:]):
                line = msg[i1:i2].lower()
                for site in sitenames:
                    if site in line and 'banned' not in line and site not in badSites:
                        badSites.append( site )
                
                
        badSites = [w.lower() for w in badSites]      
        return badSites
    def classifyThreads(self,Threads,listSMTfDC):
        '''
        Classify threads by issue. 
        Issues are named and specified in issues_keyphrases.define()
        Hierarchy for determination of issue: Subject, single-message-Announcements, email text 

        inputs 
        Threads[archive0] = [Subject0,[(archive0,msgid0,irt0,from0), (archive1,msgid1,irt1,from1) ,...] ]
        listSMTfDC = [archiveN,...] = list of single-message threads from the Distributed Computing team

        return issues,issueOrder,issueUnique, thread_issues
         issues[issue0] = [achive0, archive1, ...]
         issueOrder = [issue0, issue1, ...]
         issueUnique = list with entry = True if issue is unique. Same indexing as issueOrder
         thread_issues = {archive0: [issue1, issue2], ...} = how many issues assigned to each thread?

         20220210 Add to hierarchy for issue classification: 
         Single-message threads from a member of the distributing computing team will be classified as announcements
        '''
        print('\nissues_keyphrases.classifyThreads Begin classification of',len(Threads),'threads.')
        
        idict, idictOrder = self.define()  # Note that Unclassified issue is added below
        
        issues = {}         # {issue: [archive0, archive1, ...] } = list of threads for this issue
        thread_issues = {}  # {archive0: [issue1, issue2]} = how many issues assigned to each thread?
        Classified = []     # list of threads classified in >0 issues
        IgnoreThese= []     # list of threads classified uniquely which should be ignored

        Stages = [] 
        NbyStage = {}
        nameUnclassified = 'Unclassified'
            
        ### first assign thread to issue by Subject
        if self.debug > 2 : print('issues_keyphrases.classifyThreads First try to assign to issue by Subject')
        for issue in idictOrder:
            Reqmts = idict[issue][0] ## Subject
            Unique = idict[issue][2]
            issues[issue] = []
            for key in [x for x in Threads if x not in IgnoreThese]:
                Subject = Threads[key][0].lower()
                if self.findN(Subject,Reqmts) :
                    issues[issue].append( key )
                    if key not in thread_issues: thread_issues[key] = []
                    thread_issues[key].append(issue)
                    if key not in Classified : Classified.append( key )
                    if Unique : IgnoreThese.append( key )
                
        Stages = ['bySubject']
        print('\nissues_keyphrases.classifyThreads',len(Threads),'total threads with',len(Classified),'successfully classified by Subject')
        for issue in idictOrder:
            print('issues_keyphrases.classifyThreads issue',issue,'found',len(issues[issue]),'times')
            NbyStage[issue] = [ len(issues[issue]) ]
        NbyStage[nameUnclassified] = [ 0 ]

        ### 20220210, single-message threads from distributed computing team will
        ### be classified as Announcements
        if self.debug > 2 : print('issues_keyphrases.classifyThreads Second try to assign single-message threads from DC team as Announcements')
        issue = self.announcementsName
        Unique = idict[issue][2]
        for key in [x for x in listSMTfDC if x not in Classified]:
            if key not in IgnoreThese:
                issues[issue].append( key )
                if key not in thread_issues: thread_issues[key] = []
                thread_issues[key].append( issue )
                if key not in Classified : Classified.append( key )
                if Unique : IgnoreThese.append( key )

        Stages.append('bySMT')
        print('\nissues_keyphrases.classifyThreads',len(Threads),'total threads with',len(Classified), \
                  'successfully classified by single-message from DC team, after classification by Subject')
        for issue in idictOrder:
            print('issues_keyphrases.classifyThreads issue',issue,'found',len(issues[issue]),'times')
            NbyStage[issue].append( len(issues[issue]) )
        NbyStage[nameUnclassified].append( 0 )
                

        ### next, for unassigned threads, assign thread to issue using email text
        if self.debug > 2 : print('issues_keyphrases.classifyThreads Finally try to assign based on email text')
        originalDebug = self.debug
        unClassified = []
        for key in Threads:
            if key not in Classified : unClassified.append( key )
        for issue in idictOrder:
            Reqmts = idict[issue][1]
            Unique = idict[issue][2]
            if self.debug > 2 : print('issues_keyphrases.classifyThreads by email text, issue',issue,'Reqmts',Reqmts)
            for key in [x for x in unClassified if x not in IgnoreThese]:
                text = self.extractMsg.getText(key,input='archive')
                if self.debug > 2 : print('issues_keyphrases.classifyThreads by email text, key',key)
                if self.debug > 3 : print('issues_keyphrases.classifyThreads by email text. text=',text)
                if self.findN(text,Reqmts) :
                    issues[issue].append( key )
                    if key not in thread_issues: thread_issues[key] = []
                    thread_issues[key].append(issue)
                    if key not in Classified : Classified.append( key )
                    if Unique : IgnoreThese.append( key )

        #### Bookkeeping: add Unclassified issue
        name = nameUnclassified 
        issues[name] = []
        idictOrder.append( name ) 
        for key in Threads:
            if key not in Classified:
                issues[name].append(key)
                thread_issues[key] = [name]

        Stages.append( 'byEmailTxt' )
        print('\nissues_keyphrases.classifyThreads',len(Threads),'total threads with', \
          len(Classified),'successfully classified by email message text, after Subject classification.')
        for issue in idictOrder:
            print('issues_keyphrases.classifyThreads issue',issue,'found',len(issues[issue]),'times')
            NbyStage[issue].append( len(issues[issue]) )

        rows = []
        for issue in idictOrder: rows.append( NbyStage[issue] )
        for latex in [False,True]:
            table = self.tableMaker.tableMaker(Stages,rows,idictOrder,integers=True,caption='Classification of threads by stage',latex=latex)
            print(table)
            
        ### list of threads that are classified under >1 issue
        maxClass = -1
        for key in thread_issues: maxClass = max(maxClass, len(thread_issues[key]))
        if maxClass==1 :
            print('\nissues_keyphrases.classifyThreads NO threads classified under >1 issue!')
        else:
            for LEN in range(2,maxClass+1):
                nTot = sum( [len(thread_issues[key])==LEN for key in thread_issues] )
                print('\nissues_keyphrases.classifyThreads There are',nTot,'threads classified under',LEN,'issues:')
                for key in thread_issues:
                    if len(thread_issues[key])==LEN:
                        Subject = Threads[key][0]
                        print(key,Subject+" : ",", ".join(thread_issues[key]))
                        
        ### write messages from unclassified threads to a log file
        ufn = open(self.UNCLASSIFIED_LOG,'w')
        print('\nissues_keyphrases.classifyThreads Write messages from unclassified threads to',self.UNCLASSIFIED_LOG)
        ufn.write('\nissues_keyphrases.classifyThreads HERE ARE THE UNCLASSIFIED THREADS')
        for key in Threads:
            if key not in Classified:
                ufn.write('\nUNCLASSIFIED THREAD: '+ key + ' ' + Threads[key][0] + '\n')
                words = self.extractMsg.getText(key,input='archive')
                for sentence in words.split('\\n'):
                    ufn.write(sentence+ '\n')
        ufn.close()

        # self.wordFrequency(Threads,threshold=5)

        ### output
        issueOrder,issueUnique = [],[]
        for issue in idictOrder:
            issueOrder.append( issue )
            unique = False
            if issue in idict: unique = idict[issue][2]
            issueUnique.append( unique )
            if self.debug > 2 : print('issues_keyphrases.classifyThreads issue,unique',issue,unique)

                
        return issues,issueOrder,issueUnique, thread_issues
    def wordFrequency(self,Threads,threshold=5):
        '''
        frequency distribution of words in Subject of threads, ignoring case

        vaguely based on https://github.com/amueller/word_cloud/blob/master/wordcloud/wordcloud.py
        '''
        allWords = []
        for key in Threads:
            Subject = Threads[key][0]
            words = self.getWords( Subject.lower() )
            allWords.extend( words )

        freq = {x:allWords.count(x) for x in allWords}
        print('\nissues_keyphrases.wordFrequency Frequency of words in Threads. Minimum frequency is',threshold)
        for word in sorted( freq, key=freq.get, reverse=True):
            f = freq[word]
            if f>threshold: print(word,f)
        return
    def getWords(self,sentence,lmin=4):
        '''
        return list of words in sentence
        Requirements
        words must be >lmin characters long
        words must not be numbers
        words must not be in list of words to ignore
        '''
        s = sentence.split()
        words = []
        for w in s:
            if len(w)>lmin and not w.isdigit() and w not in self.ignoreThese:
                words.append(w)
        return words
    def findN(self,Subject,Reqmts):
        '''
        return True if at least one requirement from each set of requirements is found in Subject
        where  
        subject is a string
        Reqmts is a list of lists with each entry in a list being a possible requirement 

        matching ignore case
        '''
        for reqmt in Reqmts:
            if not self.basicFind(Subject,reqmt) : return False
        return True
    def basicFind(self,Subject,phrases):
        '''
        return True if a phrase in list phrases is found in string Subject

        if the wildcard '*' is found in a phrase, eg: 'part1 * part2', 
        then both 'part1' and 'part2' must be found in Subject and the location of 'part1' must precede 'part2'
        matching ignores case

        20230105 also replace all \n in Subject with a blank so that phrases that extend over 
                 multiple lines can be parsed and matched. And replace double spaces in Subject with a single space. 
        '''
        
        subject = Subject.lower().replace('\\n',' ').replace('  ',' ')
        if self.debug > 2 : print('issues_keyphrases.basicFind xxx subject',subject)
        for phrase in phrases:
            p = phrase.lower()
            if self.debug > 2 : print('issues_keyphrases.basicFind phrase.lower()',p)
            if '*' in p: 
                i = p.index('*')
                p1 = p[:i].strip()
                p2 = p[i+1:].strip()
                if self.debug > 2 : print('issues_keyphrases.basicFind p1',p1,'p2',p2)
                if p1 in subject and p2 in subject:
                    if self.debug > 2 : print('issues_keyphrases.basicFind subject.index(p1)',subject.index(p1),'subject.index(p2)',subject.index(p2))
                    if subject.index(p1)<subject.index(p2) : return True
            else:
                if p in subject :
                    if self.debug > 2 : print('issues_keyphrases.basicFind phrase found in subject')
                    return True
        if self.debug > 2 : print('issues_keyphrases.basicFind phrase NOT found in subject')
        return False
    def readFileThreads(self):
        fn = 'threads'
        f = open(fn,'r')
        Threads = {}
        for line in f:
            if ' ' in line:
                i = line.index(' ')
                archive = line[:i]
                subject = line[i+1:-1]
            else:
                archive = line[:-1]
                subject = ''
            Threads[archive] = [subject,[]]
        f.close()
        return Threads
if __name__ == '__main__' :
    ik = issues_keyphrases()

    testGridParse = False
    if testGridParse :
        
        for fn in ['DATA/comp-users-forum_2021-06/61','DATA/comp-users-forum_2020-09/79','DATA/comp-users-forum_2020-01/17']:
            text = ik.extractMsg.getText(fn)
            badSites = ik.parseGridMsg(text)
            print(fn,'badSites',badSites)
        sys.exit('issues_keyphrases testGridParse')

    Threads = ik.readFileThreads()
    issues,issueOrder,issueUnique = ik.classifyThreads(Threads)
    sys.exit('exit here cuz the rest is gibberish')
    
    fn = 'DATA/comp-users-forum_2020-02/22'
