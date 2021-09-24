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
        idict = {}
        idict['Announcements'] = []
        systems = ['Distributed Computing', 'BelleDIRAC', 'DIRAC', 'KEKCC', 'network', 'gbasf2']
        actions = ['intervention','to be down','shutdown', 'downtime','timeout', 'update', 'restart', 'security patch', 'release']
        idict['Announcements'] = [ systems, actions ]
        
                       
        return idict
    def classifyThreads(self,Threads):
        '''
        Threads[archive0] = [Subject0,[(archive0,msgid0,irt0), (archive1,msgid1,irt1) ,...] ]

        '''
        idict = self.define()
        issues = {}
        for issue in idict:
            Reqmts = idict[issue]
            issues[issue] = []
            Classified = []
            for key in Threads:
                Subject = Threads[key][0].lower()
                if self.findN(Subject,Reqmts) :
                    issues[issue].append( Subject )
                    Classified.append( key )

        print 'issues_keyphrases.classifyThreads',len(Threads),'total threads with',len(Classified),'successfully classified'
        for issue in sorted(issues):
            print 'issues_keyphrases.classifyThreads issue',issue,'found',len(issues[issue]),'times'
                        
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
    def find2(self,Subject,systems,actions):
        '''
        return True if at least one system in systems and at least one action in actions is found in subject
        where  
        subject is a string
        systems and actions are lists of strings
        matching ignore case
        '''
        if self.basicFind(Subject,systems):
            if self.basicFind(Subject,actions):
                return True
        return False
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
