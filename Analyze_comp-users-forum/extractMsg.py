#!/usr/bin/env python
'''
extract the original email text from a message from comp-users-forum

main use is extractMsg.getEmailMsg(filename) 
where filename is the file that contains one message from 
the comp-users-forum archive

20210922
'''
#import math
import sys,os
import glob
import email, base64
import numpy

class extractMsg():
    def __init__(self):
        self.debug = 0
        self.badKeys = {}
        return
    def bigTest(self):
        '''
        run some text extraction modules on a messages from a bunch of files

        mostly diagnostic
        '''
        files = glob.glob('DATA/comp-users-forum_2021*/*')
        L,E = 0,0
        for i,fn in enumerate(files):
            lines = self.getText(fn)
            emsg  = self.decodeText(fn)
            if len(lines)==0:
                L += 1
                #print fn,'zero-length text'
            if len(emsg)==0:
                E += 1
                #print fn,'zero-length message'
            if i%100==0: print 'extractMsg.bigTest processing file#',i,'text/message length',len(lines),'/',len(emsg),'fn',fn,'self.badKeys',self.badKeys
        print 'extractMsg.bigTest failed to extract text/message in',L,'/',E,'files out of a total of',len(files)
        return
    def finalTest(self):
        '''
        check that zero length message can be extracted from every file
        compile/report stats on lengths extracted for all files
        '''
        files = glob.glob('DATA/comp-users-forum_20*/*')
        print 'extractMsg.finalTest will process',len(files),'files'
        L = 0
        lengths = []
        Ldict = {}
        Msgs  = {}
        for i,fn in enumerate(files):
            lines = self.getEmailMsg(fn)
            lengths.append( len(lines) )
            Ldict[fn] = len(lines)
            Msgs[fn]  = lines
            if len(lines)==0:
                L += 1
                print fn,'zero-length text'

            if i%100==0: print 'extractMsg.finalTest processing file#',i,'text length',len(lines),'fn',fn
        print 'extractMsg.finalTest failed to extract email message in',L,'files out of a total of',len(files)
        A = numpy.array(lengths)
        mean,median,std,mx = numpy.mean(A), numpy.median(A), numpy.std(A), numpy.max(A)
        print 'extractMsg.finalTest message length stats: mean {:.2f} median {:.2f} stddev {:.2f} max {:.2f}'.format(mean,median,std,mx)
        nSig = 5.
        fiveSigma = mean + nSig*std
        print 'extractMsg.finalTest Look at messages with length',nSig,'sigma above mean, or >',fiveSigma
        for key in sorted(Ldict, key=Ldict.get):
            #print key,Ldict[key]

            if Ldict[key] > fiveSigma:
                print 'extractMsg.finalTest fn',key,'length',Ldict[key],'msg\n',Msgs[key]
            
        return        
    def getText(self,fn):
        '''
        return string with best guess at email message text
        use msgFix to pick the best part of the original message
        '''

        dthres = 1
        f = open(fn,'r')
        if self.debug > 0 : print 'extractMsg.getText fn',fn
        msg = email.message_from_file(f)
        f.close()

        msg = self.msgFix(msg)
        
        keys = msg.keys()
        if self.debug > dthres : print 'extractMsg.getText initially len(msg)',len(msg),'len(keys)',len(keys)
        if self.debug > dthres : print 'extractMsg.getText keys',keys
        if self.debug > dthres : print 'extractMsg.getText original msg\n',msg


        s1 = ''
        for key in keys:
            s1 = msg.as_string()
            if self.debug > dthres : print 'extractMsg.getText pre-delitem key',key,'type(msg)',type(msg),'len(msg)',len(msg),'len(s1)',len(s1)
            msg.__delitem__(key)
            try:
                s2 = msg.as_string()
            except:
                if key in self.badKeys:
                    self.badKeys[key] += 1
                else:
                    self.badKeys[key] = 1
                if self.debug > dthres : print 'extractMsg.getText Exception after removing',key,'now break'
                break
        s = s1

        if self.debug > dthres : print 'extractMsg.getText before exit len(s),s',len(s),s
        return s
    def listParts(self,fn):
        '''
        list info on parts of msg in fn

        diagnostic use only
        '''
        f = open(fn,'r')
        if self.debug > 0 : print 'extractMsg.listParts fn',fn
        msg = email.message_from_file(f)
        f.close()
        i = 0
        if msg.is_multipart():
            for part in msg.walk():
                print 'part',i,'items',part.items()
                i += 1
        else:
            print 'not multipart'
        return
    def decodeText(self,fn):
        '''
        return decoded email message text
        may return a zero-length string if text cannot be decoded

        open input file, get the best part of the message using msgFix
        and decode it if it is base64-encoded
        '''
        dthres = 1 # overall debug threshold in this module
        
        f = open(fn,'r')
        if self.debug > 0 : print 'extractMsg.decodeText fn',fn
        msg = email.message_from_file(f)
        f.close()

        msg = self.msgFix(msg)
                    
        if self.debug > dthres : print 'extractMsg.decodeText fixed msg',msg
        if self.debug > dthres : print 'extractMsg.decodeText msg.items()',msg.items()

        plaintext, charset = False, None
        for item in msg.items():
            if 'Content-Type' in item[0]:
                if 'text/plain' in item[1] : plaintext = True
            if 'Content-Transfer-Encoding' in item[0] : charset = item[1]

        if self.debug > dthres : print 'extractMsg.decodeText plaintext,charset',plaintext,charset
        s = ''
        if plaintext and charset=='base64':
            s = msg.as_string()
            if self.debug > dthres : print 'extractMsg.decodeText initial s\n',s
            while charset in s:
                k = s.index(charset) + len(charset)
                if self.debug > dthres : print 'extractMsg.decodeText charset k',k
                s = s[k:]
            extraClean = True  # try to remove header and extraneous text before base64 decoding
            if extraClean:
                cr = '\n'
                while cr in s:
                    k = s.index(cr) + len(cr)
                    l1 = len(s[:k])
                    l2 = len(s[:k].strip())
                    l3 = len(s[:k].replace(' ',''))
                    if min(l1,l2,l3)>0 and l1==l3 and l2+1==l1:
                        break
                    else:
                        s = s[k:]
                    
            if self.debug > dthres : print 'extractMsg.decodeText final s\n',s
            
            try:
                s = base64.b64decode(s)
            except:
                s = ''

            if s=='' and self.debug > dthres : print 'extractMsg.decodeText base64 decode Exception'
                
        if self.debug > dthres : print 'extractMsg.decodeText after base64 decoding, s\n',s
        return s
    def msgFix(self,msg):
        '''
        return most likely part of msg to be interpreted as the actual email message
        '''
        fav = {'Content-Type' : 'text/plain'}
        if msg.is_multipart():
            for part in msg.walk():
                for item in part.items():
                    for key in fav:
                        if key==item[0]:
                            if fav[key] in item[1]: return part
                                
        return msg
    def msgReducer(self,msg,QUOLEV=1):
        '''
        return msg after removing quote level > quolev
        assume input msg is string
        '''
        quolev = max(1,QUOLEV)
        quote = '>'
        lines = msg.split('\n')
        for i,line in enumerate(lines):
            if line[:quolev].count(quote)==quolev:
                break
        s = ''
        for line in lines[:i]:
            s += line+'\n'
        return s
    def getEmailMsg(self,fn):
        '''
        return email message in input file, hopefully in normal text
        '''
        msg = self.decodeText(fn)
        if len(msg)==0:
            msg = self.getText(fn)
        msg = self.msgReducer(msg)
        return msg
        
if __name__ == '__main__' :
    eM = extractMsg()
    fn = 'DATA/comp-users-forum_2020-02/22'

    listParts = False
    if listParts:
        fn = 'DATA/comp-users-forum_2021-01/107'
        if len(sys.argv)>1 : fn = sys.argv[1]
        eM.listParts(fn)
        sys.exit('extractMsg listParts ' + fn)

    getEmailMsg =  False
    if getEmailMsg:
        fn = 'DATA/comp-users-forum_2021-01/107'
        fn = 'DATA/comp-users-forum_2021-06/27'
        fn = 'DATA/comp-users-forum_2021-05/41'
        fn = 'DATA/comp-users-forum_2018-03/22'
        msg = eM.getEmailMsg(fn)
        print 'message from',fn,'\n',msg
        sys.exit('extractMsg '+fn)

    finalTest = not False
    if finalTest:
        eM.finalTest()
        sys.exit('extractMsg.finalTest completed')
    

    bigTest =  False
    if bigTest : 
        eM.bigTest()
        sys.exit('extractMsg.bigTest completed')
    
    fn = 'DATA/comp-users-forum_2020-02/5'
    if len(sys.argv)>1 : fn = sys.argv[1]
    s = eM.decodeText(fn)
    print 'len(s)',len(s)
    print 's\n',s
    sys.exit('extractMsg.decodeText '+fn)
    
    #fn = 'DATA/comp-users-forum_2017-06/61'
    lines = eM.getText(fn)
    print lines
    
