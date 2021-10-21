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
    def __init__(self,prefix='DATA/comp-users-forum'):
        self.debug = 0
        self.badKeys = {}
        self.dirPrefix = prefix

        ## salutation phrases used in getText
        S1 = ['Dear','Hello','Hi','HI','Hello again','Good morning']
        S2 = [
            'experts','Experts','Belle 2 computing experts', 
            'gbasf2','colleagues', 
            'comp-users-forum','Comp users forum','team',
            'All','all','everyone','everybody',
            'computing experts','computer experts',
            'grid-experts','GRID experts','grid experts','Grid experts']
        Salutations = []
        for s1 in S1:
            for s2 in S2:
                s = s1 + ' ' + s2
                Salutations.append( s )
        FirstColumn = S1
        self.Salutations = Salutations
        self.FirstColumn = FirstColumn

        
        print 'extractMsg.__init__ completed'
        return
    def bigTest(self):
        '''
        run some text extraction modules on a messages from a bunch of files

        mostly diagnostic
        '''
        files = glob.glob(self.dirPrefix + '_2021*/*')
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
    def getText(self,INPUT,input='file'):
        '''
        return string with best guess at email message text
        use msgFix to pick the best part of the original message

        if input=='file', then INPUT is the filename
        if input=='archive', then INPUT is the archive identifier eg., 2021-03/32

        DEPRECATED ?? if omitPreSalutation==True, then find salutation and remove the text prior to salutation, if salutation is found
        '''
        fn = None
        if input=='file': fn = INPUT
        if input=='archive': fn = self.dirPrefix + '_' + INPUT
        if fn is None : sys.exit('extractMsg.getText ERROR Invalid input='+input)
            
        dthres = 1
        f = open(fn,'r')
        if self.debug > 0 : print 'extractMsg.getText fn',fn
        originalMsg = msg = email.message_from_file(f)
        f.close()

        msg = self.msgFix(msg)

        s = self.get_text(msg)
        
        if self.debug > dthres : print 'extractMsg.getText before exit len(s),s',len(s),s
        return s
    def OLDgetText(self,INPUT,input='file',omitPreSalutation=True):
        '''
        return string with best guess at email message text
        use msgFix to pick the best part of the original message

        if input=='file', then INPUT is the filename
        if input=='archive', then INPUT is the archive identifier eg., 2021-03/32

        if omitPreSalutation==True, then find salutation and remove the text prior to salutation, if salutation is found
        '''
        fn = None
        if input=='file': fn = INPUT
        if input=='archive' : fn = self.dirPrefix + '_' + INPUT
        if fn is None : sys.exit('extractMsg.OLDgetText ERROR Invalid input='+input)
            
        dthres = 1
        f = open(fn,'r')
        if self.debug > 0 : print 'extractMsg.OLDgetText fn',fn
        originalMsg = msg = email.message_from_file(f)
        f.close()

        msg = self.msgFix(msg)
        
        keys = msg.keys()
        if self.debug > dthres : print 'extractMsg.OLDgetText initially len(msg)',len(msg),'len(keys)',len(keys)
        if self.debug > dthres : print 'extractMsg.OLDgetText keys',keys
        if self.debug > dthres : print 'extractMsg.OLDgetText original msg\n',msg


        ### Remove all key,value pairs except the last one to leave
        ### the most likely part of email to be the message.
        ### This procedure was determined empirically.
        s1 = ''
        for key in keys:
            s1 = msg.as_string()
            if self.debug > dthres : print 'extractMsg.OLDgetText pre-delitem key',key,'type(msg)',type(msg),'len(msg)',len(msg),'len(s1)',len(s1)
            msg.__delitem__(key)
            try:
                s2 = msg.as_string()
            except:
                if key in self.badKeys:
                    self.badKeys[key] += 1
                else:
                    self.badKeys[key] = 1
                if self.debug > dthres : print 'extractMsg.OLDgetText Exception after removing',key,'now break'
                break
        s = s1

        ### Try to find the salutation and remove all text prior to the salutation
        if omitPreSalutation :
            idx = -1
            for salut in self.Salutations:
                if salut in s :
                    idx = s.index(salut)
                    break
            if idx < 0 :
                for salut in self.FirstColumn:
                    offset = 0
                    for line in s.split('\n'):
                        offset += len(line) + len('\n')
                        if salut in line:
                            if line.index(salut)==0 :
                                idx = offset + line.index(salut)
                                break
            if idx > 0 :
                s = s[idx:]
            else:
                print 'extractMsg.OLDgetText COULD NOT FIND SALUTATION'
                print 'extractMsg.OLDgetText here is the originalMsg\n',originalMsg

        if self.debug > dthres : print 'extractMsg.OLDgetText before exit len(s),s',len(s),s
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
    def get_text(self,msg):
        '''
        this code taken verbatim from the most popular answer at
        https://stackoverflow.com/questions/4824376/parse-multi-part-email-with-sub-parts-using-python
        on 20211021

        I added idiot_html2text to do rudimentary html to text translation
        Added check on charset
        '''
        text = ""
        if msg.is_multipart():
            html = None
            for part in msg.get_payload():
                if part.get_content_charset() is None:
                    charset = chardet.detect(str(part))['encoding']
                else:
                    charset = part.get_content_charset()
                if part.get_content_type() == 'text/plain':
                    text = unicode(part.get_payload(decode=True),str(charset),"ignore").encode('utf8','replace')
                if part.get_content_type() == 'text/html':
                    html = unicode(part.get_payload(decode=True),str(charset),"ignore").encode('utf8','replace')
            if html is None:
                return text.strip()
            else:
                html = self.idiot_html2text(html) ## added
                return html.strip()
        else:
            cs = msg.get_content_charset()   ## added
            if cs is None : cs = 'us-ascii'  ## added
            text = unicode(msg.get_payload(decode=True),cs,'ignore').encode('utf8','replace') ## altered
            return text.strip()
    def idiot_html2text(self,html):
        '''
        return text given html using knucklehead's method
        '''
        boring = ['&nbsp;','<i>','<\i>']
        text = ''
        for line in html.split('\n'):
            if '<div>' in line and '</div>' in line:
                l = line[line.index('<div>')+len('<div>'):line.index('</div>')-1]
                for s in boring:
                    l = l.replace(s,'').strip()
                text += l + '\n'
        return text
            
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

    finalTest = False
    if finalTest:
        eM.finalTest()
        sys.exit('extractMsg.finalTest completed')
    

    bigTest =  False
    if bigTest : 
        eM.bigTest()
        sys.exit('extractMsg.bigTest completed')

    decodeTest = False
    if decodeTest:
        fn = 'DATA/comp-users-forum_2020-02/5'
        if len(sys.argv)>1 : fn = sys.argv[1]
        s = eM.decodeText(fn)
        print 'len(s)',len(s)
        print 's\n',s
        sys.exit('extractMsg.decodeText '+fn)

    getArchiveText = False
    if getArchiveText:
        #fn = 'DATA/comp-users-forum_2017-06/61'
        input = 'archive'
        archive = '2020-11/25'
        archive = '2021-05/32'
        if len(sys.argv)>1 : archive = sys.argv[1]
        lines = eM.getText(archive,input=input)
        print lines

    betterGetText = True
    if betterGetText :
        for n in range(38,39):
#            fn = 'DATA/comp-users-forum_2021-03/'+str(n)
            fn = 'DATA/comp-users-forum_2021-02/'+str(n)
            f = open(fn,'r')
            print '\n\nextractMsg -------------------------------- test get_text for fn',fn
            msg = email.message_from_file(f)
            f.close()
            msg = eM.msgFix(msg)
            lines = eM.get_text(msg)
            print lines
