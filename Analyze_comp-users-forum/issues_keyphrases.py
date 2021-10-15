#!/usr/bin/env python
'''
define issues and key words and phrases for analysis of comp-users-forum threads

20210924
'''
#import math
import sys,os
import glob
import email, base64
import numpy

class issues_keyphrases():
    def __init__(self):
        self.debug = 0
        print 'issues_keyphrases.__init__ completed'
        return
    def define(self):
        '''
        return idict = dictionary defining issues with requirements systems and actions
        and idictOrder = order that issues are to be applied
        idict[issue] = [ systems, actions ]
        
        systems = list of systems
        actions = list of actions
        case is ignored

        '''
        idict = {}
        idictOrder = []

        name = 'Announcements'
        systems = ['Distributed Computing', 'BelleDIRAC', 'DIRAC', 'KEKCC', 'network', 'gbasf2','VOMS membership','Please use gbasf2','Call for volunteer','Integration of BelleDIRAC','gbasf2 tutorial','Coming gbasf2','Release']
        actions = ['intervention','to be down','shutdown', 'downtime','timeout', 'update', 'restart', 'security patch', 'release', 'is down','Please use gbasf2','test of','with Rucio','feedback','follow-up','migration to Rucio','available on']
        idict[name] = [ systems, actions ]
        idictOrder.append(name)

        name = 'Downloading files'
        systems = ['Download','Cannot get files']
        actions = ['fail',"can't",'error','unable','problem','slow','grid','files','issues','jobs','from LCG']
        idict[name] = [ systems, actions ]
        idictOrder.append(name)

        name = 'Jobs in waiting'
        systems = ['Jobs']
        actions = ['waiting','stuck','stall','too long']
        idict[name] = [ systems, actions ]
        idictOrder.append(name)

        name = 'Failed jobs'
        systems = ['Jobs']
        actions= ['fail', 'error','crash']
        idict[name] = [ systems, actions ]
        idictOrder.append(name)

        name = 'Proxy/VOMS'
        systems = ['VOMS', 'proxy', 'Certificate']
        actions= ['Error', 'fail', 'unable', '_init','not register']
        idict[name] = [ systems, actions ]
        idictOrder.append(name)

        name = 'Submitting jobs'
        systems = ['submit']
        actions= ['cannot','troubles','problem','Resubmit','not show','environment','How to']
        idict[name] = [ systems, actions ]
        idictOrder.append(name)

        name = 'Installing gbasf2'
        systems = ['gbasf2','light-2106-rhea']
        actions= ['install','Problems updating','setting up','issue','help','unable to setup','updating error','not available at LCG']
        idict[name] = [ systems, actions ]
        idictOrder.append(name)
        
        

        
        return idict
    def classifyThreads(self,Threads):
        '''
        Threads[archive0] = [Subject0,[(archive0,msgid0,irt0), (archive1,msgid1,irt1) ,...] ]

        '''
        idict = self.define()
        issues = {}
        thread_issues = {}
        Classified = []
        for issue in idict:
            Reqmts = idict[issue]
            issues[issue] = []
            for key in Threads:
                Subject = Threads[key][0].lower()
                if self.findN(Subject,Reqmts) :
                    issues[issue].append( Subject )
                    if key not in thread_issues: thread_issues[key] = []
                    thread_issues[key].append(issue)
                    Classified.append( key )

        print 'issues_keyphrases.classifyThreads',len(Threads),'total threads with',len(Classified),'successfully classified'
        for issue in sorted(issues):
            print 'issues_keyphrases.classifyThreads issue',issue,'found',len(issues[issue]),'times'

        # list of threads that are classified under >1 issue
        First = True
        for key in thread_issues:
            if len(thread_issues[key])>1 :
                if First :
                    First = False
                    print '\nissues_keyphrases.classifyThreads Threads that are classified under >1 issue:'
                Subject = Threads[key][0]
                print key,Subject,":",", ".join(thread_issues[key])
        if not First: print 'issues_keyphrases.classifyThreads NO threads classified under >1 issue!'

            
        print '\nissues_keyphrases.classifyThreads HERE ARE THE UNCLASSIFIED THREADS'
        for key in Threads:
            if key not in Classified:
                print key,Threads[key][0]
                        
        return
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
        matching ignores case
        '''
        subject = Subject.lower()
        for phrase in phrases:
            p = phrase.lower()
            if p in subject : return True
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
    Threads = ik.readFileThreads()
    ik.classifyThreads(Threads)
    sys.exit('exit here cuz the rest is gibberish')
    
    fn = 'DATA/comp-users-forum_2020-02/22'

    listParts = False
    if listParts:
        fn = 'DATA/comp-users-forum_2021-01/107'
        if len(sys.argv)>1 : fn = sys.argv[1]
        eM.listParts(fn)
        sys.exit('extractMsg listParts ' + fn)
